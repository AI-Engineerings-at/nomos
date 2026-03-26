"""Gateway proxy — forwards chat to OpenClaw /v1/chat/completions (OpenAI-compatible)."""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import Agent
from nomos_api.schemas import (
    ProxyChatRequest,
    ProxyChatResponse,
    ProxyStatusResponse,
)

logger = logging.getLogger("nomos-api")

router = APIRouter(prefix="/api", tags=["proxy"])


async def _gateway_fetch(method: str, path: str, json_body: dict | None = None) -> dict | None:
    """HTTP request to OpenClaw Gateway. Returns parsed JSON or None on failure."""
    import asyncio
    import json
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError

    url = urljoin(settings.gateway_url.rstrip("/") + "/", path.lstrip("/"))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.gateway_token}",
    }
    data = json.dumps(json_body).encode("utf-8") if json_body else None

    def _do_request() -> dict | None:
        try:
            req = Request(url, data=data, headers=headers, method=method)
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            # HTTP errors (4xx, 5xx) still have a response body we can parse
            try:
                body = exc.read().decode("utf-8")
                return json.loads(body)
            except Exception:
                logger.debug("Gateway HTTP %d at %s", exc.code, url)
                return None
        except (URLError, OSError, TimeoutError) as exc:
            logger.debug("Gateway unreachable at %s: %s", url, exc)
            return None
        except (OSError, TimeoutError) as exc:
            logger.debug("Gateway unreachable at %s: %s", url, exc)
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _do_request)


@router.get("/proxy/status", response_model=ProxyStatusResponse)
async def gateway_status() -> ProxyStatusResponse:
    """Check OpenClaw Gateway health."""
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
    request: ProxyChatRequest, db: AsyncSession = Depends(get_db)
) -> ProxyChatResponse:
    """Proxy chat to OpenClaw Gateway via OpenAI-compatible /v1/chat/completions.

    Model is derived from agent manifest (llm_provider). If no provider is
    configured, the gateway default is used. Customer chooses their own LLM.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Resolve model from agent manifest if available
    model = "openclaw/default"
    agent = await db.get(Agent, request.agent_id)
    if agent and agent.manifest_data:
        manifest = agent.manifest_data if isinstance(agent.manifest_data, dict) else {}
        llm_provider = manifest.get("llm_provider")
        if llm_provider:
            model = llm_provider

    # OpenAI-compatible chat completions format
    result = await _gateway_fetch("POST", "/v1/chat/completions", {
        "model": model,
        "messages": [{"role": "user", "content": request.message}],
    })

    if result is None:
        raise HTTPException(
            status_code=502,
            detail="OpenClaw Gateway ist nicht erreichbar. Stellen Sie sicher, dass der Gateway-Dienst laeuft.",
        )

    # Handle error response from gateway (e.g. no API key configured)
    if "error" in result:
        error_msg = result["error"].get("message", "Unbekannter Gateway-Fehler")
        # Gateway masks auth errors as "internal error" — check logs for details
        if "internal error" in error_msg.lower() or "No API key" in error_msg or "auth" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Kein LLM-Provider konfiguriert. Bitte konfigurieren Sie einen Anbieter in den Einstellungen.",
            )
        raise HTTPException(status_code=502, detail=error_msg)

    # Extract response from OpenAI format
    choices = result.get("choices", [])
    response_text = ""
    if choices:
        response_text = choices[0].get("message", {}).get("content", "")

    return ProxyChatResponse(
        response=response_text,
        session_id=session_id,
    )
