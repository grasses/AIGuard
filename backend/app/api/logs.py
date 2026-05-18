
"""Request logs API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import User, RequestLog
from app.schemas import RequestLogOut, RequestLogDetailOut
from app.middleware import get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    model: str = Query(None),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List request logs."""
    query = select(RequestLog).where(RequestLog.user_id == current_user.id)

    if status:
        query = query.where(RequestLog.status == status)
    if model:
        query = query.where(RequestLog.model == model)
    if search:
        query = query.where(RequestLog.request_id.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(desc(RequestLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [RequestLogOut.model_validate(l).model_dump() for l in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{log_id}")
async def get_log_detail(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed log entry."""
    result = await db.execute(
        select(RequestLog).where(RequestLog.id == log_id, RequestLog.user_id == current_user.id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    return {"code": 0, "data": RequestLogDetailOut.model_validate(log).model_dump()}
