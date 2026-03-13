from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from core.database import get_db
from models import Queue, User, Job, JobStatus
from schemas import QueueCreate, QueueResponse, QueueStatsResponse, JobResponse
from api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=QueueResponse)
async def create_queue(
    queue_in: QueueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Queue).where(Queue.name == queue_in.name)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Queue with this name already exists")

    queue = Queue(name=queue_in.name, description=queue_in.description, owner_id=current_user.id)
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return queue


@router.get("/", response_model=List[QueueStatsResponse])
async def list_queues(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Queue).where(Queue.owner_id == current_user.id)
    result = await db.execute(stmt)
    queues = result.scalars().all()

    queue_stats: list[QueueStatsResponse] = []
    for queue in queues:
        counts_stmt = select(Job.status, func.count(Job.id)).where(
            Job.owner_id == current_user.id,
            Job.queue_name == queue.name,
        ).group_by(Job.status)
        counts_result = await db.execute(counts_stmt)
        counts_map = {status: count for status, count in counts_result.all()}

        total_jobs_stmt = select(func.count(Job.id)).where(
            Job.owner_id == current_user.id,
            Job.queue_name == queue.name,
        )
        total_jobs = (await db.execute(total_jobs_stmt)).scalar() or 0

        last_activity_stmt = select(func.max(Job.completed_at)).where(
            Job.owner_id == current_user.id,
            Job.queue_name == queue.name,
        )
        last_activity = (await db.execute(last_activity_stmt)).scalar()

        queue_stats.append(
            QueueStatsResponse(
                id=queue.id,
                name=queue.name,
                description=queue.description,
                owner_id=queue.owner_id,
                total_jobs=total_jobs,
                queued_jobs=counts_map.get(JobStatus.QUEUED, 0),
                running_jobs=counts_map.get(JobStatus.RUNNING, 0),
                succeeded_jobs=counts_map.get(JobStatus.SUCCEEDED, 0),
                failed_jobs=counts_map.get(JobStatus.FAILED, 0),
                last_activity_at=last_activity,
            )
        )

    return queue_stats


@router.get("/{queue_name}", response_model=QueueStatsResponse)
async def get_queue(
    queue_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Queue).where(Queue.name == queue_name, Queue.owner_id == current_user.id)
    result = await db.execute(stmt)
    queue = result.scalars().first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    counts_stmt = select(Job.status, func.count(Job.id)).where(
        Job.owner_id == current_user.id,
        Job.queue_name == queue.name,
    ).group_by(Job.status)
    counts_result = await db.execute(counts_stmt)
    counts_map = {status: count for status, count in counts_result.all()}

    total_jobs_stmt = select(func.count(Job.id)).where(
        Job.owner_id == current_user.id,
        Job.queue_name == queue.name,
    )
    total_jobs = (await db.execute(total_jobs_stmt)).scalar() or 0

    last_activity_stmt = select(func.max(Job.completed_at)).where(
        Job.owner_id == current_user.id,
        Job.queue_name == queue.name,
    )
    last_activity = (await db.execute(last_activity_stmt)).scalar()

    return QueueStatsResponse(
        id=queue.id,
        name=queue.name,
        description=queue.description,
        owner_id=queue.owner_id,
        total_jobs=total_jobs,
        queued_jobs=counts_map.get(JobStatus.QUEUED, 0),
        running_jobs=counts_map.get(JobStatus.RUNNING, 0),
        succeeded_jobs=counts_map.get(JobStatus.SUCCEEDED, 0),
        failed_jobs=counts_map.get(JobStatus.FAILED, 0),
        last_activity_at=last_activity,
    )


@router.get("/{queue_name}/jobs", response_model=List[JobResponse])
async def get_queue_jobs(
    queue_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    queue_stmt = select(Queue).where(Queue.name == queue_name, Queue.owner_id == current_user.id)
    if not (await db.execute(queue_stmt)).scalars().first():
        raise HTTPException(status_code=404, detail="Queue not found")

    jobs_stmt = select(Job).where(
        Job.owner_id == current_user.id,
        Job.queue_name == queue_name,
    ).order_by(Job.created_at.desc()).limit(25)
    jobs_result = await db.execute(jobs_stmt)
    return jobs_result.scalars().all()
