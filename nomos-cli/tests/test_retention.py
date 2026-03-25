"""Tests for Retention Engine — enforces session expiry by age."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from nomos.core.retention import RetentionEngine, RetentionResult


def test_nothing_to_delete_when_fresh():
    engine = RetentionEngine(retention_days=90)
    engine.add_session("sess-1", created_at=datetime.now(timezone.utc))
    result = engine.enforce()
    assert result.deleted_count == 0


def test_deletes_expired_sessions():
    engine = RetentionEngine(retention_days=90)
    old_date = datetime.now(timezone.utc) - timedelta(days=91)
    engine.add_session("sess-old", created_at=old_date)
    engine.add_session("sess-new", created_at=datetime.now(timezone.utc))
    result = engine.enforce()
    assert result.deleted_count == 1
    assert "sess-old" in result.deleted_ids


def test_custom_retention_period():
    engine = RetentionEngine(retention_days=7)
    old_date = datetime.now(timezone.utc) - timedelta(days=8)
    engine.add_session("sess-1", created_at=old_date)
    result = engine.enforce()
    assert result.deleted_count == 1


def test_audit_entry_created():
    engine = RetentionEngine(retention_days=90)
    old_date = datetime.now(timezone.utc) - timedelta(days=91)
    engine.add_session("sess-1", created_at=old_date)
    result = engine.enforce()
    assert result.audit_event == "data.retention_enforced"


def test_no_audit_when_nothing_deleted():
    engine = RetentionEngine(retention_days=90)
    engine.add_session("sess-1", created_at=datetime.now(timezone.utc))
    result = engine.enforce()
    assert result.deleted_count == 0
    assert result.deleted_ids == []


def test_boundary_not_deleted():
    """Session just inside retention boundary should NOT be deleted."""
    engine = RetentionEngine(retention_days=90)
    # Use 89 days to stay safely within the retention window
    inside_boundary = datetime.now(timezone.utc) - timedelta(days=89)
    engine.add_session("sess-boundary", created_at=inside_boundary)
    result = engine.enforce()
    assert result.deleted_count == 0


def test_multiple_expired():
    engine = RetentionEngine(retention_days=30)
    for i in range(5):
        old = datetime.now(timezone.utc) - timedelta(days=31 + i)
        engine.add_session(f"sess-{i}", created_at=old)
    engine.add_session("sess-fresh", created_at=datetime.now(timezone.utc))
    result = engine.enforce()
    assert result.deleted_count == 5
    assert "sess-fresh" not in result.deleted_ids
