"""Tests for Control Plane event types added to EventType enum."""

from __future__ import annotations

from nomos.core.events import EventType


def test_task_events_exist():
    assert hasattr(EventType, "TASK_CREATED")
    assert hasattr(EventType, "TASK_ASSIGNED")
    assert hasattr(EventType, "TASK_COMPLETED")


def test_budget_events_exist():
    assert hasattr(EventType, "BUDGET_WARNING")
    assert hasattr(EventType, "BUDGET_EXCEEDED")


def test_approval_events_exist():
    assert hasattr(EventType, "APPROVAL_REQUESTED")
    assert hasattr(EventType, "APPROVAL_GRANTED")
    assert hasattr(EventType, "APPROVAL_DENIED")


def test_config_events_exist():
    assert hasattr(EventType, "CONFIG_CHANGED")
    assert hasattr(EventType, "CONFIG_ROLLED_BACK")


def test_task_event_values():
    assert EventType.TASK_CREATED.value == "task.created"
    assert EventType.TASK_ASSIGNED.value == "task.assigned"
    assert EventType.TASK_COMPLETED.value == "task.completed"


def test_budget_event_values():
    assert EventType.BUDGET_WARNING.value == "budget.warning"
    assert EventType.BUDGET_EXCEEDED.value == "budget.exceeded"


def test_approval_event_values():
    assert EventType.APPROVAL_REQUESTED.value == "approval.requested"
    assert EventType.APPROVAL_GRANTED.value == "approval.granted"
    assert EventType.APPROVAL_DENIED.value == "approval.denied"


def test_config_event_values():
    assert EventType.CONFIG_CHANGED.value == "config.changed"
    assert EventType.CONFIG_ROLLED_BACK.value == "config.rolled_back"
