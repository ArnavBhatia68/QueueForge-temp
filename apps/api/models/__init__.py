import datetime
import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from models.base import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    jobs = relationship("Job", back_populates="owner")


class Queue(Base):
    __tablename__ = "queues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    jobs = relationship("Job", back_populates="queue")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Untitled job")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    queue_name = Column(String, ForeignKey("queues.name"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    priority = Column(Integer, default=0, index=True)
    payload = Column(Text, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, index=True)
    attempts = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    worker_id = Column(String, nullable=True)

    owner = relationship("User", back_populates="jobs")
    queue = relationship("Queue", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")


class JobLog(Base):
    __tablename__ = "job_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String, default="INFO")

    job = relationship("Job", back_populates="logs")
