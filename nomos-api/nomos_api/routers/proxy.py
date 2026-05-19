"""Gateway proxy — forwards chat to LLM provider.

Two modes:
1. Direct LLM: If NOMOS_LLM_BASE_URL is set, bypasses OpenClaw agent loop
   and calls the provider API directly. Best for simple chat.
2. Gateway Agent: Falls back to OpenClaw /v1/chat/completions (agent loop
   with tools, memory, sessions). Best for agentic workflows.
"""

from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import check_agent_access
from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import Agent, User
from nomos_api.routers.auth import get_current_user
from nomos_api.services import memory
from nomos_api.services.context_pipeline import ContextPipeline
from nomos_api.schemas import (
    ProxyChatRequest,
    ProxyChatResponse,
    ProxyStatusResponse,
)

logger = logging.getLogger("nomos-api")

router = APIRouter(prefix="/api", tags=["proxy"])


def _has_direct_llm() -> bool:
    """Check if direct LLM provider is configured."""
    return bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)


async def _gateway_fetch(
    method: str, path: str, json_body: dict | None = None, request_id: str | None = None
) -> dict | None:
    """HTTP request to OpenClaw Gateway. Returns parsed JSON or None on failure."""
    url = f"{settings.gateway_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {settings.gateway_token}",
        "x-openclaw-scopes": "operator.read,operator.write,operator.admin",
    }
    # Propagate the correlation id to the egress hop so traces span the
    # API -> gateway boundary.
    if request_id:
        headers["X-Request-ID"] = request_id

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.request(method, url, json=json_body, headers=headers)
            return response.json()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.debug("Gateway unreachable at %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.debug("Gateway error at %s: %s", url, exc)
        return None


async def _direct_llm_chat(
    messages: list[dict], model: str | None = None, request_id: str | None = None
) -> dict | None:
    """Direct LLM API call (OpenAI-compatible). Bypasses OpenClaw agent loop."""
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if request_id:
        headers["X-Request-ID"] = request_id
    body = {
        "model": model or settings.llm_model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=body, headers=headers)
            if response.status_code == 429:
                logger.warning("LLM rate limit reached (429)")
                return {"error": {"message": "Rate limit reached. Please try again later."}}
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.warning("LLM provider timeout at %s", url)
        return None
    except httpx.HTTPStatusError as exc:
        # Do NOT log the raw provider response body — it can echo back the
        # Authorization bearer / API key or other secrets (H5).
        logger.warning("LLM provider error %d (body suppressed)", exc.response.status_code)
        return {"error": {"message": f"LLM provider error: {exc.response.status_code}"}}
    except Exception as exc:
        logger.warning("LLM provider error at %s: %s", url, exc)
        return None


@router.get("/proxy/status", response_model=ProxyStatusResponse)
async def gateway_status() -> ProxyStatusResponse:
    """Check LLM provider / Gateway health."""
    if _has_direct_llm():
        # Test direct LLM provider
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.llm_base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                )
                if response.status_code < 500:
                    return ProxyStatusResponse(status="online", version="direct-llm")
        except Exception:
            pass
        return ProxyStatusResponse(status="offline")

    result = await _gateway_fetch("GET", "/healthz")
    if result is None:
        return ProxyStatusResponse(status="offline")

    return ProxyStatusResponse(
        status="online",
        version=result.get("version"),
        agents_count=result.get("agents_count"),
    )


@router.post("/proxy/chat", response_model=ProxyChatResponse)
async def proxy_chat(
    request: ProxyChatRequest,
    http_request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProxyChatResponse:
    """Proxy chat to LLM.

    Uses direct LLM provider if configured (NOMOS_LLM_BASE_URL),
    otherwise falls back to OpenClaw Gateway agent loop.

    AuthZ: requires an authenticated user (console JWT cookie) and that the
    user owns the target agent (IDOR fix — H3). Outbound provider/gateway
    URLs are taken ONLY from settings (settings.gateway_url /
    settings.llm_base_url), never from request- or agent-controlled input,
    so this endpoint cannot be used as an SSRF pivot.
    """
    session_id = request.session_id or str(uuid.uuid4())
    request_id = getattr(http_request.state, "request_id", None)

    # Agent must exist and be owned by the caller (no chatting as arbitrary
    # agent_id). check_agent_access allows admins and the owning user.
    agent = await db.get(Agent, request.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id!r} not found")
    check_agent_access(user, agent, "chat")

    # Resolve model from agent manifest if available
    model = None
    if agent and agent.manifest_data:
        manifest = agent.manifest_data if isinstance(agent.manifest_data, dict) else {}
        llm_provider = manifest.get("llm_provider")
        if llm_provider:
            model = llm_provider

    # Build the managed context from PRIOR turns only, append the new user
    # message in-memory, and persist BOTH turns ONLY after a successful LLM
    # response. Persisting the user turn upfront orphans it in agent_memory
    # on LLM failure (next attempt then sees [user, user] history — state
    # corruption). Post-success persistence keeps the chain consistent.
    pipeline = ContextPipeline()
    prior = await pipeline.get_managed_context(db, request.agent_id, session_id)
    messages = prior + [{"role": "user", "content": request.message}]

    # Mode 1: Direct LLM (preferred for chat)
    if _has_direct_llm():
        result = await _direct_llm_chat(messages, model=model, request_id=request_id)

        if result is None:
            raise HTTPException(
                status_code=502,
                detail="LLM-Provider ist nicht erreichbar. Bitte pruefen Sie die Konfiguration.",
            )

        if "error" in result:
            error_msg = result["error"].get("message", "Unbekannter LLM-Fehler")
            raise HTTPException(status_code=502, detail=error_msg)

        choices = result.get("choices", [])
        response_text = ""
        if choices:
            response_text = choices[0].get("message", {}).get("content", "")

        # Persist user-then-assistant ONLY after a successful LLM call. This
        # prevents the orphan-user-turn corruption observed when persistence
        # happened before the LLM call.
        await pipeline.process_new_message(db, request.agent_id, session_id, "user", request.message)
        await memory.store_message(db, request.agent_id, session_id, "assistant", response_text)

        return ProxyChatResponse(response=response_text, session_id=session_id)

    # Mode 2: Gateway agent loop (fallback)
    gateway_model = model or "openclaw"
    result = await _gateway_fetch(
        "POST",
        "/v1/chat/completions",
        {"model": gateway_model, "messages": messages},
        request_id=request_id,
    )

    if result is None:
        raise HTTPException(
            status_code=502,
            detail="OpenClaw Gateway ist nicht erreichbar. Stellen Sie sicher, dass der Gateway-Dienst laeuft.",
        )

    if "error" in result:
        error_msg = result["error"].get("message", "Unbekannter Gateway-Fehler")
        if "internal error" in error_msg.lower() or "No API key" in error_msg or "auth" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Kein LLM-Provider konfiguriert. Bitte konfigurieren Sie einen Anbieter in den Einstellungen.",
            )
        raise HTTPException(status_code=502, detail=error_msg)

    choices = result.get("choices", [])
    response_text = ""
    if choices:
        response_text = choices[0].get("message", {}).get("content", "")

    # Persist user-then-assistant ONLY after a successful gateway response.
    await pipeline.process_new_message(db, request.agent_id, session_id, "user", request.message)
    await memory.store_message(db, request.agent_id, session_id, "assistant", response_text)

    return ProxyChatResponse(response=response_text, session_id=session_id)
