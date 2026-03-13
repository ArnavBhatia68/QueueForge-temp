from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import json
import redis.asyncio as aioredis  # type: ignore

from core.database import get_db
from core.config import settings
from models import Job, Queue, JobStatus, JobLog, User
from schemas import JobCreate, JobResponse, JobDetailResponse
from api.deps import get_current_user

router = APIRouter()


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
    stmt = select(Queue).where(Queue.name == job_in.queue_name)
    result = await db.execute(stmt)
    if not result.scalars().first():
        queue = Queue(name=job_in.queue_name, description="Auto-created queue")
        db.add(queue)
        await db.commit()

    job = Job(
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

    db.add(JobLog(job_id=job.id, message="Job created and queued", level="INFO"))
    await db.commit()

    job_data_str = json.dumps({"job_id": job.id})
    await redis.rpush(f"queue:{job.queue_name}", job_data_str)

    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: JobStatus = None,  # type: ignore
    queue_name: str = None,  # type: ignore
    current_user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.owner_id == current_user.id).order_by(Job.created_at.desc())
    if status:
        stmt = stmt.where(Job.status == status)
    if queue_name:
        stmt = stmt.where(Job.queue_name == queue_name)

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
    job.attempts = 0
    job.error_message = None

    db.add(JobLog(job_id=job.id, message="Job retry initiated", level="INFO"))
    await db.commit()
    await db.refresh(job)

    job_data_str = json.dumps({"job_id": job.id})
    await redis.rpush(f"queue:{job.queue_name}", job_data_str)

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

    if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
        raise HTTPException(status_code=400, detail="Cannot cancel a completed job")

    job.status = JobStatus.CANCELLED

    db.add(JobLog(job_id=job.id, message="Job cancelled by user", level="WARNING"))
    await db.commit()
    await db.refresh(job)

    return job
