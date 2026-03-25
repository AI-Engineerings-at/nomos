"""Tests for the HeartbeatService — in-memory heartbeat tracking."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from nomos_api.services.heartbeat import HeartbeatService


def test_record_heartbeat():
    svc = HeartbeatService()
    svc.record("agent-1", {"tokens_used": 100, "memory_mb": 256})
    assert svc.get_status("agent-1") == "online"


def test_stale_after_5_minutes():
    svc = HeartbeatService()
    svc.record("agent-1", {})
    svc._last_seen["agent-1"] = datetime.now(timezone.utc) - timedelta(minutes=6)
    assert svc.get_status("agent-1") == "stale"


def test_offline_after_10_minutes():
    svc = HeartbeatService()
    svc.record("agent-1", {})
    svc._last_seen["agent-1"] = datetime.now(timezone.utc) - timedelta(minutes=11)
    assert svc.get_status("agent-1") == "offline"


def test_unknown_agent():
    svc = HeartbeatService()
    assert svc.get_status("unknown") == "offline"


def test_metrics_stored():
    svc = HeartbeatService()
    svc.record("agent-1", {"tokens_used": 100})
    metrics = svc.get_metrics("agent-1")
    assert metrics is not None
    assert metrics["tokens_used"] == 100


def test_metrics_unknown_agent():
    svc = HeartbeatService()
    assert svc.get_metrics("unknown") is None


def test_multiple_agents():
    svc = HeartbeatService()
    svc.record("agent-1", {})
    svc.record("agent-2", {})
    assert svc.get_status("agent-1") == "online"
    assert svc.get_status("agent-2") == "online"
    all_statuses = svc.get_all_statuses()
    assert len(all_statuses) == 2
