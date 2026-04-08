from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from jose import JWTError

from app.database import get_db
from app.schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse, MessageResponse
from app.services.user_service import create_user, authenticate_user
from app.core.security import create_access_token, decode_access_token
from app.core.redis_client import cache_token, blacklist_token, delete_user_token
from app.core.dependencies import get_current_user, bearer_scheme
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    **Signup Flow:**
    1. Validate email + password (Pydantic)
    2. Hash password (bcrypt)
    3. Store user in PostgreSQL
    4. Assign default role: `user`
    """
    user = await create_user(db, data)
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=user.role_names,
        permissions=user.permission_names,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT",
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    **Login Flow:**
    1. Verify email exists
    2. Compare bcrypt hash
    3. Generate JWT (user_id + role + exp)
    4. Cache token in Redis (TTL = 30 min)
    5. Return token
    """
    user = await authenticate_user(db, data.email, data.password)

    # Build JWT payload
    expire_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    primary_role = user.role_names[0] if user.role_names else "user"
    token = create_access_token(
        data={"user_id": user.id, "role": primary_role},
        expires_delta=expire_delta,
    )

    # Cache in Redis
    ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await cache_token(user.id, token, ttl_seconds=ttl)

    return TokenResponse(
        access_token=token,
        expires_in=ttl,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and blacklist token",
)
async def logout(
    credentials=Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    """
    **Logout Flow:**
    1. Decode token → get remaining TTL
    2. Blacklist token in Redis
    3. Delete cached token for user
    """
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        from datetime import datetime, timezone
        exp = payload.get("exp")
        now = datetime.now(timezone.utc).timestamp()
        remaining_ttl = max(int(exp - now), 1)
    except JWTError:
        remaining_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    await blacklist_token(token, ttl_seconds=remaining_ttl)
    await delete_user_token(current_user.id)

    return MessageResponse(message="Logged out successfully")
