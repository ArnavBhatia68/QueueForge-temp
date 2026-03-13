import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy.future import select
import redis.asyncio as aioredis  # type: ignore

from core.config import settings
from db.database import db_manager
from models.job import Job, JobLog, JobStatus
from handlers import HANDLERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("worker")

GLOBAL_JOB_QUEUE = "queue:__all_jobs__"


class Worker:
    def __init__(self):
        self.redis = None
        self.running = False
        self.worker_id = settings.WORKER_ID

    async def start(self):
        logger.info(f"Starting Worker {self.worker_id}")
        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self.running = True

        logger.info(f"Watching queue: {GLOBAL_JOB_QUEUE}")

        while self.running:
            try:
                result = await self.redis.blpop([GLOBAL_JOB_QUEUE], timeout=settings.POLL_INTERVAL_SEC)
                if result:
                    _, item = result
                    await self.process_job_msg(item)
            except asyncio.CancelledError:
                logger.info("Worker cancelled")
                break
            except Exception as exc:
                logger.error(f"Error in poll loop: {exc}")
                await asyncio.sleep(1)

        await self.redis.aclose()  # type: ignore
        logger.info("Worker stopped")

    async def log_job(self, session, job_id, message, level="INFO"):
        session.add(JobLog(job_id=job_id, message=message, level=level))

    async def process_job_msg(self, msg_str: str):
        try:
            msg = json.loads(msg_str)
            job_id = msg.get("job_id")
            if not job_id:
                return
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message: {msg_str}")
            return

        async with db_manager as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalars().first()

            if not job:
                logger.error(f"Job {job_id} not found in DB")
                return
            if job.status == JobStatus.CANCELLED:
                logger.info(f"Job {job_id} is cancelled, ignoring")
                return
            if job.status not in (JobStatus.QUEUED, JobStatus.RETRYING):
                return

            job.status = JobStatus.RUNNING
            job.attempts += 1
            job.started_at = datetime.utcnow()
            job.worker_id = self.worker_id

            await self.log_job(session, job.id, f"Worker {self.worker_id} picked up job '{job.name}' (attempt {job.attempts})")
            await self.log_job(session, job.id, f"Processing job type '{job.type}'")
            await session.commit()

            success = False
            result_data = None
            error_msg = None

            try:
                handler_fn = HANDLERS.get(job.type)
                if not handler_fn:
                    raise ValueError(f"Unknown job type: {job.type}")

                payload = json.loads(job.payload) if job.payload else {}
                await self.log_job(session, job.id, "Validated input payload")
                await session.commit()

                result_data = await handler_fn(payload)

                if job.type == "webhook_request" and result_data.get("ok") is False and payload.get("fail_on_http_error", True):
                    raise RuntimeError(result_data.get("error") or f"Webhook returned non-success status {result_data.get('status_code')}")

                success = True
            except Exception as exc:
                logger.error(f"Job {job_id} failed: {exc}")
                error_msg = str(exc)

            job.completed_at = datetime.utcnow()

            if success:
                job.status = JobStatus.SUCCEEDED
                job.result = json.dumps(result_data)
                job.error_message = None
                await self.log_job(session, job.id, "Job completed successfully")
            else:
                job.error_message = error_msg
                if job.attempts >= job.max_retries:
                    job.status = JobStatus.FAILED
                    await self.log_job(session, job.id, f"Job failed permanently: {error_msg}", level="ERROR")
                else:
                    await self.log_job(session, job.id, f"Job failed, requeuing for retry: {error_msg}", level="WARNING")
                    job.status = JobStatus.QUEUED
                    payload = json.dumps({"job_id": job.id, "queue_name": job.queue_name})
                    await self.redis.rpush(GLOBAL_JOB_QUEUE, payload)

            await session.commit()


if __name__ == "__main__":
    worker = Worker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        worker.running = False
