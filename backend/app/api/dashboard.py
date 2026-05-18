
"""Dashboard API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import User, RequestLog, AlertEvent
from app.middleware import get_current_user, get_current_admin

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/user/dashboard/stats")
async def user_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User dashboard statistics."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Total requests
    total = await db.scalar(
        select(func.count()).select_from(RequestLog).where(
            RequestLog.user_id == current_user.id,
            RequestLog.created_at >= since,
        )
    )

    # Blocked
    blocked = await db.scalar(
        select(func.count()).select_from(RequestLog).where(
            RequestLog.user_id == current_user.id,
            RequestLog.created_at >= since,
            RequestLog.status.in_(["blocked_pre", "blocked_post"]),
        )
    )

    # Avg latency
    avg_latency = await db.scalar(
        select(func.avg(RequestLog.latency_ms)).where(
            RequestLog.user_id == current_user.id,
            RequestLog.created_at >= since,
        )
    )

    # Total tokens
    total_tokens = await db.scalar(
        select(func.sum(RequestLog.request_tokens + RequestLog.response_tokens)).where(
            RequestLog.user_id == current_user.id,
            RequestLog.created_at >= since,
        )
    )

    # Points consumed
    points = await db.scalar(
        select(func.sum(RequestLog.points_consumed)).where(
            RequestLog.user_id == current_user.id,
            RequestLog.created_at >= since,
        )
    )

    # Chart data (last 24h by hour)
    chart_data = []
    for i in range(24):
        hour_start = since + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        count = await db.scalar(
            select(func.count()).select_from(RequestLog).where(
                RequestLog.user_id == current_user.id,
                RequestLog.created_at >= hour_start,
                RequestLog.created_at < hour_end,
            )
        )
        chart_data.append({"time": hour_start.strftime("%H:%M"), "count": count or 0})

    return {
        "code": 0,
        "data": {
            "total_requests_24h": total or 0,
            "blocked_requests_24h": blocked or 0,
            "block_rate_24h": round(blocked / total * 100, 1) if total else 0,
            "avg_latency_ms_24h": round(avg_latency, 1) if avg_latency else 0,
            "total_tokens_24h": total_tokens or 0,
            "points_consumed_24h": points or 0,
            "chart_data": chart_data,
        },
    }


@router.get("/admin/dashboard/stats")
async def admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin dashboard statistics (system-wide)."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    total = await db.scalar(
        select(func.count()).select_from(RequestLog).where(RequestLog.created_at >= since)
    )
    blocked = await db.scalar(
        select(func.count()).select_from(RequestLog).where(
            RequestLog.created_at >= since,
            RequestLog.status.in_(["blocked_pre", "blocked_post"]),
        )
    )
    avg_latency = await db.scalar(
        select(func.avg(RequestLog.latency_ms)).where(RequestLog.created_at >= since)
    )
    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(
        select(func.count(func.distinct(RequestLog.user_id))).where(
            RequestLog.created_at >= since,
        )
    )

    # Hourly chart
    chart_data = []
    for i in range(24):
        hour_start = since + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        count = await db.scalar(
            select(func.count()).select_from(RequestLog).where(
                RequestLog.created_at >= hour_start,
                RequestLog.created_at < hour_end,
            )
        )
        chart_data.append({"time": hour_start.strftime("%H:%M"), "count": count or 0})

    return {
        "code": 0,
        "data": {
            "total_requests_24h": total or 0,
            "blocked_requests_24h": blocked or 0,
            "block_rate_24h": round(blocked / total * 100, 1) if total else 0,
            "avg_latency_ms_24h": round(avg_latency, 1) if avg_latency else 0,
            "total_users": total_users or 0,
            "active_users_24h": active_users or 0,
            "chart_data": chart_data,
        },
    }
