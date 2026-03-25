"""Tests for the ConfigRevisionService — in-memory config versioning."""

from __future__ import annotations

import pytest

from nomos_api.services.config_revision import ConfigRevisionService


def test_save_revision():
    svc = ConfigRevisionService()
    rev = svc.save("agent-1", {"model": "claude-sonnet", "budget": 50}, "created")
    assert rev["version"] == 1
    assert rev["agent_id"] == "agent-1"
    assert rev["change_description"] == "created"


def test_multiple_revisions():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "claude-sonnet"}, "created")
    svc.save("agent-1", {"model": "claude-opus"}, "model changed")
    revs = svc.list("agent-1")
    assert len(revs) == 2
    assert revs[0]["version"] == 1
    assert revs[1]["version"] == 2


def test_rollback():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "sonnet", "budget": 50}, "v1")
    svc.save("agent-1", {"model": "opus", "budget": 100}, "v2")
    config = svc.rollback("agent-1", version=1)
    assert config["model"] == "sonnet"
    assert config["budget"] == 50


def test_rollback_nonexistent_version():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "sonnet"}, "v1")
    with pytest.raises(KeyError):
        svc.rollback("agent-1", version=99)


def test_rollback_unknown_agent():
    svc = ConfigRevisionService()
    with pytest.raises(KeyError):
        svc.rollback("unknown", version=1)


def test_list_empty():
    svc = ConfigRevisionService()
    assert svc.list("unknown") == []


def test_get_latest():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "sonnet"}, "v1")
    svc.save("agent-1", {"model": "opus"}, "v2")
    latest = svc.get_latest("agent-1")
    assert latest is not None
    assert latest["version"] == 2


def test_get_latest_unknown():
    svc = ConfigRevisionService()
    assert svc.get_latest("unknown") is None


def test_independent_agents():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "sonnet"}, "v1")
    svc.save("agent-2", {"model": "opus"}, "v1")
    assert len(svc.list("agent-1")) == 1
    assert len(svc.list("agent-2")) == 1
