from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

from core.database import get_db
from models import Job, JobStatus, User, Queue
from schemas import AnalyticsOverview
from api.deps import get_current_user

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_jobs = (await db.execute(select(func.count(Job.id)).where(Job.owner_id == current_user.id))).scalar() or 0
    total_queues = (await db.execute(select(func.count(Queue.id)).where(Queue.owner_id == current_user.id))).scalar() or 0

    status_counts_result = await db.execute(
        select(Job.status, func.count(Job.id)).where(Job.owner_id == current_user.id).group_by(Job.status)
    )
    status_counts = {status: count for status, count in status_counts_result.all()}

    queued_jobs = status_counts.get(JobStatus.QUEUED, 0)
    running_jobs = status_counts.get(JobStatus.RUNNING, 0)
    succeeded_jobs = status_counts.get(JobStatus.SUCCEEDED, 0)
    failed_jobs = status_counts.get(JobStatus.FAILED, 0)
    retrying_jobs = status_counts.get(JobStatus.RETRYING, 0)

    completed = succeeded_jobs + failed_jobs
    success_rate = ((succeeded_jobs / completed) * 100.0) if completed else 0.0

    stmt = select(Job.started_at, Job.completed_at).where(
        Job.owner_id == current_user.id,
        Job.status == JobStatus.SUCCEEDED,
        Job.started_at.isnot(None),
        Job.completed_at.isnot(None),
    )
    times_result = await db.execute(stmt)
    times = times_result.all()

    avg_processing_time_ms = 0.0
    if times:
        total_ms = sum((t.completed_at - t.started_at).total_seconds() * 1000 for t in times)
        avg_processing_time_ms = total_ms / len(times)

    return AnalyticsOverview(
        total_queues=total_queues,
        total_jobs=total_jobs,
        queued_jobs=queued_jobs,
        running_jobs=running_jobs,
        succeeded_jobs=succeeded_jobs,
        failed_jobs=failed_jobs,
        retrying_jobs=retrying_jobs,
        success_rate=round(success_rate, 2),
        avg_processing_time_ms=round(avg_processing_time_ms, 2),
    )


class DailyJobCount(BaseModel):
    date: str
    succeeded: int
    failed: int
    queued: int


@router.get("/daily", response_model=List[DailyJobCount])
async def get_daily_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cutoff = datetime.utcnow() - timedelta(days=7)
    stmt = select(Job.created_at, Job.status).where(
        Job.owner_id == current_user.id,
        Job.created_at >= cutoff,
    )
    result = await db.execute(stmt)
    rows = result.all()

    days: dict[str, dict[str, int]] = {}
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        days[day] = {"succeeded": 0, "failed": 0, "queued": 0}

    for row in rows:
        day = row.created_at.strftime("%Y-%m-%d")
        if day not in days:
            continue
        if row.status == JobStatus.SUCCEEDED:
            days[day]["succeeded"] += 1
        elif row.status == JobStatus.FAILED:
            days[day]["failed"] += 1
        else:
            days[day]["queued"] += 1

    return [DailyJobCount(date=day, **counts) for day, counts in sorted(days.items())]


class RecentJobItem(BaseModel):
    id: int
    name: str
    type: str
    queue_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/recent", response_model=List[RecentJobItem])
async def get_recent_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Job)
        .where(Job.owner_id == current_user.id)
        .order_by(Job.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
