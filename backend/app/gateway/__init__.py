"""Proxy gateway: handles /v1 requests, executes guardrail chains, forwards via LiteLLM."""
from typing import Optional
import httpx
import litellm
from litellm import completion, acompletion
from app.models import Guardrail, GuardrailPosition, HitAction, RequestLog, GuardrailDomain


async def execute_guardrail(
    guardrail: Guardrail,
    messages: list[dict],
    request_id: str,
    user_id: str,
    model: str,
    metadata: dict = None,
) -> dict:
    """Execute a single guardrail HTTP call."""
    payload = {
        "request_id": request_id,
        "user_id": user_id,
        "domain": guardrail.domain.value if isinstance(guardrail.domain, GuardrailDomain) else guardrail.domain,
        "position": guardrail.position.value if isinstance(guardrail.position, GuardrailPosition) else guardrail.position,
        "model": model,
        "messages": messages,
        "metadata": {
            "guardrail_id": guardrail.id,
            **(metadata or {}),
        },
        "ext_params": guardrail.ext_params or {},
    }

    async with httpx.AsyncClient(timeout=float(guardrail.timeout_ms) / 1000) as client:
        resp = await client.post(guardrail.endpoint_url, json=payload)
        return resp.json()


async def execute_guardrail_chain(
    guardrails: list[dict],  # [{"guardrail": Guardrail, "priority": int}, ...]
    messages: list[dict],
    request_id: str,
    user_id: str,
    model: str,
    position: str,
    execution_mode: str = "serial",
) -> dict:
    """
    Execute a chain of guardrails.
    Returns: {"verdict": "pass"|"block"|"correct", "messages": [...], "results": [...]}
    """
    results = []
    current_messages = messages

    # Sort by priority
    sorted_guardrails = sorted(guardrails, key=lambda g: g.get("priority", 50))

    if execution_mode == "parallel":
        # Parallel execution
        import asyncio
        tasks = [
            execute_guardrail(g["guardrail"], current_messages, request_id, user_id, model)
            for g in sorted_guardrails
        ]
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                results.append({"guardrail_id": sorted_guardrails[i]["guardrail"].id, "verdict": "error", "reason": str(result)})
                continue

            results.append({
                "guardrail_id": sorted_guardrails[i]["guardrail"].id,
                "name": sorted_guardrails[i]["guardrail"].name,
                "guardrail_type": sorted_guardrails[i]["guardrail"].guardrail_type,
                "verdict": result.get("verdict", "error"),
                "reason": result.get("reason", ""),
                "confidence": result.get("confidence", 0.0),
            })

            if result.get("verdict") == "block":
                return {"verdict": "block", "messages": current_messages, "results": results, "blocked_by": sorted_guardrails[i]["guardrail"].name}
            elif result.get("verdict") == "correct":
                corrected = result.get("corrected_content")
                if corrected:
                    current_messages = [{"role": "assistant", "content": corrected}] if position == "post" else [{"role": "user", "content": corrected}]
    else:
        # Serial execution (default)
        for g_entry in sorted_guardrails:
            g = g_entry["guardrail"]
            result = await execute_guardrail(g, current_messages, request_id, user_id, model)

            results.append({
                "guardrail_id": g.id,
                "name": g.name,
                "guardrail_type": g.guardrail_type,
                "verdict": result.get("verdict", "error"),
                "reason": result.get("reason", ""),
                "confidence": result.get("confidence", 0.0),
            })

            if result.get("verdict") == "block":
                return {"verdict": "block", "messages": current_messages, "results": results, "blocked_by": g.name}
            elif result.get("verdict") == "correct":
                corrected = result.get("corrected_content")
                if corrected:
                    current_messages = [{"role": "user", "content": corrected}] if position == "pre" else [{"role": "assistant", "content": corrected}]

    return {"verdict": "pass", "messages": current_messages, "results": results}
