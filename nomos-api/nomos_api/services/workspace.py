"""Workspace service — isolation, mount/unmount, and agent retirement.

Enforces that each agent can only read/write its own workspace.
The company workspace is read-only for all agents.
Collections can be mounted/unmounted per agent workspace.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nomos_api.services.honcho import HonchoClient

COMPANY_WORKSPACE_NAME = "company"


@dataclass
class WorkspaceService:
    """Manages workspace isolation, collection mounting, and agent retirement."""

    client: HonchoClient
    _agent_workspaces: dict[str, str] = field(default_factory=dict)
    _mounted_collections: dict[str, list[str]] = field(default_factory=dict)
    _retired_agents: set[str] = field(default_factory=set)
    _company_workspace_id: str | None = field(default=None)

    def create_agent_workspace(self, agent_id: str) -> dict:
        """Create an isolated workspace for an agent."""
        ws = self.client.create_workspace(agent_id)
        self._agent_workspaces[agent_id] = ws["id"]
        self._mounted_collections[agent_id] = []
        return ws

    def create_company_workspace(self) -> dict:
        """Create the shared company workspace (read-only for all agents)."""
        ws = self.client.create_workspace(COMPANY_WORKSPACE_NAME)
        self._company_workspace_id = ws["id"]
        return ws

    def can_access(self, agent_id: str, workspace_name: str, operation: str) -> bool:
        """Check if agent_id can perform operation on workspace_name.

        Rules:
        - Retired agents have no access to anything.
        - Company workspace: read-only for all agents, no writes.
        - Agent workspace: full read/write only for the owning agent.
        - Cross-agent access is denied.
        """
        if agent_id in self._retired_agents:
            return False

        if workspace_name == COMPANY_WORKSPACE_NAME:
            if self._company_workspace_id is None:
                return False
            return operation == "read"

        if workspace_name == agent_id and agent_id in self._agent_workspaces:
            return operation in ("read", "write")

        return False

    def mount_collection(self, agent_id: str, collection_name: str) -> bool:
        """Mount a collection into an agent's workspace. Idempotent."""
        if agent_id not in self._mounted_collections:
            return False
        if collection_name not in self._mounted_collections[agent_id]:
            self._mounted_collections[agent_id].append(collection_name)
        return True

    def unmount_collection(self, agent_id: str, collection_name: str) -> bool:
        """Unmount a collection from an agent's workspace."""
        if agent_id not in self._mounted_collections:
            return False
        if collection_name not in self._mounted_collections[agent_id]:
            return False
        self._mounted_collections[agent_id].remove(collection_name)
        return True

    def get_mounted_collections(self, agent_id: str) -> list[str]:
        """Return list of mounted collection names for an agent."""
        if agent_id in self._retired_agents:
            return []
        return list(self._mounted_collections.get(agent_id, []))

    def retire_agent(self, agent_id: str) -> None:
        """Retire an agent — revoke all access and unmount all collections."""
        self._retired_agents.add(agent_id)
        if agent_id in self._mounted_collections:
            self._mounted_collections[agent_id] = []
