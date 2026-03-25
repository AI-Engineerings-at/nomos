"""Tests for FCL (Fair Core License) enforcement — max 3 agents free."""

from __future__ import annotations

from nomos_api.services.agent_service import check_fcl_limit, check_fcl_limit_with_message


def test_allows_up_to_3_agents():
    assert check_fcl_limit(active_count=0) is True
    assert check_fcl_limit(active_count=1) is True
    assert check_fcl_limit(active_count=2) is True


def test_blocks_4th_agent():
    assert check_fcl_limit(active_count=3) is False


def test_blocks_beyond_4th():
    assert check_fcl_limit(active_count=10) is False


def test_returns_message_allowed():
    allowed, msg = check_fcl_limit_with_message(active_count=2)
    assert allowed is True
    assert "2/3" in msg


def test_returns_message_blocked():
    allowed, msg = check_fcl_limit_with_message(active_count=3)
    assert allowed is False
    assert "3/3" in msg
    assert "license" in msg.lower() or "Lizenz" in msg
