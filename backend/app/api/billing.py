
"""Billing and points API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import User, RechargeOrder, PointsConsumption
from app.schemas import RechargeRequest, PointsConsumptionOut
from app.middleware import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/consumption")
async def list_consumption(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List points consumption history."""
    query = select(PointsConsumption).where(PointsConsumption.user_id == current_user.id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(desc(PointsConsumption.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [PointsConsumptionOut.model_validate(i).model_dump() for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/recharge")
async def create_recharge(
    req: RechargeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a recharge order."""
    order = RechargeOrder(
        user_id=current_user.id,
        amount_points=req.amount_points,
        amount_money=req.amount_money,
    )
    db.add(order)
    await db.flush()

    return {"code": 0, "data": {"order_id": order.id, "amount_points": order.amount_points}}


@router.post("/recharge/{order_id}/confirm")
async def confirm_recharge(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a recharge (in production, this would be a callback from payment)."""
    from app.models import RechargeStatus
    from datetime import datetime, timezone

    result = await db.execute(
        select(RechargeOrder).where(
            RechargeOrder.id == order_id,
            RechargeOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.status = RechargeStatus.completed
    order.completed_at = datetime.now(timezone.utc)

    # Add points to user
    current_user.balance += order.amount_points

    await db.flush()
    return {"code": 0, "data": {"balance": current_user.balance}}


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user balance."""
    return {"code": 0, "data": {"balance": current_user.balance, "user_id": current_user.id}}
