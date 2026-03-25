"""Approval service — manages approval queue for gated agent actions.

Actions that require human sign-off (e.g. external API calls, file deletion,
data export) are submitted as approval requests and must be explicitly
approved or denied before the agent can proceed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


_VALID_RESOLUTIONS = {"approved", "denied"}


class ApprovalService:
    """In-memory approval queue for gated agent actions."""

    def __init__(self) -> None:
        self._approvals: dict[str, dict] = {}

    def request(
        self,
        agent_id: str,
        action: str,
        description: str,
        timeout_minutes: int = 60,
    ) -> dict:
        """Submit an approval request. Returns the request in 'pending' status."""
        approval_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        approval = {
            "id": approval_id,
            "agent_id": agent_id,
            "action": action,
            "description": description,
            "status": "pending",
            "requested_at": now,
            "resolved_at": None,
            "resolved_by": None,
            "timeout_minutes": timeout_minutes,
        }
        self._approvals[approval_id] = approval
        return dict(approval)

    def resolve(self, approval_id: str, resolution: str, resolved_by: str) -> dict:
        """Approve or deny a pending request.

        Args:
            approval_id: The approval request ID.
            resolution: Must be 'approved' or 'denied'.
            resolved_by: Identifier of the person resolving.

        Raises:
            KeyError: If approval_id not found.
            ValueError: If resolution is not 'approved' or 'denied'.
        """
        if approval_id not in self._approvals:
            raise KeyError(f"Approval {approval_id!r} not found")

        if resolution not in _VALID_RESOLUTIONS:
            raise ValueError(
                f"Invalid resolution: {resolution!r}. Must be one of {sorted(_VALID_RESOLUTIONS)}"
            )

        approval = self._approvals[approval_id]
        approval["status"] = resolution
        approval["resolved_by"] = resolved_by
        approval["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return dict(approval)

    def get(self, approval_id: str) -> dict:
        """Get an approval by ID. Raises KeyError if not found."""
        if approval_id not in self._approvals:
            raise KeyError(f"Approval {approval_id!r} not found")
        return dict(self._approvals[approval_id])

    def list_pending(self) -> list[dict]:
        """List all pending approval requests."""
        return [dict(a) for a in self._approvals.values() if a["status"] == "pending"]

    def list_by_agent(self, agent_id: str) -> list[dict]:
        """List all approvals for a specific agent."""
        return [dict(a) for a in self._approvals.values() if a["agent_id"] == agent_id]
