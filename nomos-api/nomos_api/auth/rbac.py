"""Role-based access control for agent operations."""

from __future__ import annotations

from typing import Protocol

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class _HasEmailRole(Protocol):
    email: str
    role: str


class _HasEmailId(Protocol):
    id: str
    email: str


def check_agent_access(user: _HasEmailRole, agent: _HasEmailId, action: str) -> None:
    """Verify that *user* is allowed to perform *action* on *agent*.

    Rules:
    - Admin can act on any agent.
    - Non-admin users can only act on agents whose email matches their own.
    """
    if user.role == "admin":
        return
    if agent.email == user.email:
        return
    raise HTTPException(
        status_code=403,
        detail=f"Not authorized to {action} agent {agent.id}",
    )


def _get_db_dep():
    """Indirection so FastAPI resolves get_db (honoring dependency_overrides)."""
    from nomos_api.database import get_db

    return get_db


async def require_admin(
    nomos_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(_get_db_dep()),
):
    """FastAPI dependency: require an authenticated, active admin user.

    Same DB-backed JWT-cookie scheme used by the users/settings admin
    endpoints (decode cookie -> load active User -> assert role == 'admin').
    Centralized here so admin-only routers (monitoring, ...) share one
    implementation instead of re-inventing per-router checks.
    """
    from nomos_api.auth.jwt import decode_token
    from nomos_api.config import settings
    from nomos_api.models import User

    if not nomos_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(nomos_token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(
        select(User).where(User.id == payload.user_id, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def authorize_agent_action(
    *,
    db: AsyncSession,
    request: Request,
    agent_id: str,
    action: str,
    allow_missing: bool = False,
):
    """Body-AuthZ analogue of require_agent_actor — used where agent_id
    comes from the JSON body, not a path parameter.

    Verifies that ``request.state.user`` (set by AuthMiddleware) is allowed
    to perform *action* on *agent_id*. Returns the loaded ``Agent`` so the
    caller can re-use it. Same semantics as :func:`require_agent_actor`:
    service principal -> trusted; user principal -> must own the agent or
    be admin.

    Use this from any handler that takes ``agent_id`` inside a Pydantic
    request body (tasks, workspace, budget, costs, compliance alias, ...).
    Path-param endpoints should keep using :func:`require_agent_actor`.

    ``allow_missing=True``: for endpoints where the existing fail-closed
    contract is "unknown agent returns a restrictive payload, not 404"
    (notably budget_check and budget_track — the OpenClaw plugin probes
    these for agents it cannot pre-register). With this flag, an unknown
    agent yields ``None`` instead of raising 404; the handler then runs
    its own fail-closed branch. AuthZ for known agents still applies.

    Raises 401/403 (and 404 unless ``allow_missing=True``) with the same
    shape as :func:`require_agent_actor`.
    """
    from nomos_api.models import Agent

    principal = getattr(request.state, "user", None)
    if not principal:
        raise HTTPException(status_code=401, detail="Not authenticated")

    agent = await db.get(Agent, agent_id)
    if agent is None:
        if allow_missing:
            return None
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    role = principal.get("role")
    if role == "service":
        return agent

    email = principal.get("email")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid principal")

    class _P:
        pass

    actor = _P()
    actor.role = role or "user"
    actor.email = email
    check_agent_access(actor, agent, action)
    return agent


async def require_agent_actor(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(_get_db_dep()),
):
    """Authorize the caller to act on *agent_id*.

    The global AuthMiddleware already authenticates every non-public request
    (plugin `X-NomOS-API-Key` -> service principal, or `nomos_token` JWT ->
    user principal) and stores it on `request.state.user`. This dependency
    closes the route-level gap (H3): it requires that principal AND, for
    non-service users, verifies agent ownership via check_agent_access.

    - Plugin/service principal: trusted infra — may heartbeat any agent.
    - User principal: must own the agent (or be admin).
    Returns the loaded Agent so the handler need not re-query.
    """
    from nomos_api.models import Agent

    principal = getattr(request.state, "user", None)
    if not principal:
        # Defense in depth — should already be enforced by AuthMiddleware.
        raise HTTPException(status_code=401, detail="Not authenticated")

    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    role = principal.get("role")
    if role == "service":
        return agent

    email = principal.get("email")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid principal")

    class _P:
        pass

    actor = _P()
    actor.role = role or "user"
    actor.email = email
    check_agent_access(actor, agent, "heartbeat")
    return agent
