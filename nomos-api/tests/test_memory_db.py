"""Tests for DB-backed agent memory service."""

from __future__ import annotations

import pytest

from nomos_api.services.memory import (
    delete_by_agent,
    delete_by_content,
    list_messages,
    search_messages,
    store_message,
)


@pytest.mark.asyncio
async def test_store_and_retrieve(db_session):
    """Store 2 messages, list them, verify count and content."""
    await store_message(db_session, "agent-1", "sess-1", "user", "Hello agent")
    await store_message(db_session, "agent-1", "sess-1", "assistant", "Hello user")

    msgs = await list_messages(db_session, "agent-1", "sess-1")

    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "Hello agent"
    assert msgs[1].role == "assistant"
    assert msgs[1].content == "Hello user"


@pytest.mark.asyncio
async def test_delete_by_agent(db_session):
    """Store messages, delete by agent, verify empty."""
    await store_message(db_session, "agent-x", "sess-1", "user", "msg1")
    await store_message(db_session, "agent-x", "sess-2", "user", "msg2")

    deleted = await delete_by_agent(db_session, "agent-x")

    assert deleted == 2
    assert await list_messages(db_session, "agent-x", "sess-1") == []
    assert await list_messages(db_session, "agent-x", "sess-2") == []


@pytest.mark.asyncio
async def test_delete_by_content(db_session):
    """Store 2 messages (one with PII), delete by content, only PII deleted."""
    await store_message(db_session, "agent-1", "sess-1", "user", "My email is max@example.com")
    await store_message(db_session, "agent-1", "sess-1", "assistant", "Hello Max!")

    deleted = await delete_by_content(db_session, "max@example.com")

    assert deleted == 1
    remaining = await list_messages(db_session, "agent-1", "sess-1")
    assert len(remaining) == 1
    assert remaining[0].content == "Hello Max!"


@pytest.mark.asyncio
async def test_search_messages(db_session):
    """Store messages, search by term, find correct ones."""
    await store_message(db_session, "agent-1", "sess-1", "user", "I need help with billing")
    await store_message(db_session, "agent-1", "sess-1", "assistant", "Sure, let me check")
    await store_message(db_session, "agent-2", "sess-2", "user", "Billing question here too")

    results = await search_messages(db_session, "billing")

    # SQLite LIKE is case-insensitive for ASCII, so both "billing" and "Billing" match
    assert len(results) == 2
    contents = {r.content for r in results}
    assert "I need help with billing" in contents
    assert "Billing question here too" in contents

    # Negative search returns nothing
    empty = await search_messages(db_session, "nonexistent-term")
    assert empty == []


@pytest.mark.asyncio
async def test_isolation(db_session):
    """Messages from agent-1 must not appear in agent-2 queries."""
    await store_message(db_session, "agent-1", "sess-a", "user", "Secret for agent-1")
    await store_message(db_session, "agent-2", "sess-b", "user", "Secret for agent-2")

    msgs_1 = await list_messages(db_session, "agent-1", "sess-a")
    msgs_2 = await list_messages(db_session, "agent-2", "sess-b")

    assert len(msgs_1) == 1
    assert msgs_1[0].content == "Secret for agent-1"
    assert len(msgs_2) == 1
    assert msgs_2[0].content == "Secret for agent-2"

    # Cross-check: agent-1 sees nothing in sess-b
    cross = await list_messages(db_session, "agent-1", "sess-b")
    assert cross == []
