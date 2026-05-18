
"""Asset management API: CRUD for LLM, MCP, Memory assets."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, Asset, AssetType
from app.schemas import (
    AssetCreateRequest, AssetUpdateRequest, AssetOut,
    AssetTestResult, AssetToggleRequest, PaginatedResponse, ApiResponse,
)
from app.middleware import get_current_user
from datetime import datetime, timezone
import httpx

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("")
async def list_assets(
    type: str = Query(None, description="llm/mcp/memory"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    enabled: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assets with optional filters."""
    query = select(Asset).where(Asset.owner_id == current_user.id)

    if type:
        query = query.where(Asset.type == type)
    if search:
        query = query.where(
            (Asset.name.ilike(f"%{search}%")) |
            (Asset.model_names.cast(str).ilike(f"%{search}%")) |
            (Asset.tool_name.ilike(f"%{search}%"))
        )
    if enabled is not None:
        query = query.where(Asset.enabled == enabled)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(Asset.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [AssetOut.model_validate(a).model_dump() for a in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("", status_code=201)
async def create_asset(
    req: AssetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new asset."""
    asset = Asset(
        owner_id=current_user.id,
        type=req.type,
        name=req.name,
        enabled=req.enabled,
        visibility=req.visibility,
        notes=req.notes,
        provider=req.provider,
        protocol=req.protocol,
        base_url=req.base_url,
        api_key=req.api_key,
        model_names=req.model_names,
        max_tokens=req.max_tokens,
        timeout_seconds=req.timeout_seconds,
        max_retries=req.max_retries,
        temperature=req.temperature,
        group_ids=req.group_ids,
        tool_name=req.tool_name,
        description=req.description,
        endpoint_url=req.endpoint_url,
        method=req.method,
        authentication_type=req.authentication_type,
        parameter_schema=req.parameter_schema,
        required_parameters=req.required_parameters,
        response_mapping=req.response_mapping,
        index_name=req.index_name,
        max_tokens_capacity=req.max_tokens_capacity,
        persist=req.persist,
        expire_days=req.expire_days,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    return {"code": 0, "data": AssetOut.model_validate(asset).model_dump()}


@router.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get asset by ID."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.owner_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    return {"code": 0, "data": AssetOut.model_validate(asset).model_dump()}


@router.put("/{asset_id}")
async def update_asset(
    asset_id: str,
    req: AssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an asset."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.owner_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)

    await db.flush()
    await db.refresh(asset)
    return {"code": 0, "data": AssetOut.model_validate(asset).model_dump()}


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.owner_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    await db.delete(asset)
    await db.flush()
    return {"code": 0, "message": "删除成功"}


@router.post("/{asset_id}/test")
async def test_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test connectivity of an asset."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.owner_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    start = datetime.now(timezone.utc)
    try:
        headers = {}
        if asset.api_key:
            headers["Authorization"] = f"Bearer {asset.api_key}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{asset.base_url.rstrip('/')}/models" if asset.type == AssetType.llm else asset.base_url
            resp = await client.get(url, headers=headers)
            success = resp.status_code < 500
            message = "连接成功" if success else f"HTTP {resp.status_code}"

        latency = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        asset.connectivity = "healthy" if success else "unhealthy"
        await db.flush()

        return {
            "code": 0,
            "data": {
                "success": success,
                "latency_ms": latency,
                "message": message,
                "tested_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception as e:
        latency = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        asset.connectivity = "unhealthy"
        await db.flush()

        return {
            "code": 0,
            "data": {
                "success": False,
                "latency_ms": latency,
                "message": str(e),
                "tested_at": datetime.now(timezone.utc).isoformat(),
            },
        }


@router.post("/{asset_id}/toggle")
async def toggle_asset(
    asset_id: str,
    req: AssetToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable an asset."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.owner_id == current_user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    asset.enabled = req.enabled
    await db.flush()
    return {"code": 0, "data": {"id": asset.id, "enabled": asset.enabled}}
