"""Honcho API client — in-memory implementation.

Provides the same interface as the Honcho REST API for workspace, session,
and message management. Uses in-memory dicts for storage. When a real Honcho
instance is available, the HTTP calls can be wired in behind the same interface.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class HonchoClient:
    """In-memory Honcho-compatible client for workspace/session/message CRUD."""

    base_url: str
    _workspaces: dict = field(default_factory=dict)
    _sessions: dict = field(default_factory=dict)
    _messages: dict = field(default_factory=dict)

    def create_workspace(self, name: str) -> dict:
        """Create a new workspace and return its metadata."""
        ws_id = f"ws-{uuid.uuid4().hex[:8]}"
        self._workspaces[ws_id] = {"id": ws_id, "name": name, "collections": []}
        return self._workspaces[ws_id]

    def get_workspace(self, workspace_id: str) -> dict | None:
        """Return workspace by ID or None if not found."""
        return self._workspaces.get(workspace_id)

    def create_session(self, workspace_id: str, agent_id: str) -> dict:
        """Create a new session within a workspace for a given agent."""
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        session = {
            "id": session_id,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "messages": [],
        }
        self._sessions[session_id] = session
        return session

    def add_message(self, session_id: str, role: str, content: str) -> dict:
        """Add a message to a session. Also stored in flat message index."""
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        msg = {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
        }
        if session_id in self._sessions:
            self._sessions[session_id]["messages"].append(msg)
        self._messages[msg_id] = msg
        return msg

    def list_sessions(self, workspace_id: str) -> list[dict]:
        """List all sessions belonging to a workspace."""
        return [
            s for s in self._sessions.values() if s["workspace_id"] == workspace_id
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID. Returns True if found and deleted."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def delete_messages_by_content(self, search_term: str) -> int:
        """Delete all messages containing search_term (for DSGVO Art. 17 forget).

        Returns the number of deleted messages.
        """
        to_delete = [
            mid
            for mid, msg in self._messages.items()
            if search_term in msg["content"]
        ]
        for mid in to_delete:
            del self._messages[mid]
        return len(to_delete)
