"""Tests for context summarizer service."""

import pytest
from unittest.mock import AsyncMock, patch

from nomos_api.services.context_summarizer import ContextSummarizer


@pytest.mark.asyncio
async def test_summarize_with_mock():
    """Test summarization with mocked LLM API."""
    summarizer = ContextSummarizer()

    # Mock the LLM API call
    mock_response = {"choices": [{"message": {"content": "This is a test summary"}}]}

    with patch.object(summarizer, "_call_llm_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        messages = [{"role": "user", "content": "Hello there"}, {"role": "assistant", "content": "Hi, how can I help?"}]

        result = await summarizer.summarize(messages)

        assert result is not None
        assert result.summary == "This is a test summary"
        assert result.token_count > 0
        assert result.original_token_count > result.token_count


@pytest.mark.asyncio
async def test_empty_messages():
    """Test handling of empty message list."""
    summarizer = ContextSummarizer()

    result = await summarizer.summarize([])

    assert result is not None
    assert result.summary == ""
    assert result.token_count == 0
    assert result.original_token_count == 0


@pytest.mark.asyncio
async def test_llm_api_failure():
    """Test handling of LLM API failure."""
    summarizer = ContextSummarizer()

    with patch.object(summarizer, "_call_llm_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = None  # Simulate API failure

        messages = [{"role": "user", "content": "Test"}]
        result = await summarizer.summarize(messages)

        assert result is None


@pytest.mark.asyncio
async def test_hierarchical_summarize():
    """Test hierarchical summarization."""
    summarizer = ContextSummarizer()

    # Mock multiple LLM calls
    mock_response = {"choices": [{"message": {"content": "Summary content"}}]}

    with patch.object(summarizer, "_call_llm_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        messages = [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}]

        summaries = await summarizer.hierarchical_summarize(messages)

        assert len(summaries) == 2  # Full summary + action items
        assert summaries[0]["level"] == 1
        assert summaries[1]["level"] == 2


def test_prompt_building():
    """Test prompt construction for different summary types."""
    summarizer = ContextSummarizer()

    messages = [
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "It's sunny today."},
    ]

    # Test conversation summary prompt
    prompt = summarizer._build_summary_prompt(messages, "conversation")
    assert "Summarize this conversation" in prompt
    assert "bullet points" in prompt

    # Test action items prompt
    prompt = summarizer._build_summary_prompt(messages, "action_items")
    assert "Extract action items" in prompt
    assert "numbered list" in prompt


def test_token_savings_calculation():
    """Test token savings estimation."""
    summarizer = ContextSummarizer()

    original_messages = [
        {"role": "user", "content": "This is a very long message with many words"},
        {"role": "assistant", "content": "This is an even longer response with more words"},
    ]

    summaries = [{"level": 1, "type": "full", "summary": "Short summary", "token_count": 5}]

    savings = summarizer.estimate_token_savings(original_messages, summaries)

    assert 0 <= savings <= 1.0


def test_message_formatting():
    """Test message formatting for prompts."""
    summarizer = ContextSummarizer()

    messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]

    formatted = summarizer._format_messages(messages)
    assert "USER: Hello" in formatted
    assert "ASSISTANT: Hi" in formatted
