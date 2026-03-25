"""Tests for the ApprovalService — in-memory approval queue."""

from __future__ import annotations

import pytest

from nomos_api.services.approval import ApprovalService


def test_request_approval():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="external_api_call", description="Call CRM API")
    assert req["status"] == "pending"
    assert req["agent_id"] == "agent-1"
    assert req["action"] == "external_api_call"
    assert "id" in req


def test_approve():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="file_deletion", description="Delete temp.txt")
    svc.resolve(req["id"], "approved", resolved_by="admin@nomos.local")
    result = svc.get(req["id"])
    assert result["status"] == "approved"
    assert result["resolved_by"] == "admin@nomos.local"
    assert result["resolved_at"] is not None


def test_deny():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="data_export", description="Export CSV")
    svc.resolve(req["id"], "denied", resolved_by="admin@nomos.local")
    assert svc.get(req["id"])["status"] == "denied"


def test_list_pending():
    svc = ApprovalService()
    svc.request(agent_id="agent-1", action="api_call", description="A")
    svc.request(agent_id="agent-2", action="export", description="B")
    pending = svc.list_pending()
    assert len(pending) == 2


def test_list_pending_excludes_resolved():
    svc = ApprovalService()
    req1 = svc.request(agent_id="agent-1", action="api_call", description="A")
    svc.request(agent_id="agent-2", action="export", description="B")
    svc.resolve(req1["id"], "approved", resolved_by="admin@nomos.local")
    pending = svc.list_pending()
    assert len(pending) == 1


def test_get_unknown_approval():
    svc = ApprovalService()
    with pytest.raises(KeyError):
        svc.get("nonexistent")


def test_resolve_unknown_approval():
    svc = ApprovalService()
    with pytest.raises(KeyError):
        svc.resolve("nonexistent", "approved", resolved_by="admin")


def test_invalid_resolution():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="test", description="Test")
    with pytest.raises(ValueError, match="Invalid"):
        svc.resolve(req["id"], "maybe", resolved_by="admin")


def test_list_by_agent():
    svc = ApprovalService()
    svc.request(agent_id="agent-1", action="a", description="A")
    svc.request(agent_id="agent-2", action="b", description="B")
    svc.request(agent_id="agent-1", action="c", description="C")
    result = svc.list_by_agent("agent-1")
    assert len(result) == 2
