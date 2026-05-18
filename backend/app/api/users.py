
"""User management API (admin only)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, UserRole, UserStatus, ApiKey
from app.schemas import (
    UserOut, UserUpdateRequest, ChangePasswordRequest,
    ApiKeyOut, ApiKeyCreateRequest, ApiKeyCreatedResponse,
)
from app.middleware import get_current_user, get_current_admin, get_current_super_admin
from app.utils import hash_password, verify_password, generate_api_key
from datetime import datetime, timezone
import hashlib

router = APIRouter(prefix="/api", tags=["users"])


# ─── User profile ───

@router.get("/user/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return {
        "code": 0,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role.value,
            "balance": current_user.balance,
            "status": current_user.status.value,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }


@router.put("/user/profile")
async def update_profile(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile (limited fields)."""
    if req.username is not None:
        current_user.username = req.username
    if req.email is not None:
        current_user.email = req.email
    await db.flush()
    return {"code": 0, "message": "更新成功"}


@router.post("/user/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.hashed_password = hash_password(req.new_password)
    await db.flush()
    return {"code": 0, "message": "密码修改成功"}


# ─── API Keys ───

@router.get("/user/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys."""
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == current_user.id))
    keys = result.scalars().all()
    return {"code": 0, "data": [ApiKeyOut.model_validate(k).model_dump() for k in keys]}


@router.post("/user/api-keys", status_code=201)
async def create_api_key(
    req: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. The raw key is only returned once."""
    raw_key, key_hash = generate_api_key()
    api_key = ApiKey(
        user_id=current_user.id,
        name=req.name,
        key_hash=key_hash,
        key_prefix=raw_key[:8],
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    return {
        "code": 0,
        "data": {
            "api_key": ApiKeyOut.model_validate(api_key).model_dump(),
            "raw_key": raw_key,
        },
    }


@router.delete("/user/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    await db.delete(key)
    await db.flush()
    return {"code": 0, "message": "删除成功"}


# ─── Admin: User Management ───

@router.get("/admin/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    role: str = Query(None),
    status: str = Query(None),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    query = select(User)
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [UserOut.model_validate(u).model_dump() for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/admin/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get user detail."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"code": 0, "data": UserOut.model_validate(user).model_dump()}


@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user (super admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    await db.flush()
    return {"code": 0, "data": UserOut.model_validate(user).model_dump()}
