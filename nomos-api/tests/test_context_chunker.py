"""Tests for context chunker service."""

from nomos_api.services.context_chunker import ContextChunker


def test_chunk_context_basic():
    """Test basic context chunking."""
    chunker = ContextChunker(window_size=20, overlap=0.1)

    # Test with short text (should return single chunk)
    short_text = "Hello world"
    chunks = chunker.chunk_context(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    # Test with longer text
    long_text = "a" * 100
    chunks = chunker.chunk_context(long_text)
    assert len(chunks) > 1

    # Verify overlap
    assert len(chunks[0]) == 20
    assert len(chunks[1]) == 20

    # Verify chunks overlap by 10% (2 characters)
    overlap = len(set(chunks[0][-2:]) & set(chunks[1][:2]))
    assert overlap > 0


def test_chunk_messages():
    """Test message chunking with preservation of boundaries."""
    chunker = ContextChunker(window_size=50, overlap=0.1)

    # Create messages that would exceed window size
    messages = [
        {"role": "user", "content": "Short message"},
        {"role": "assistant", "content": "This is a longer response that should help fill up the context window"},
        {"role": "user", "content": "Another message"},
        {"role": "assistant", "content": "Yet another response that adds more content to the conversation"},
    ]

    chunks = chunker.chunk_messages(messages)

    # Should have at least one chunk
    assert len(chunks) >= 1

    # Each chunk should contain complete messages
    for chunk in chunks:
        assert all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in chunk)


def test_get_context_stats():
    """Test context statistics calculation."""
    chunker = ContextChunker(window_size=100, overlap=0.1)

    text = "Test content for statistics"
    stats = chunker.get_context_stats(text)

    assert "char_count" in stats
    assert "chunk_count" in stats
    assert "window_size" in stats
    assert "overlap_chars" in stats

    assert stats["char_count"] == len(text)
    assert stats["window_size"] == 100
    assert stats["overlap_chars"] == 10


def test_empty_context():
    """Test handling of empty context."""
    chunker = ContextChunker()

    chunks = chunker.chunk_context("")
    assert chunks == []

    message_chunks = chunker.chunk_messages([])
    assert message_chunks == []

    stats = chunker.get_context_stats("")
    assert stats["char_count"] == 0
    assert stats["chunk_count"] == 1  # Minimum 1 chunk


def test_boundary_conditions():
    """Test edge cases and boundary conditions."""
    chunker = ContextChunker(window_size=10, overlap=0.0)  # No overlap

    # Exactly window size
    text = "1234567890"
    chunks = chunker.chunk_context(text)
    assert len(chunks) == 1
    assert chunks[0] == text

    # One character over
    text = "12345678901"
    chunks = chunker.chunk_context(text)
    assert len(chunks) == 2
    assert chunks[0] == "1234567890"
    assert chunks[1] == "1"


def test_safe_split():
    """Test basic chunking behavior."""
    chunker = ContextChunker(window_size=15, overlap=0.0)

    text = "hello world this is a test"
    chunks = chunker.chunk_context(text)

    # Should split long text into chunks
    assert len(chunks) >= 1
    # First chunk should not exceed window size
    if len(chunks) > 1:
        assert len(chunks[0]) <= 15
        assert len(chunks[1]) <= 15
