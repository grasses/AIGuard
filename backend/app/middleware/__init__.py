"""Authentication middleware for JWT and API Key."""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, UserStatus, ApiKey
from app.utils import decode_token
import hashlib

jwt_bearer = HTTPBearer(auto_error=False)
api_key_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(jwt_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract current user from JWT token (for web API)."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    token = credentials.credentials
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="无效或过期的令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌载荷")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if user.status == UserStatus.inactive:
        raise HTTPException(status_code=403, detail="账号未激活")
    if user.status == UserStatus.locked:
        raise HTTPException(status_code=403, detail="账号已锁定")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require admin or super_admin role."""
    if current_user.role.value not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require super_admin role."""
    if current_user.role.value != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


async def get_user_by_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(api_key_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract user from API Key (for /v1 proxy gateway)."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing API Key")

    raw_key = credentials.credentials
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.enabled == True)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="User not active")

    return user
