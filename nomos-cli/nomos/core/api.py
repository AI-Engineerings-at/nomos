"""HTTP client for the NomOS API.

Provides typed methods for every CLI-relevant endpoint with retry logic,
configurable timeouts, and human-readable error handling.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

_LOGGER = logging.getLogger("nomos.core.api")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "http://localhost:8060"
DEFAULT_TIMEOUT = 10.0  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds between retries

# Human-readable error messages (DE) keyed by HTTP status code.
_STATUS_MESSAGES: dict[int, str] = {
    404: "Nicht gefunden",
    409: "Konflikt",
    400: "Ungueltige Anfrage",
    500: "Interner Serverfehler",
}


def _base_url() -> str:
    return os.environ.get("NOMOS_API_URL", DEFAULT_BASE_URL).rstrip("/")


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------


def _ok(data: Any) -> dict[str, Any]:
    """Return a success result."""
    return {"success": True, "data": data}


def _err(message: str, status_code: int | None = None) -> dict[str, Any]:
    """Return an error result with a human-readable message."""
    return {"success": False, "error": message, "status_code": status_code}


def _human_error(response: httpx.Response) -> str:
    """Extract a human-readable error from an HTTP response.

    v0.4.0 (Q / audit D-#2): the previous bare ``except Exception: pass``
    silently swallowed both "body isn't JSON" and "JSON has wrong shape".
    Both fall back to the status message — but we LOG which path was
    taken so an operator can distinguish a non-JSON 502 (gateway dropped
    the body) from a JSON 500 with no ``detail`` field (handler bug).
    """
    import json as _json

    try:
        body = response.json()
    except _json.JSONDecodeError:
        # Server returned non-JSON (e.g. an HTML 502 from a proxy). Log
        # at debug because this is a normal failure mode in dev.
        _LOGGER.debug(
            "non-JSON response body status=%d url=%s",
            response.status_code,
            response.request.url if response.request else "?",
        )
        return _STATUS_MESSAGES.get(response.status_code, f"HTTP {response.status_code}")
    except Exception:  # truly unexpected
        _LOGGER.warning(
            "unexpected error parsing response body status=%d",
            response.status_code,
            exc_info=True,
        )
        return _STATUS_MESSAGES.get(response.status_code, f"HTTP {response.status_code}")

    if isinstance(body, dict):
        detail = body.get("detail", "")
        if detail:
            return str(detail)
    return _STATUS_MESSAGES.get(response.status_code, f"HTTP {response.status_code}")


# ---------------------------------------------------------------------------
# Core request function with retry
# ---------------------------------------------------------------------------


def _request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Send an HTTP request with retry logic.

    Returns a Result dict: ``{"success": True, "data": ...}`` on success,
    ``{"success": False, "error": "...", "status_code": ...}`` on failure.
    """
    url = f"{_base_url()}{path}"
    last_error: str = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.request(method, url, json=json, params=params)

            if response.is_success:
                # 204 No Content has no body
                if response.status_code == 204:
                    return _ok(None)
                return _ok(response.json())

            # Non-retryable client errors (4xx)
            if 400 <= response.status_code < 500:
                return _err(_human_error(response), response.status_code)

            # Server errors (5xx) — retry
            last_error = _human_error(response)

        except httpx.ConnectError:
            last_error = f"Verbindung zu {_base_url()} fehlgeschlagen. Laeuft der NomOS Server?"
        except httpx.TimeoutException:
            last_error = f"Timeout nach {timeout}s — Server antwortet nicht."
        except httpx.HTTPError as exc:
            last_error = f"HTTP Fehler: {exc}"

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return _err(last_error)


# ---------------------------------------------------------------------------
# Agent lifecycle
# ---------------------------------------------------------------------------


def pause_agent(agent_id: str) -> dict[str, Any]:
    """POST /api/agents/{agent_id}/pause"""
    return _request("POST", f"/api/agents/{agent_id}/pause")


def resume_agent(agent_id: str) -> dict[str, Any]:
    """POST /api/agents/{agent_id}/resume"""
    return _request("POST", f"/api/agents/{agent_id}/resume")


def retire_agent(agent_id: str) -> dict[str, Any]:
    """POST /api/agents/{agent_id}/retire"""
    return _request("POST", f"/api/agents/{agent_id}/retire")


# ---------------------------------------------------------------------------
# DSGVO
# ---------------------------------------------------------------------------


def forget_email(email: str) -> dict[str, Any]:
    """POST /api/dsgvo/forget — Art. 17 DSGVO right to be forgotten."""
    return _request("POST", "/api/dsgvo/forget", json={"email": email})


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


def create_task(
    agent_id: str,
    description: str,
    priority: str = "normal",
    timeout_minutes: int = 60,
) -> dict[str, Any]:
    """POST /api/tasks — create and assign a task to an agent."""
    return _request(
        "POST",
        "/api/tasks",
        json={
            "agent_id": agent_id,
            "description": description,
            "priority": priority,
            "timeout_minutes": timeout_minutes,
        },
    )


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------


def get_costs() -> dict[str, Any]:
    """GET /api/costs — cost overview across all agents."""
    return _request("GET", "/api/costs")


def get_agent_costs(agent_id: str) -> dict[str, Any]:
    """GET /api/costs/{agent_id} — cost details for a single agent."""
    return _request("GET", f"/api/costs/{agent_id}")


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


def get_incidents() -> dict[str, Any]:
    """GET /api/incidents — list all incidents."""
    return _request("GET", "/api/incidents")


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


def mount_collection(agent_id: str, collection_name: str) -> dict[str, Any]:
    """POST /api/workspace/mount — mount a collection to an agent workspace."""
    return _request(
        "POST",
        "/api/workspace/mount",
        json={"agent_id": agent_id, "collection_name": collection_name},
    )


def unmount_collection(agent_id: str, collection_name: str) -> dict[str, Any]:
    """POST /api/workspace/unmount — unmount a collection from an agent workspace."""
    return _request(
        "POST",
        "/api/workspace/unmount",
        json={"agent_id": agent_id, "collection_name": collection_name},
    )
