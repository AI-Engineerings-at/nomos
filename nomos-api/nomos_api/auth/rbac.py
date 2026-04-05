"""Role-based access control for agent operations."""

from __future__ import annotations

from typing import Protocol

from fastapi import HTTPException


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
