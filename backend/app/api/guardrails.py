
"""Guardrail management API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, Guardrail
from app.schemas import (
    GuardrailCreateRequest, GuardrailUpdateRequest, GuardrailOut,
    GuardrailTestRequest, GuardrailTestResult, GuardrailToggleRequest,
)
from app.middleware import get_current_user
from datetime import datetime, timezone
import httpx

router = APIRouter(prefix="/api/guardrails", tags=["guardrails"])


@router.get("")
async def list_guardrails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    domain: str = Query(None),
    position: str = Query(None),
    type: str = Query(None),
    enabled: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List guardrails with filters."""
    query = select(Guardrail).where(Guardrail.owner_id == current_user.id)

    if search:
        query = query.where(Guardrail.name.ilike(f"%{search}%"))
    if domain:
        query = query.where(Guardrail.domain == domain)
    if position:
        query = query.where(Guardrail.position == position)
    if type:
        query = query.where(Guardrail.guardrail_type == type)
    if enabled is not None:
        query = query.where(Guardrail.enabled == enabled)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Guardrail.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [GuardrailOut.model_validate(g).model_dump() for g in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("", status_code=201)
async def create_guardrail(
    req: GuardrailCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new guardrail."""
    guardrail = Guardrail(
        owner_id=current_user.id,
        **req.model_dump(),
    )
    db.add(guardrail)
    await db.flush()
    await db.refresh(guardrail)
    return {"code": 0, "data": GuardrailOut.model_validate(guardrail).model_dump()}


@router.get("/{guardrail_id}")
async def get_guardrail(
    guardrail_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get guardrail by ID."""
    result = await db.execute(
        select(Guardrail).where(Guardrail.id == guardrail_id, Guardrail.owner_id == current_user.id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="护栏不存在")
    return {"code": 0, "data": GuardrailOut.model_validate(g).model_dump()}


@router.put("/{guardrail_id}")
async def update_guardrail(
    guardrail_id: str,
    req: GuardrailUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a guardrail."""
    result = await db.execute(
        select(Guardrail).where(Guardrail.id == guardrail_id, Guardrail.owner_id == current_user.id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="护栏不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(g, key, value)

    await db.flush()
    await db.refresh(g)
    return {"code": 0, "data": GuardrailOut.model_validate(g).model_dump()}


@router.delete("/{guardrail_id}")
async def delete_guardrail(
    guardrail_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a guardrail."""
    result = await db.execute(
        select(Guardrail).where(Guardrail.id == guardrail_id, Guardrail.owner_id == current_user.id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="护栏不存在")

    await db.delete(g)
    await db.flush()
    return {"code": 0, "message": "删除成功"}


@router.post("/{guardrail_id}/test")
async def test_guardrail(
    guardrail_id: str,
    req: GuardrailTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a guardrail with sample messages."""
    result = await db.execute(
        select(Guardrail).where(Guardrail.id == guardrail_id, Guardrail.owner_id == current_user.id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="护栏不存在")

    start = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=float(g.timeout_ms) / 1000) as client:
            payload = {
                "request_id": "test_" + guardrail_id,
                "user_id": current_user.id,
                "domain": g.domain.value,
                "position": g.position.value,
                "messages": req.messages,
                "metadata": req.metadata,
                "ext_params": g.ext_params or {},
            }
            resp = await client.post(g.endpoint_url, json=payload)
            raw = resp.json()
            latency = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

        return {
            "code": 0,
            "data": {
                "verdict": raw.get("verdict", "unknown"),
                "reason": raw.get("reason", ""),
                "confidence": raw.get("confidence", 0.0),
                "latency_ms": latency,
                "raw_response": raw,
            },
        }
    except Exception as e:
        latency = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return {
            "code": 0,
            "data": {
                "verdict": "error",
                "reason": str(e),
                "confidence": 0.0,
                "latency_ms": latency,
                "raw_response": {"error": str(e)},
            },
        }


@router.post("/{guardrail_id}/toggle")
async def toggle_guardrail(
    guardrail_id: str,
    req: GuardrailToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a guardrail."""
    result = await db.execute(
        select(Guardrail).where(Guardrail.id == guardrail_id, Guardrail.owner_id == current_user.id)
    )
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="护栏不存在")

    g.enabled = req.enabled
    await db.flush()
    return {"code": 0, "data": {"id": g.id, "enabled": g.enabled}}
