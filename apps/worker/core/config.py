from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WORKER_ID: str = "worker-default"
    QUEUES_TO_WATCH: str = "default,emails,reports,ml_pipeline"
    POLL_INTERVAL_SEC: float = 1.0
    
    # Configure via .env
    DATABASE_URL: str
    REDIS_URL: str
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    class Config:
        env_file = "../../.env"
        extra = "ignore"

settings = Settings()
