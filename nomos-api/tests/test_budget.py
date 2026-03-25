"""Tests for the BudgetService — in-memory budget tracking and enforcement."""

from __future__ import annotations

import pytest

from nomos_api.services.budget import BudgetService


def test_check_within_budget():
    svc = BudgetService()
    result = svc.check("agent-1", current=30.0, limit=50.0, warn_at=80)
    assert result["allowed"] is True
    assert result["status"] == "normal"


def test_check_warning_threshold():
    svc = BudgetService()
    result = svc.check("agent-1", current=42.0, limit=50.0, warn_at=80)
    assert result["allowed"] is True
    assert result["status"] == "warning"


def test_check_exceeded():
    svc = BudgetService()
    result = svc.check("agent-1", current=51.0, limit=50.0, warn_at=80)
    assert result["allowed"] is False
    assert result["status"] == "exceeded"


def test_check_at_exact_limit():
    svc = BudgetService()
    result = svc.check("agent-1", current=50.0, limit=50.0, warn_at=80)
    assert result["allowed"] is False
    assert result["status"] == "exceeded"


def test_check_at_exact_warning():
    svc = BudgetService()
    result = svc.check("agent-1", current=40.0, limit=50.0, warn_at=80)
    assert result["allowed"] is True
    assert result["status"] == "warning"


def test_track_cost():
    svc = BudgetService()
    svc.track("agent-1", cost=0.05)
    svc.track("agent-1", cost=0.03)
    assert svc.get_total("agent-1") == pytest.approx(0.08)


def test_track_cost_multiple_agents():
    svc = BudgetService()
    svc.track("agent-1", cost=1.0)
    svc.track("agent-2", cost=2.0)
    assert svc.get_total("agent-1") == pytest.approx(1.0)
    assert svc.get_total("agent-2") == pytest.approx(2.0)


def test_get_total_unknown_agent():
    svc = BudgetService()
    assert svc.get_total("unknown") == pytest.approx(0.0)


def test_check_includes_percent_used():
    svc = BudgetService()
    result = svc.check("agent-1", current=25.0, limit=50.0, warn_at=80)
    assert result["percent_used"] == pytest.approx(50.0)
