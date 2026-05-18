"""/v1 proxy gateway: OpenAI-compatible API endpoint."""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, get_redis
from app.models import (
    User, Asset, AssetType, TrafficConfig, TrafficAssetLink,
    TrafficGuardrailEntry, Guardrail, GuardrailPosition, HitAction,
    RequestLog, PointsConsumption,
)
from app.middleware import get_user_by_api_key
from app.gateway import execute_guardrail_chain
from datetime import datetime, timezone
import uuid
import json
import time
import litellm
import logging

# Suppress LiteLLM verbose logs and drop unsupported params
litellm.drop_params = True
litellm.set_verbose = False
litellm.suppress_debug_info = True

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["proxy"])


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    current_user: User = Depends(get_user_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    OpenAI-compatible chat completions endpoint.
    Flow: authenticate -> match model/asset -> pre guardrails -> forward -> post guardrails -> return
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    model = body.get("model", "")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    request_id = "req_" + uuid.uuid4().hex[:16]
    received_at = datetime.now(timezone.utc)

    # 1. Match model to user's asset -> traffic config
    asset_result = await db.execute(
        select(Asset).where(
            Asset.owner_id == current_user.id,
            Asset.type == AssetType.llm,
            Asset.enabled == True,
        )
    )
    assets = asset_result.scalars().all()

    matched_asset = None
    for asset in assets:
        if asset.model_names and model in asset.model_names:
            matched_asset = asset
            break

    if not matched_asset:
        # Try matching by name
        for asset in assets:
            if asset.name == model:
                matched_asset = asset
                break

    if not matched_asset:
        raise HTTPException(status_code=404, detail=f"Model '{model}' not found")

    # Find traffic config linked to this asset
    link_result = await db.execute(
        select(TrafficAssetLink).where(TrafficAssetLink.asset_id == matched_asset.id)
    )
    links = link_result.scalars().all()

    traffic_config = None
    pre_guardrails = []
    post_guardrails = []

    if links:
        tc_result = await db.execute(
            select(TrafficConfig).where(
                TrafficConfig.id.in_([l.traffic_config_id for l in links]),
                TrafficConfig.enabled == True,
            )
        )
        traffic_config = tc_result.scalars().first()

    if traffic_config:
        # Get guardrail entries
        entry_result = await db.execute(
            select(TrafficGuardrailEntry, Guardrail)
            .join(Guardrail)
            .where(
                TrafficGuardrailEntry.traffic_config_id == traffic_config.id,
                TrafficGuardrailEntry.enabled == True,
                Guardrail.enabled == True,
            )
            .order_by(TrafficGuardrailEntry.position, TrafficGuardrailEntry.priority)
        )
        for entry, guardrail in entry_result:
            gr_entry = {
                "guardrail": guardrail,
                "priority": entry.priority,
            }
            if entry.position == GuardrailPosition.pre:
                pre_guardrails.append(gr_entry)
            else:
                post_guardrails.append(gr_entry)

    # 2. Execute pre guardrails
    guardrail_results = []
    if pre_guardrails:
        pre_result = await execute_guardrail_chain(
            pre_guardrails, messages, request_id, current_user.id, model, "pre",
            execution_mode=traffic_config.execution_mode if traffic_config else "serial",
        )
        guardrail_results.extend(pre_result.get("results", []))

        if pre_result["verdict"] == "block":
            # Log and return block
            log = RequestLog(
                user_id=current_user.id,
                request_id=request_id,
                api_key_hash="",
                model=model,
                traffic_config_id=traffic_config.id if traffic_config else None,
                asset_id=matched_asset.id,
                request_messages=messages,
                request_tokens=sum(len(json.dumps(m).split()) for m in messages),
                received_at=received_at,
                completed_at=datetime.now(timezone.utc),
                latency_ms=int((datetime.now(timezone.utc) - received_at).total_seconds() * 1000),
                status="blocked_pre",
                blocked_by=pre_result.get("blocked_by", "unknown"),
                block_reason=next((r.get("reason") for r in guardrail_results if r.get("verdict") == "block"), ""),
                points_consumed=1,
                guardrail_results=guardrail_results,
            )
            db.add(log)
            await db.flush()

            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": f"Content blocked by guardrail: {pre_result.get('blocked_by')}",
                        "type": "guardrail_blocked",
                        "code": "content_filtered",
                    }
                },
            )

        # Apply corrections
        if pre_result["verdict"] == "correct":
            messages = pre_result["messages"]

    # 3. Deduct points
    points_to_deduct = 1  # Base cost; scale by tokens in production
    if current_user.balance < points_to_deduct:
        raise HTTPException(status_code=402, detail="积分不足")

    current_user.balance -= points_to_deduct
    consumption = PointsConsumption(
        user_id=current_user.id,
        points=points_to_deduct,
        description=f"Request: {model}",
    )
    db.add(consumption)

    # 4. Forward to LLM via LiteLLM
    try:
        # Build LiteLLM kwargs using the asset's provider config
        # For custom endpoints, use openai/ prefix with base_url
        provider_prefix = (matched_asset.protocol or "openai").lower()
        model_str = f"{provider_prefix}/{model}"

        litellm_kwargs = {
            "model": model_str,
            "messages": messages,
            "api_key": matched_asset.api_key or "dummy",
        }

        # Use base_url for custom API endpoints
        base_url = (matched_asset.base_url or "").rstrip("/")
        if base_url and "api.openai.com" not in base_url:
            # Auto-upgrade http:// to https:// to prevent POST→GET redirect trap.
            # httpx (used by OpenAI SDK) follows 301/302 redirects but changes
            # POST to GET per RFC 7231, causing "Invalid URL (GET /...)" errors.
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            if parsed.scheme == "http" and parsed.hostname not in (
                "localhost", "127.0.0.1", "0.0.0.0", "::1",
            ):
                logger.warning(
                    f"Auto-upgrading base_url from http to https to avoid "
                    f"POST→GET redirect trap: {base_url}"
                )
                base_url = base_url.replace("http://", "https://", 1)
            litellm_kwargs["api_base"] = base_url

        if stream:
            litellm_kwargs["stream"] = True
        if matched_asset.max_tokens:
            litellm_kwargs["max_tokens"] = matched_asset.max_tokens
        if matched_asset.temperature is not None:
            litellm_kwargs["temperature"] = matched_asset.temperature

        if stream:
            async def stream_response():
                collected_content = ""
                collected_tokens = 0
                response = await litellm.acompletion(**litellm_kwargs)
                async for chunk in response:
                    chunk_json = chunk.model_dump_json()
                    collected_content += chunk.choices[0].delta.content or ""
                    collected_tokens += 1
                    yield f"data: {chunk_json}\n\n"

                # Execute post guardrails on complete content
                if post_guardrails:
                    post_messages = [{"role": "assistant", "content": collected_content}]
                    post_result = await execute_guardrail_chain(
                        post_guardrails, post_messages, request_id, current_user.id, model, "post",
                        execution_mode=traffic_config.execution_mode if traffic_config else "serial",
                    )
                    guardrail_results.extend(post_result.get("results", []))

                # Log
                log = RequestLog(
                    user_id=current_user.id,
                    request_id=request_id,
                    model=model,
                    traffic_config_id=traffic_config.id if traffic_config else None,
                    asset_id=matched_asset.id,
                    request_messages=messages,
                    request_tokens=sum(len(json.dumps(m).split()) for m in messages),
                    response_content=collected_content,
                    response_tokens=collected_tokens,
                    received_at=received_at,
                    completed_at=datetime.now(timezone.utc),
                    latency_ms=int((datetime.now(timezone.utc) - received_at).total_seconds() * 1000),
                    status="completed",
                    cost=0.0,
                    points_consumed=points_to_deduct,
                    guardrail_results=guardrail_results,
                )
                db.add(log)
                await db.flush()

                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_response(), media_type="text/event-stream")
        else:
            response = await litellm.acompletion(**litellm_kwargs)
            response_content = response.choices[0].message.content
            response_tokens = response.usage.completion_tokens if response.usage else 0

            # 5. Execute post guardrails
            if post_guardrails:
                post_messages = [{"role": "assistant", "content": response_content}]
                post_result = await execute_guardrail_chain(
                    post_guardrails, post_messages, request_id, current_user.id, model, "post",
                    execution_mode=traffic_config.execution_mode if traffic_config else "serial",
                )
                guardrail_results.extend(post_result.get("results", []))

                if post_result["verdict"] == "block":
                    log = RequestLog(
                        user_id=current_user.id,
                        request_id=request_id,
                        model=model,
                        traffic_config_id=traffic_config.id if traffic_config else None,
                        asset_id=matched_asset.id,
                        request_messages=messages,
                        request_tokens=sum(len(json.dumps(m).split()) for m in messages),
                        response_content=response_content,
                        response_tokens=response_tokens,
                        received_at=received_at,
                        completed_at=datetime.now(timezone.utc),
                        latency_ms=int((datetime.now(timezone.utc) - received_at).total_seconds() * 1000),
                        status="blocked_post",
                        blocked_by=post_result.get("blocked_by", "unknown"),
                        block_reason=next((r.get("reason") for r in guardrail_results if r.get("verdict") == "block"), ""),
                        cost=0.0,
                        points_consumed=points_to_deduct,
                        guardrail_results=guardrail_results,
                    )
                    db.add(log)
                    await db.flush()

                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": {
                                "message": f"Response blocked by guardrail: {post_result.get('blocked_by')}",
                                "type": "guardrail_blocked",
                                "code": "content_filtered",
                            }
                        },
                    )

            # 6. Log and return
            log = RequestLog(
                user_id=current_user.id,
                request_id=request_id,
                model=model,
                traffic_config_id=traffic_config.id if traffic_config else None,
                asset_id=matched_asset.id,
                request_messages=messages,
                request_tokens=sum(len(json.dumps(m).split()) for m in messages),
                response_content=response_content,
                response_tokens=response_tokens,
                received_at=received_at,
                completed_at=datetime.now(timezone.utc),
                latency_ms=int((datetime.now(timezone.utc) - received_at).total_seconds() * 1000),
                status="completed",
                cost=0.0,
                points_consumed=points_to_deduct,
                guardrail_results=guardrail_results,
            )
            db.add(log)
            await db.flush()

            return response.model_dump()

    except litellm.exceptions.APIError as e:
        logger.error(f"LiteLLM API error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")
    except litellm.exceptions.AuthenticationError as e:
        logger.error(f"LiteLLM auth error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Authentication failed with LLM provider: {str(e)}")
    except litellm.exceptions.Timeout as e:
        logger.error(f"LiteLLM timeout: {e}", exc_info=True)
        raise HTTPException(status_code=504, detail=f"LLM provider timeout: {str(e)}")
    except Exception as e:
        logger.error(f"Proxy internal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/models")
async def list_models(
    current_user: User = Depends(get_user_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List available models for this user."""
    result = await db.execute(
        select(Asset).where(
            Asset.owner_id == current_user.id,
            Asset.type == AssetType.llm,
            Asset.enabled == True,
        )
    )
    assets = result.scalars().all()

    models = []
    for asset in assets:
        for model_name in (asset.model_names or [asset.name]):
            models.append({
                "id": model_name,
                "object": "model",
                "owned_by": asset.provider,
            })

    return {"object": "list", "data": models}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
