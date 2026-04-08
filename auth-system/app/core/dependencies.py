from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database import get_db
from app.core.security import decode_access_token
from app.core.redis_client import is_token_blacklisted
from app.models.user import User
from app.services.user_service import get_user_by_id

# ─── Bearer token extractor ───────────────────────────────────────────────────
bearer_scheme = HTTPBearer()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Decode JWT → fetch User from DB.
    Steps:
      1. Extract Bearer token
      2. Check blacklist (Redis)
      3. Decode JWT → user_id
      4. Load user from DB
      5. Verify user is active
    """
    token = credentials.credentials

    # 1. Check blacklist
    if await is_token_blacklisted(token):
        raise CREDENTIALS_EXCEPTION

    # 2. Decode
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
    except JWTError:
        raise CREDENTIALS_EXCEPTION

    # 3. Fetch user
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 4. Active check
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user


def require_role(*allowed_roles: str):
    """
    Factory dependency: enforce role-based access control.
    Usage: Depends(require_role("admin"))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not any(role in current_user.role_names for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires role: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


def require_permission(*perms: str):
    """
    Factory dependency: enforce permission-based access control.
    Usage: Depends(require_permission("write"))
    """
    async def perm_checker(current_user: User = Depends(get_current_user)) -> User:
        user_perms = set(current_user.permission_names)
        if not all(p in user_perms for p in perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(perms)}",
            )
        return current_user
    return perm_checker
