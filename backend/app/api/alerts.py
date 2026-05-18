
"""Alert rules and events API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import User, AlertRule, AlertEvent
from app.schemas import (
    AlertRuleCreateRequest, AlertRuleUpdateRequest,
    AlertRuleOut, AlertEventOut,
)
from app.middleware import get_current_user

router = APIRouter(prefix="/api", tags=["alerts"])


# ─── Alert Rules ───

@router.get("/alert-rules")
async def list_alert_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alert rules."""
    query = select(AlertRule).where(AlertRule.user_id == current_user.id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(desc(AlertRule.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [AlertRuleOut.model_validate(r).model_dump() for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/alert-rules", status_code=201)
async def create_alert_rule(
    req: AlertRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an alert rule."""
    rule = AlertRule(user_id=current_user.id, **req.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return {"code": 0, "data": AlertRuleOut.model_validate(rule).model_dump()}


@router.get("/alert-rules/{rule_id}")
async def get_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id, AlertRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    return {"code": 0, "data": AlertRuleOut.model_validate(rule).model_dump()}


@router.put("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    req: AlertRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id, AlertRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="告警规则不存在")

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    await db.flush()
    return {"code": 0, "message": "更新成功"}


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id, AlertRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    await db.delete(rule)
    await db.flush()
    return {"code": 0, "message": "删除成功"}


# ─── Alert Events ───

@router.get("/alerts")
async def list_alert_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alert events."""
    query = select(AlertEvent).where(AlertEvent.user_id == current_user.id)
    if is_read is not None:
        query = query.where(AlertEvent.is_read == is_read)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(desc(AlertEvent.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [AlertEventOut.model_validate(e).model_dump() for e in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/alerts/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all alerts as read."""
    result = await db.execute(
        select(AlertEvent).where(
            AlertEvent.user_id == current_user.id,
            AlertEvent.is_read == False,
        )
    )
    for event in result.scalars():
        event.is_read = True
    await db.flush()
    return {"code": 0, "message": "全部已读"}


@router.get("/alerts/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread alert count."""
    count = await db.scalar(
        select(func.count()).select_from(AlertEvent).where(
            AlertEvent.user_id == current_user.id,
            AlertEvent.is_read == False,
        )
    )
    return {"code": 0, "data": {"count": count or 0}}
