from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.role import RoleCreate, AssignRoleRequest, RoleResponse
from app.schemas.user import UserResponse, MessageResponse
from app.services.role_service import create_role, assign_role_to_user
from app.core.dependencies import require_role

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role (admin only)",
    dependencies=[Depends(require_role("admin"))],
)
async def add_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new role (e.g., `moderator`, `editor`).
    Restricted to admins.
    """
    role = await create_role(db, data)
    return RoleResponse(id=role.id, name=role.name)


@router.post(
    "/assign",
    response_model=UserResponse,
    summary="Assign a role to a user (admin only)",
    dependencies=[Depends(require_role("admin"))],
)
async def assign_role(data: AssignRoleRequest, db: AsyncSession = Depends(get_db)):
    """
    Assigns an existing role to a user by user_id.
    Idempotent — assigning an already-held role is a no-op.
    """
    user = await assign_role_to_user(db, data.user_id, data.role_name)
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=user.role_names,
        permissions=user.permission_names,
    )
