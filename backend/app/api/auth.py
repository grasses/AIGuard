
"""Authentication API routes: login, register, activate, refresh, password reset."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, UserRole, UserStatus
from app.schemas import (
    LoginRequest, RegisterRequest, TokenResponse,
    RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest,
    ApiResponse, UserOut,
)
from app.utils import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.config import settings
from datetime import datetime, timedelta, timezone
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """User login. Returns JWT tokens."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if user.status == UserStatus.inactive:
        raise HTTPException(status_code=401, detail="账号未激活")
    if user.status == UserStatus.locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="账号已临时锁定，请稍后再试")
        user.status = UserStatus.active
        user.login_failed_count = 0

    # Reset failed counter on success
    user.login_failed_count = 0
    user.locked_until = None
    await db.flush()

    token_data = {"sub": user.id, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "code": 0,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "balance": user.balance,
                "status": user.status.value,
            },
        },
    }


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """User registration."""
    # Check existing
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.username == req.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已被注册")

    activation_token = uuid.uuid4().hex

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=UserRole.user,
        status=UserStatus.inactive,
        activation_token=activation_token,
    )
    db.add(user)
    await db.flush()

    # In production, send activation email here
    return {"code": 0, "message": "注册成功，请查收激活邮件"}


@router.get("/activate")
async def activate(token: str, db: AsyncSession = Depends(get_db)):
    """Activate user account via email token."""
    result = await db.execute(select(User).where(User.activation_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="无效的激活链接")

    user.status = UserStatus.active
    user.activation_token = None
    await db.flush()

    return {"code": 0, "message": "账号激活成功"}


@router.post("/refresh")
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != UserStatus.active:
        raise HTTPException(status_code=401, detail="用户不存在或未激活")

    token_data = {"sub": user.id, "role": user.role.value}
    access_token = create_access_token(token_data)

    return {
        "code": 0,
        "data": {
            "access_token": access_token,
            "expires_in": settings.access_token_expire_minutes * 60,
        },
    }


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset email."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if user:
        user.reset_token = uuid.uuid4().hex
        await db.flush()
        # In production, send email here

    return {"code": 0, "message": "重置邮件已发送"}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email."""
    result = await db.execute(select(User).where(User.reset_token == req.token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="无效的重置链接")

    user.hashed_password = hash_password(req.new_password)
    user.reset_token = None
    await db.flush()

    return {"code": 0, "message": "密码重置成功"}
