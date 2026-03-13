from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import JobStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Queue Schemas
class QueueBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None

class QueueCreate(QueueBase):
    pass

class QueueResponse(QueueBase):
    id: int
    owner_id: Optional[int] = None
    class Config:
        from_attributes = True


class QueueStatsResponse(QueueResponse):
    total_jobs: int
    queued_jobs: int
    running_jobs: int
    succeeded_jobs: int
    failed_jobs: int
    last_activity_at: Optional[datetime] = None

# Job Schemas
class JobBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    queue_name: str
    type: str
    priority: int = 0
    payload: Optional[str] = None
    max_retries: int = 3

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    owner_id: int
    status: JobStatus
    attempts: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[str] = None
    worker_id: Optional[str] = None

    class Config:
        from_attributes = True

# Job Log Schemas
class JobLogResponse(BaseModel):
    id: int
    job_id: int
    message: str
    timestamp: datetime
    level: str

    class Config:
        from_attributes = True

# Aggregated responses
class JobDetailResponse(JobResponse):
    logs: List[JobLogResponse] = []

class AnalyticsOverview(BaseModel):
    total_queues: int
    total_jobs: int
    queued_jobs: int
    running_jobs: int
    succeeded_jobs: int
    failed_jobs: int
    retrying_jobs: int
    success_rate: float
    avg_processing_time_ms: float
