from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import json
import redis.asyncio as aioredis  # type: ignore

from core.database import get_db
from core.config import settings
from models import Job, Queue, JobStatus, JobLog, User
from schemas import JobCreate, JobResponse, JobDetailResponse
from api.deps import get_current_user

router = APIRouter()

ALLOWED_JOB_TYPES = {"webhook_request", "csv_processing", "text_transform"}


async def get_redis():
    redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()  # type: ignore


@router.post("/", response_model=JobResponse)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    queue_stmt = select(Queue).where(Queue.name == job_in.queue_name, Queue.owner_id == current_user.id)
    queue_result = await db.execute(queue_stmt)
    if not queue_result.scalars().first():
        raise HTTPException(status_code=404, detail="Queue not found")

    if job_in.type not in ALLOWED_JOB_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported job type: {job_in.type}")

    if job_in.max_retries < 0 or job_in.max_retries > 10:
        raise HTTPException(status_code=400, detail="max_retries must be between 0 and 10")

    payload_obj = json.loads(job_in.payload) if job_in.payload else {}

    if job_in.type == "webhook_request":
        if not payload_obj.get("url"):
            raise HTTPException(status_code=400, detail="Webhook job requires payload.url")
    elif job_in.type == "csv_processing":
        if not payload_obj.get("csv_text"):
            raise HTTPException(status_code=400, detail="CSV job requires payload.csv_text")
        if payload_obj.get("operation") not in {"csv_to_json", "deduplicate_rows", "validate_required_columns", "summary_statistics"}:
            raise HTTPException(status_code=400, detail="CSV job has unsupported operation")
    elif job_in.type == "text_transform":
        if not payload_obj.get("input"):
            raise HTTPException(status_code=400, detail="Text job requires payload.input")

    job = Job(
        name=job_in.name,
        owner_id=current_user.id,
        queue_name=job_in.queue_name,
        type=job_in.type,
        priority=job_in.priority,
        payload=job_in.payload,
        max_retries=job_in.max_retries,
        status=JobStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    db.add(JobLog(job_id=job.id, message="Job queued", level="INFO"))
    await db.commit()

    await redis.rpush(f"queue:{job.queue_name}", json.dumps({"job_id": job.id}))

    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    queue_name: Optional[str] = None,
    job_type: Optional[str] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.owner_id == current_user.id).order_by(Job.created_at.desc())
    if status:
        stmt = stmt.where(Job.status == status)
    if queue_name:
        stmt = stmt.where(Job.queue_name == queue_name)
    if job_type:
        stmt = stmt.where(Job.type == job_type)
    if search:
        like_term = f"%{search}%"
        stmt = stmt.where((Job.name.ilike(like_term)) | (Job.queue_name.ilike(like_term)) | (Job.type.ilike(like_term)))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Job)
        .options(selectinload(Job.logs))
        .where(Job.id == job_id, Job.owner_id == current_user.id)
    )
    result = await db.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.logs = sorted(job.logs, key=lambda x: x.timestamp)
    return job


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.id == job_id, Job.owner_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="Can only retry failed or cancelled jobs")

    job.status = JobStatus.QUEUED
    job.error_message = None
    job.started_at = None
    job.completed_at = None

    db.add(JobLog(job_id=job.id, message="Job retry requested by user", level="INFO"))
    await db.commit()
    await db.refresh(job)

    await redis.rpush(f"queue:{job.queue_name}", json.dumps({"job_id": job.id}))

    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.id == job_id, Job.owner_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.RETRYING):
        raise HTTPException(status_code=400, detail="Can only cancel queued or running jobs")

    job.status = JobStatus.CANCELLED
    db.add(JobLog(job_id=job.id, message="Job cancelled by user", level="WARNING"))
    await db.commit()
    await db.refresh(job)

    return job
