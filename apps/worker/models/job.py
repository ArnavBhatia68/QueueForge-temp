# Just replicating the necessary models for the worker to avoid complex monorepo local package setups
import enum
import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Untitled job")
    queue_name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    priority = Column(Integer, default=0, index=True)
    payload = Column(Text, nullable=True) # JSON string
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, index=True)
    attempts = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True) # JSON string
    worker_id = Column(String, nullable=True)

class JobLog(Base):
    __tablename__ = "job_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String, default="INFO")
