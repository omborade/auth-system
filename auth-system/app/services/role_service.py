from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate
from app.services.user_service import get_user_by_id
from fastapi import HTTPException, status


async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{data.name}' already exists",
        )
    role = Role(name=data.name)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def assign_role_to_user(db: AsyncSession, user_id: int, role_name: str) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

    if role not in user.roles:
        user.roles.append(role)
        await db.commit()
        await db.refresh(user)

    return user


async def get_or_create_role(db: AsyncSession, name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalars().first()
    if not role:
        role = Role(name=name)
        db.add(role)
        await db.flush()
    return role
