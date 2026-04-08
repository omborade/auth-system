from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user, require_role
from app.services.user_service import get_all_users
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    **Authorization Flow:**
    1. Extract Bearer token from header
    2. Check Redis blacklist
    3. Decode JWT → user_id
    4. Load user + roles + permissions from DB
    5. Return profile
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        roles=current_user.role_names,
        permissions=current_user.permission_names,
    )


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
    dependencies=[Depends(require_role("admin"))],
)
async def list_users(db: AsyncSession = Depends(get_db)):
    """
    **RBAC Protected:** Only users with role `admin` can access this.
    Returns all registered users with their roles.
    """
    users = await get_all_users(db)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            is_active=u.is_active,
            created_at=u.created_at,
            roles=u.role_names,
            permissions=u.permission_names,
        )
        for u in users
    ]
