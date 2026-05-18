"""Tests for context pipeline service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.context_pipeline import ContextPipeline, ContextManager
from nomos_api.models import AgentMemory


@pytest.mark.asyncio
async def test_process_new_message():
    """Test processing a new message through the pipeline."""
    # Create mock database session
    db = MagicMock(spec=AsyncSession)

    # Mock the store_message and list_messages functions
    mock_store = AsyncMock()
    mock_list = AsyncMock()

    # Import and patch the functions
    import nomos_api.services.memory as memory_module

    memory_module.store_message = mock_store
    memory_module.list_messages = mock_list

    # Create pipeline
    pipeline = ContextPipeline()

    # Mock the summarizer to avoid actual LLM calls
    pipeline.summarizer.summarize = AsyncMock(return_value=None)

    # Set up mock responses
    mock_message = AgentMemory(
        id=1, agent_id="test-agent", session_id="test-session", role="user", content="test", importance_score=1.0
    )
    mock_store.return_value = mock_message
    mock_list.return_value = [mock_message]  # Only one message, so no summary needed

    # Process message
    result = await pipeline.process_new_message(db, "test-agent", "test-session", "user", "Hello world")

    # Verify message was stored
    assert result == mock_message
    mock_store.assert_awaited_once()


@pytest.mark.asyncio
async def test_context_management_trigger():
    """Test that context management is triggered after threshold."""
    db = MagicMock(spec=AsyncSession)

    # Mock functions
    import nomos_api.services.memory as memory_module

    mock_store = AsyncMock()
    mock_list = AsyncMock()
    memory_module.store_message = mock_store
    memory_module.list_messages = mock_list

    pipeline = ContextPipeline()
    pipeline.summary_threshold = 5  # Lower threshold for testing

    # Mock summarize to return a valid response
    mock_summary_response = MagicMock()
    mock_summary_response.summary = "Summary of conversation"
    mock_summary_response.token_count = 50
    mock_summary_response.original_token_count = 500
    pipeline.summarizer.summarize = AsyncMock(return_value=mock_summary_response)

    # Create mock messages (more than threshold)
    mock_messages = []
    for i in range(10):
        mock_msg = AgentMemory(
            id=i,
            agent_id="test-agent",
            session_id="test-session",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            importance_score=1.0,
        )
        mock_messages.append(mock_msg)

    mock_store.return_value = mock_messages[-1]  # Last message
    mock_list.return_value = mock_messages

    # Process message (should trigger context management)
    await pipeline.process_new_message(db, "test-agent", "test-session", "user", "New message")

    # Verify summarize was called
    pipeline.summarizer.summarize.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_managed_context():
    """Test getting managed context with summaries and recent messages."""
    db = MagicMock(spec=AsyncSession)

    import nomos_api.services.memory as memory_module

    mock_list = AsyncMock()
    memory_module.list_messages = mock_list

    pipeline = ContextPipeline()

    # Create mock messages with summaries
    mock_messages = [
        AgentMemory(
            id=1,
            agent_id="test-agent",
            session_id="test-session",
            role="system",
            content="[SUMMARY]: Old conversation summary",
            importance_score=2.0,
        ),
        AgentMemory(
            id=2,
            agent_id="test-agent",
            session_id="test-session",
            role="user",
            content="Recent message 1",
            importance_score=1.0,
        ),
        AgentMemory(
            id=3,
            agent_id="test-agent",
            session_id="test-session",
            role="assistant",
            content="Recent response 1",
            importance_score=1.0,
        ),
    ]

    mock_list.return_value = mock_messages

    # Get managed context
    context = await pipeline.get_managed_context(db, "test-agent", "test-session")

    # Should have summary first, then recent messages
    assert len(context) == 3
    assert context[0]["content"].startswith("[SUMMARY]")
    assert context[1]["content"] == "Recent message 1"
    assert context[2]["content"] == "Recent response 1"


@pytest.mark.asyncio
async def test_context_stats():
    """Test context statistics calculation."""
    db = MagicMock(spec=AsyncSession)

    import nomos_api.services.memory as memory_module

    mock_list = AsyncMock()
    memory_module.list_messages = mock_list

    pipeline = ContextPipeline()

    # Create mock messages
    mock_messages = [
        AgentMemory(
            id=1,
            agent_id="test-agent",
            session_id="test-session",
            role="system",
            content="[SUMMARY]: Summary",
            importance_score=2.0,
        ),
        AgentMemory(
            id=2, agent_id="test-agent", session_id="test-session", role="user", content="Message", importance_score=1.0
        ),
    ]

    mock_list.return_value = mock_messages

    # Get stats
    stats = await pipeline.get_context_stats(db, "test-agent", "test-session")

    assert stats["agent_id"] == "test-agent"
    assert stats["session_id"] == "test-session"
    assert stats["total_messages"] == 2
    assert stats["summary_count"] == 1
    assert stats["recent_messages"] == 1


@pytest.mark.asyncio
async def test_context_manager_integration():
    """Test full context manager integration."""
    db = MagicMock(spec=AsyncSession)

    # Mock memory functions
    import nomos_api.services.memory as memory_module

    mock_store = AsyncMock()
    mock_list = AsyncMock()
    memory_module.store_message = mock_store
    memory_module.list_messages = mock_list

    manager = ContextManager()

    # Create mock message
    mock_message = AgentMemory(
        id=1, agent_id="test-agent", session_id="test-session", role="user", content="test", importance_score=1.0
    )
    mock_store.return_value = mock_message
    mock_list.return_value = [mock_message]

    # Process message
    result = await manager.process_message(db, "test-agent", "test-session", "user", "Hello")

    assert "message_id" in result
    assert "context_stats" in result
    assert "context_within_limits" in result
    assert result["context_within_limits"] is True


@pytest.mark.asyncio
async def test_prune_old_context():
    """Test pruning old context delegates to memory.prune_messages."""
    db = MagicMock(spec=AsyncSession)

    import nomos_api.services.memory as memory_module

    # prune_old_context now performs real deletion via memory.prune_messages;
    # patch that to assert delegation + returned rowcount passthrough.
    mock_prune = AsyncMock(return_value=40)
    memory_module.prune_messages = mock_prune

    pipeline = ContextPipeline()

    pruned_count = await pipeline.prune_old_context(db, "test-agent", "test-session", keep_recent=50)

    # Returned the deleted-row count and delegated with correct args.
    assert pruned_count == 40
    mock_prune.assert_awaited_once_with(db, "test-agent", "test-session", 50)


@pytest.mark.asyncio
async def test_empty_context_handling():
    """Test handling of empty context scenarios."""
    db = MagicMock(spec=AsyncSession)

    import nomos_api.services.memory as memory_module

    mock_list = AsyncMock()
    memory_module.list_messages = mock_list

    pipeline = ContextPipeline()

    # Empty messages
    mock_list.return_value = []

    context = await pipeline.get_managed_context(db, "test-agent", "test-session")
    assert context == []

    stats = await pipeline.get_context_stats(db, "test-agent", "test-session")
    assert stats["total_messages"] == 0
