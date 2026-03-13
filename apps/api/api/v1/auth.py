from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.config import settings
from core.auth import verify_password, get_password_hash, create_access_token
from core.rate_limit import RateLimitConfig, rate_limiter
from models import User
from schemas import UserCreate, UserResponse, Token
from api.deps import get_current_user

router = APIRouter()


REGISTER_RATE_LIMIT = RateLimitConfig(max_attempts=5, window_seconds=60)
LOGIN_RATE_LIMIT = RateLimitConfig(max_attempts=10, window_seconds=60)


def _client_key(request: Request, identifier: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    return f"{ip}:{identifier.lower()}"


def _enforce_rate_limit(key: str, config: RateLimitConfig, message: str) -> None:
    if not rate_limiter.allow(key=key, config=config):
        raise HTTPException(status_code=429, detail=message)

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = user_in.email.lower()
    _enforce_rate_limit(
        key=_client_key(request, f"register:{email}"),
        config=REGISTER_RATE_LIMIT,
        message="Too many registration attempts. Please try again later.",
    )

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    email = form_data.username.lower()
    _enforce_rate_limit(
        key=_client_key(request, f"login:{email}"),
        config=LOGIN_RATE_LIMIT,
        message="Too many login attempts. Please try again later.",
    )

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
