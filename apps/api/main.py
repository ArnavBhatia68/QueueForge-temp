from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import redis.asyncio as aioredis  # type: ignore

from core.config import settings
from core.database import SessionLocal
from api.v1 import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],  # Reads from ENV or defaults to localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/deep")
async def deep_health_check():
    db_ok = False
    redis_ok = False

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis = None
    try:
        redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_ok = bool(await redis.ping())
    except Exception:
        redis_ok = False
    finally:
        if redis is not None:
            await redis.aclose()  # type: ignore

    overall_ok = db_ok and redis_ok
    return {
        "status": "ok" if overall_ok else "degraded",
        "dependencies": {
            "postgres": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "down",
        },
    }
