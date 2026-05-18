
"""System settings API (super admin only)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, SystemSetting
from app.schemas import SystemSettingUpdate
from app.middleware import get_current_super_admin

router = APIRouter(prefix="/api/admin/settings", tags=["settings"])


@router.get("")
async def list_settings(
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all system settings."""
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return {
        "code": 0,
        "data": [
            {"key": s.key, "value": s.value, "description": s.description}
            for s in settings
        ],
    }


@router.put("")
async def update_setting(
    req: SystemSettingUpdate,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upsert a system setting."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == req.key))
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = req.value
        if req.description is not None:
            setting.description = req.description
    else:
        setting = SystemSetting(key=req.key, value=req.value, description=req.description)
        db.add(setting)

    await db.flush()
    return {"code": 0, "message": "设置已更新"}
