import asyncio
import json
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis # type: ignore

from core.database import SessionLocal, engine
from core.config import settings
from core.auth import get_password_hash
from models import User, Queue, Job, JobLog, JobStatus
from models.base import Base

async def clean_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def seed():
    await clean_db()
    
    redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.flushall()

    async with SessionLocal() as db:
        # Create user
        user = User(
            email="demo@queueforge.io",
            hashed_password=get_password_hash("password")
        )
        db.add(user)

        # Create queues
        queues = [
            Queue(name="default", description="General purpose queue"),
            Queue(name="emails", description="Outbound email queue"),
            Queue(name="reports", description="Heavy report generation"),
            Queue(name="ml_pipeline", description="ML model inference")
        ]
        db.add_all(queues)
        await db.commit()

        # Generate Fake Jobs
        job_types = ["send_email", "send_webhook", "generate_csv_report", "process_csv", "simulate_ml_task"]
        now = datetime.utcnow()

        for i in range(50):
            queue_obj = random.choice(queues)
            status = random.choices(
                [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLED],
                weights=[60, 15, 10, 10, 5]
            )[0]
            
            created_at = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
            started_at = created_at + timedelta(seconds=random.randint(1, 10)) if status != JobStatus.QUEUED else None
            completed_at = started_at + timedelta(seconds=random.randint(2, 120)) if status in (JobStatus.SUCCEEDED, JobStatus.FAILED) else None
            
            priority = random.choice([0, 10, 20])
            attempts = 1 if status in (JobStatus.SUCCEEDED, JobStatus.RUNNING) else random.randint(1, 3)
            
            error_message = f"Simulated error parsing payload" if status == JobStatus.FAILED else None
            result = json.dumps({"output": f"Success data {i}"}) if status == JobStatus.SUCCEEDED else None

            job = Job(
                owner_id=user.id,
                queue_name=queue_obj.name,
                type=random.choice(job_types),
                priority=priority,
                payload=json.dumps({"task_id": i, "user_id": random.randint(100, 999), "email": "user@example.com", "url": "https://httpbin.org/post", "rows": [{"id": i, "score": random.randint(1,100)}], "csv_content": "name,score\nalice,10\nbob,20", "text": "sample transaction"}),
                status=status,
                attempts=attempts,
                created_at=created_at,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
                result=result,
                worker_id=f"worker-{random.randint(1,3)}" if status != JobStatus.QUEUED else None
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            # Add logs
            db.add(JobLog(job_id=job.id, message="Job created", timestamp=job.created_at))
            if job.started_at:
                db.add(JobLog(job_id=job.id, message=f"Job started on {job.worker_id}", timestamp=job.started_at))
            if job.completed_at:
                if status == JobStatus.SUCCEEDED:
                    db.add(JobLog(job_id=job.id, message="Job completed successfully", timestamp=job.completed_at))
                elif status == JobStatus.FAILED:
                    db.add(JobLog(job_id=job.id, message=error_message, level="ERROR", timestamp=job.completed_at))
            await db.commit()

            # Enqueue to Redis if queued
            if status == JobStatus.QUEUED:
                await redis.rpush(f"queue:{job.queue_name}", json.dumps({"job_id": job.id}))

    print("Seed data generated successfully.")
    await redis.aclose() # type: ignore

if __name__ == "__main__":
    asyncio.run(seed())
