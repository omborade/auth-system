from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.role import Role
from app.core.security import hash_password, verify_password
from app.schemas.user import RegisterRequest
from fastapi import HTTPException, status


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.email == email)
    )
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    return result.scalars().first()


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(User).options(selectinload(User.roles))
    )
    return result.scalars().all()


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    # Check duplicate
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash password
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()   # get user.id before commit

    # Assign default "user" role
    role_result = await db.execute(select(Role).where(Role.name == "user"))
    default_role = role_result.scalars().first()
    if default_role:
        user.roles.append(default_role)

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user
