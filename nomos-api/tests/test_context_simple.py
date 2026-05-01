"""Simple tests for context management services without complex mocking."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from nomos_api.services.context_chunker import ContextChunker
from nomos_api.services.context_summarizer import ContextSummarizer
from nomos_api.services.context_pipeline import ContextPipeline, ContextManager


def test_context_chunker_integration():
    """Test context chunker with realistic scenarios."""
    chunker = ContextChunker(window_size=100, overlap=0.1)

    # Test with realistic conversation
    long_conversation = """
User: Hello, how are you?
Assistant: I'm doing well, thank you for asking. How can I help you today?
User: I need help with a complex problem related to context management in AI systems.
Assistant: That's an interesting topic. Context management is crucial for handling large prompts effectively.
User: Yes, exactly. We're dealing with prompts that exceed the 131k token limit and need a comprehensive solution.
Assistant: I understand. Let me break down the key components of a good context management solution...
"""

    chunks = chunker.chunk_context(long_conversation)

    # Should create multiple chunks
    assert len(chunks) > 1

    # Each chunk should be roughly window size
    for chunk in chunks:
        assert len(chunk) <= 110  # window_size + overlap
        assert len(chunk) > 50  # reasonable minimum

    # Test message chunking
    messages = [
        {"role": "user", "content": "Message 1" * 20},  # Long message
        {"role": "assistant", "content": "Response 1" * 20},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
    ]

    message_chunks = chunker.chunk_messages(messages)
    assert len(message_chunks) >= 1

    # Verify message integrity
    for chunk in message_chunks:
        for msg in chunk:
            assert "role" in msg
            assert "content" in msg


@pytest.mark.asyncio
async def test_context_summarizer_mocked():
    """Test summarizer with mocked LLM calls."""
    summarizer = ContextSummarizer()

    # Mock the LLM API
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "This is a concise summary of the conversation covering main points and key decisions."
                }
            }
        ]
    }

    with patch.object(summarizer, "_call_llm_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        # Test with realistic conversation
        messages = [
            {"role": "user", "content": "What's the best approach for context management?"},
            {
                "role": "assistant",
                "content": "The best approach involves chunking, summarization, and strategic retention.",
            },
            {"role": "user", "content": "Can you elaborate on the chunking strategy?"},
            {"role": "assistant", "content": "Chunking uses sliding windows with overlap to maintain coherence."},
        ]

        result = await summarizer.summarize(messages, "conversation")

        assert result is not None
        assert "concise summary" in result.summary
        assert result.token_count > 0
        assert result.original_token_count > result.token_count

        # Test hierarchical summarization
        summaries = await summarizer.hierarchical_summarize(messages)
        assert len(summaries) == 2  # Full + action items

        # Test token savings calculation
        savings = summarizer.estimate_token_savings(messages, summaries)
        assert 0 < savings < 1.0


def test_context_pipeline_initialization():
    """Test pipeline initialization and basic properties."""
    pipeline = ContextPipeline()

    assert pipeline.chunker is not None
    assert pipeline.summarizer is not None
    assert pipeline.max_recent_messages == 50
    assert pipeline.summary_threshold == 20

    # Test chunker properties
    assert pipeline.chunker.window_size == 8192
    assert pipeline.chunker.overlap == 0.1


def test_context_manager_initialization():
    """Test context manager initialization."""
    manager = ContextManager()

    assert manager.pipeline is not None
    assert manager.max_context_tokens == 131072

    # Verify pipeline is properly initialized
    assert manager.pipeline.chunker is not None
    assert manager.pipeline.summarizer is not None

    @pytest.mark.asyncio
    async def test_context_manager_mocked():
        """Test context manager with mocked dependencies."""
        manager = ContextManager()

        # Create a mock message object
        mock_message = MagicMock()
        mock_message.id = 123

        # Mock the pipeline methods
        manager.pipeline.process_new_message = AsyncMock(return_value=mock_message)
        manager.pipeline.get_context_stats = AsyncMock(return_value={"estimated_token_count": 100000})

        # Mock database session
        mock_db = MagicMock()

        # Test process_message
        result = await manager.process_message(mock_db, "test-agent", "test-session", "user", "Hello")

        assert result is not None
        assert "message_id" in result
        assert result["message_id"] == 123
        manager.pipeline.process_new_message.assert_awaited_once()


def test_chunking_performance():
    """Test chunking performance with large inputs."""
    chunker = ContextChunker(window_size=1000, overlap=0.05)

    # Create a large text (simulating 50k characters)
    large_text = "This is a test sentence. " * 2500  # ~50k chars

    # Time the chunking operation
    import time

    start_time = time.time()

    chunks = chunker.chunk_context(large_text)

    end_time = time.time()
    duration = end_time - start_time

    # Should complete quickly (< 100ms)
    assert duration < 0.1

    # Should create reasonable number of chunks
    assert 10 <= len(chunks) <= 100

    # Verify chunk sizes
    for chunk in chunks:
        assert len(chunk) <= 1050  # window_size + overlap


def test_message_chunking_edge_cases():
    """Test message chunking with edge cases."""
    chunker = ContextChunker(window_size=50, overlap=0.0)

    # Empty messages
    assert chunker.chunk_messages([]) == []

    # Single short message
    single = [{"role": "user", "content": "Hi"}]
    result = chunker.chunk_messages(single)
    assert len(result) == 1
    assert result[0] == single

    # Single long message (but still under window size)
    long_msg = [{"role": "user", "content": "a" * 100}]
    result = chunker.chunk_messages(long_msg)
    assert len(result) == 1  # Still fits in one chunk (window_size=50, but message is single dict)

    # Mixed short and long messages
    mixed = [
        {"role": "user", "content": "Short"},
        {"role": "assistant", "content": "a" * 200},  # Long content
        {"role": "user", "content": "Another short"},
    ]
    result = chunker.chunk_messages(mixed)
    # With window_size=50 chars, the long message should cause splitting
    assert len(result) >= 2


def test_stats_calculation():
    """Test context statistics calculation."""
    chunker = ContextChunker(window_size=100, overlap=0.05)

    # Test with various text lengths
    test_cases = [
        ("", 1),  # Empty text -> 1 chunk minimum
        ("a" * 50, 1),  # Short text
        ("a" * 150, 2),  # Just over window size
        ("a" * 1000, 10),  # Large text
    ]

    for text, expected_chunks in test_cases:
        stats = chunker.get_context_stats(text)
        assert stats["char_count"] == len(text)
        assert stats["window_size"] == 100
        assert stats["overlap_chars"] == 5
        # Chunk count should be reasonable
        assert stats["chunk_count"] >= expected_chunks - 1
        assert stats["chunk_count"] <= expected_chunks + 1


@pytest.mark.asyncio
async def test_summarizer_prompt_building():
    """Test different prompt building strategies."""
    summarizer = ContextSummarizer()

    messages = [
        {"role": "user", "content": "What's the weather today?"},
        {"role": "assistant", "content": "It's sunny and 75°F."},
        {"role": "user", "content": "Should I bring a jacket?"},
        {"role": "assistant", "content": "A light jacket might be good for evening."},
    ]

    # Test conversation prompt
    prompt = summarizer._build_summary_prompt(messages, "conversation")
    assert "Summarize this conversation" in prompt
    assert "bullet points" in prompt
    assert "USER:" in prompt
    assert "ASSISTANT:" in prompt

    # Test action items prompt
    prompt = summarizer._build_summary_prompt(messages, "action_items")
    assert "Extract action items" in prompt
    assert "numbered list" in prompt

    # Test message formatting
    formatted = summarizer._format_messages(messages)
    lines = formatted.split("\n")
    assert len(lines) == 4
    assert all(":" in line for line in lines)


def test_context_limits():
    """Test context size limits and calculations."""
    manager = ContextManager()

    # Default limit should be 131k tokens
    assert manager.max_context_tokens == 131072

    # Test with different limits
    manager.max_context_tokens = 8192  # 8k limit
    assert manager.max_context_tokens == 8192

    # Verify pipeline uses same chunker
    assert manager.pipeline.chunker.window_size == 8192
