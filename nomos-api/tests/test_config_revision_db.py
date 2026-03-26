"""Tests for the config revision service — DB-backed via async session."""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.config_revision import (
    get_latest,
    list_revisions,
    rollback,
    save_revision,
)


async def test_save_and_get_latest(db_session: AsyncSession) -> None:
    rev = await save_revision(
        db_session,
        agent_id="agent-1",
        config_json={"model": "claude-sonnet", "budget": 50},
        change_description="initial config",
        created_by="admin",
    )
    assert rev.version == 1
    assert rev.agent_id == "agent-1"
    assert rev.change_description == "initial config"
    assert rev.created_by == "admin"
    assert json.loads(rev.config_json) == {"model": "claude-sonnet", "budget": 50}

    latest = await get_latest(db_session, "agent-1")
    assert latest is not None
    assert latest.id == rev.id
    assert latest.version == 1


async def test_multiple_revisions_increment_version(db_session: AsyncSession) -> None:
    await save_revision(db_session, "agent-1", {"model": "sonnet"}, "v1")
    await save_revision(db_session, "agent-1", {"model": "opus"}, "v2")
    rev3 = await save_revision(db_session, "agent-1", {"model": "haiku"}, "v3")

    assert rev3.version == 3

    latest = await get_latest(db_session, "agent-1")
    assert latest is not None
    assert latest.version == 3
    assert json.loads(latest.config_json) == {"model": "haiku"}


async def test_rollback(db_session: AsyncSession) -> None:
    await save_revision(db_session, "agent-1", {"model": "sonnet", "budget": 50}, "v1")
    await save_revision(db_session, "agent-1", {"model": "opus", "budget": 100}, "v2")

    rev = await rollback(db_session, "agent-1", version=1)
    assert rev is not None
    config = json.loads(rev.config_json)
    assert config["model"] == "sonnet"
    assert config["budget"] == 50


async def test_rollback_nonexistent_returns_none(db_session: AsyncSession) -> None:
    await save_revision(db_session, "agent-1", {"model": "sonnet"}, "v1")
    result = await rollback(db_session, "agent-1", version=99)
    assert result is None


async def test_rollback_unknown_agent_returns_none(db_session: AsyncSession) -> None:
    result = await rollback(db_session, "unknown-agent", version=1)
    assert result is None


async def test_list_revisions(db_session: AsyncSession) -> None:
    await save_revision(db_session, "agent-1", {"model": "sonnet"}, "v1")
    await save_revision(db_session, "agent-1", {"model": "opus"}, "v2")
    await save_revision(db_session, "agent-2", {"model": "haiku"}, "v1")

    revs = await list_revisions(db_session, "agent-1")
    assert len(revs) == 2
    assert revs[0].version == 1
    assert revs[1].version == 2

    revs2 = await list_revisions(db_session, "agent-2")
    assert len(revs2) == 1


async def test_list_revisions_empty(db_session: AsyncSession) -> None:
    revs = await list_revisions(db_session, "unknown")
    assert revs == []


async def test_get_latest_unknown(db_session: AsyncSession) -> None:
    result = await get_latest(db_session, "unknown")
    assert result is None
