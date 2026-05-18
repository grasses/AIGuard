
"""Traffic configuration API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, TrafficConfig, TrafficAssetLink, TrafficGuardrailEntry, Asset, Guardrail
from app.schemas import (
    TrafficConfigCreateRequest, TrafficConfigUpdateRequest,
    TrafficConfigOut, TrafficConfigDetailOut, TrafficConfigToggleRequest,
)
from app.middleware import get_current_user

router = APIRouter(prefix="/api/traffic-configs", tags=["traffic"])


@router.get("")
async def list_traffic_configs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    enabled: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List traffic configs."""
    query = select(TrafficConfig).where(TrafficConfig.owner_id == current_user.id)
    if search:
        query = query.where(TrafficConfig.name.ilike(f"%{search}%"))
    if enabled is not None:
        query = query.where(TrafficConfig.enabled == enabled)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(TrafficConfig.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    configs = result.scalars().all()

    items = []
    for tc in configs:
        # Count guardrails
        pre_count = await db.execute(
            select(func.count()).select_from(TrafficGuardrailEntry).where(
                TrafficGuardrailEntry.traffic_config_id == tc.id,
                TrafficGuardrailEntry.position == "pre"
            )
        )
        post_count = await db.execute(
            select(func.count()).select_from(TrafficGuardrailEntry).where(
                TrafficGuardrailEntry.traffic_config_id == tc.id,
                TrafficGuardrailEntry.position == "post"
            )
        )

        # Get linked assets
        link_result = await db.execute(
            select(Asset.name).join(TrafficAssetLink).where(
                TrafficAssetLink.traffic_config_id == tc.id
            )
        )
        asset_names = link_result.scalars().all()

        items.append({
            "id": tc.id,
            "owner_id": tc.owner_id,
            "name": tc.name,
            "description": tc.description,
            "enabled": tc.enabled,
            "execution_mode": tc.execution_mode,
            "assets_summary": [{"name": n} for n in asset_names],
            "pre_guardrail_count": pre_count.scalar() or 0,
            "post_guardrail_count": post_count.scalar() or 0,
            "request_count_24h": 0,
            "block_rate_24h": 0.0,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
            "updated_at": tc.updated_at.isoformat() if tc.updated_at else None,
        })

    return {"code": 0, "data": {"items": items, "total": total, "page": page, "page_size": page_size}}


@router.post("", status_code=201)
async def create_traffic_config(
    req: TrafficConfigCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create traffic config with assets and guardrails."""
    tc = TrafficConfig(
        owner_id=current_user.id,
        name=req.name,
        description=req.description,
        enabled=req.enabled,
        execution_mode=req.execution_mode,
    )
    db.add(tc)
    await db.flush()

    # Link assets
    for aid in req.asset_ids:
        link = TrafficAssetLink(traffic_config_id=tc.id, asset_id=aid)
        db.add(link)

    # Link guardrails
    for entry in req.guardrail_entries:
        ge = TrafficGuardrailEntry(
            traffic_config_id=tc.id,
            guardrail_id=entry["guardrail_id"],
            position=entry["position"],
            priority=entry.get("priority", 50),
            enabled=entry.get("enabled", True),
        )
        db.add(ge)

    await db.flush()
    await db.refresh(tc)

    return {"code": 0, "data": {"id": tc.id, "name": tc.name}}


@router.get("/{config_id}")
async def get_traffic_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get traffic config detail."""
    result = await db.execute(
        select(TrafficConfig).where(TrafficConfig.id == config_id, TrafficConfig.owner_id == current_user.id)
    )
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="流量配置不存在")

    # Get assets
    link_result = await db.execute(
        select(TrafficAssetLink).where(TrafficAssetLink.traffic_config_id == tc.id)
    )
    asset_ids = [l.asset_id for l in link_result.scalars().all()]

    # Get guardrail entries
    entry_result = await db.execute(
        select(TrafficGuardrailEntry, Guardrail.name).join(Guardrail).where(
            TrafficGuardrailEntry.traffic_config_id == tc.id
        ).order_by(TrafficGuardrailEntry.position, TrafficGuardrailEntry.priority)
    )
    entries = []
    for entry, gr_name in entry_result:
        entries.append({
            "id": entry.id,
            "guardrail_id": entry.guardrail_id,
            "guardrail_name": gr_name,
            "position": entry.position.value,
            "priority": entry.priority,
            "enabled": entry.enabled,
        })

    return {
        "code": 0,
        "data": {
            "id": tc.id,
            "owner_id": tc.owner_id,
            "name": tc.name,
            "description": tc.description,
            "enabled": tc.enabled,
            "execution_mode": tc.execution_mode,
            "asset_ids": asset_ids,
            "guardrail_entries": entries,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
            "updated_at": tc.updated_at.isoformat() if tc.updated_at else None,
        },
    }


@router.put("/{config_id}")
async def update_traffic_config(
    config_id: str,
    req: TrafficConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update traffic config."""
    result = await db.execute(
        select(TrafficConfig).where(TrafficConfig.id == config_id, TrafficConfig.owner_id == current_user.id)
    )
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="流量配置不存在")

    # Update basic fields
    for field in ("name", "description", "enabled", "execution_mode"):
        val = getattr(req, field, None)
        if val is not None:
            setattr(tc, field, val)

    # Replace asset links
    if req.asset_ids is not None:
        await db.execute(
            select(TrafficAssetLink).where(TrafficAssetLink.traffic_config_id == tc.id).delete()
        )
        for aid in req.asset_ids:
            db.add(TrafficAssetLink(traffic_config_id=tc.id, asset_id=aid))

    # Replace guardrail entries
    if req.guardrail_entries is not None:
        await db.execute(
            select(TrafficGuardrailEntry).where(TrafficGuardrailEntry.traffic_config_id == tc.id).delete()
        )
        for entry in req.guardrail_entries:
            db.add(TrafficGuardrailEntry(
                traffic_config_id=tc.id,
                guardrail_id=entry["guardrail_id"],
                position=entry["position"],
                priority=entry.get("priority", 50),
                enabled=entry.get("enabled", True),
            ))

    await db.flush()
    return {"code": 0, "message": "更新成功"}


@router.delete("/{config_id}")
async def delete_traffic_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete traffic config."""
    result = await db.execute(
        select(TrafficConfig).where(TrafficConfig.id == config_id, TrafficConfig.owner_id == current_user.id)
    )
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="流量配置不存在")

    await db.delete(tc)
    await db.flush()
    return {"code": 0, "message": "删除成功"}
