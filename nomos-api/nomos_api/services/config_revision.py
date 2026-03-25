"""Config revision service — versioned snapshots of agent configurations.

Supports saving new revisions, listing history, retrieving the latest,
and rolling back to a specific version.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone


class ConfigRevisionService:
    """In-memory config revision tracker with versioning and rollback."""

    def __init__(self) -> None:
        # agent_id -> list of revisions (ordered by version)
        self._revisions: dict[str, list[dict]] = {}

    def save(
        self,
        agent_id: str,
        config: dict,
        change_description: str,
        created_by: str | None = None,
    ) -> dict:
        """Save a new config revision. Auto-increments version number."""
        if agent_id not in self._revisions:
            self._revisions[agent_id] = []

        revs = self._revisions[agent_id]
        version = len(revs) + 1
        now = datetime.now(timezone.utc).isoformat()

        revision = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "version": version,
            "config_json": json.dumps(config),
            "change_description": change_description,
            "created_by": created_by,
            "created_at": now,
        }
        revs.append(revision)
        return dict(revision)

    def list(self, agent_id: str) -> list[dict]:
        """List all revisions for an agent, ordered by version."""
        return [dict(r) for r in self._revisions.get(agent_id, [])]

    def get_latest(self, agent_id: str) -> dict | None:
        """Get the latest revision for an agent, or None if no revisions exist."""
        revs = self._revisions.get(agent_id, [])
        if not revs:
            return None
        return dict(revs[-1])

    def rollback(self, agent_id: str, version: int) -> dict:
        """Retrieve the config from a specific version.

        Returns the parsed config dict (not the revision metadata).

        Raises:
            KeyError: If agent_id or version not found.
        """
        revs = self._revisions.get(agent_id, [])
        if not revs:
            raise KeyError(f"No revisions found for agent {agent_id!r}")

        for rev in revs:
            if rev["version"] == version:
                return json.loads(rev["config_json"])

        raise KeyError(f"Version {version} not found for agent {agent_id!r}")
