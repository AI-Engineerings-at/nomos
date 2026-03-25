"""Gateway proxy endpoints — forwards requests to OpenClaw Gateway."""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urljoin

from fastapi import APIRouter, HTTPException

from nomos_api.config import settings
from nomos_api.schemas import (
    ProxyChatRequest,
    ProxyChatResponse,
    ProxyStatusResponse,
)

logger = logging.getLogger("nomos-api")

router = APIRouter(prefix="/api", tags=["proxy"])


async def _gateway_fetch(method: str, path: str, json_body: dict | None = None) -> dict | None:
    """Make an HTTP request to the OpenClaw Gateway.

    Uses the standard library urllib to avoid adding httpx as a runtime dependency
    for the proxy layer. Returns parsed JSON on success, None on connection failure.
    """
    import asyncio
    import json
    from urllib.request import Request, urlopen
    from urllib.error import URLError

    url = urljoin(settings.gateway_url.rstrip("/") + "/", path.lstrip("/"))
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps(json_body).encode("utf-8") if json_body else None

    def _do_request() -> dict | None:
        try:
            req = Request(url, data=data, headers=headers, method=method)
            with urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except (URLError, OSError, TimeoutError) as exc:
            logger.debug("Gateway unreachable at %s: %s", url, exc)
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _do_request)


@router.get("/proxy/status", response_model=ProxyStatusResponse)
async def gateway_status() -> ProxyStatusResponse:
    """Check OpenClaw Gateway health.

    Returns online/offline status. Gracefully handles the case when
    the gateway is not running.
    """
    result = await _gateway_fetch("GET", "/health")
    if result is None:
        return ProxyStatusResponse(status="offline")

    return ProxyStatusResponse(
        status="online",
        version=result.get("version"),
        agents_count=result.get("agents_count"),
    )


@router.post("/proxy/chat", response_model=ProxyChatResponse)
async def proxy_chat(request: ProxyChatRequest) -> ProxyChatResponse:
    """Proxy a chat message to the OpenClaw Gateway.

    Forwards the message to the gateway and returns the response.
    If the gateway is not reachable, returns 502 Bad Gateway.
    """
    session_id = request.session_id or str(uuid.uuid4())

    result = await _gateway_fetch("POST", "/api/chat", {
        "agent_id": request.agent_id,
        "message": request.message,
        "session_id": session_id,
    })

    if result is None:
        raise HTTPException(
            status_code=502,
            detail="OpenClaw Gateway is not reachable. Ensure the gateway is running.",
        )

    return ProxyChatResponse(
        response=result.get("response", ""),
        session_id=result.get("session_id", session_id),
    )
