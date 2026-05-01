"""Context chunker service — split large contexts into manageable chunks.

Uses sliding window approach with configurable size and overlap.
"""

from __future__ import annotations

from typing import List


class ContextChunker:
    """Split large text contexts into chunks using sliding window approach."""

    def __init__(self, window_size: int = 8192, overlap: float = 0.1):
        """Initialize chunker.

        Args:
            window_size: Target chunk size in characters (default: 8192)
            overlap: Overlap ratio between chunks (default: 0.1)
        """
        self.window_size = window_size
        self.overlap = overlap
        self.overlap_chars = int(window_size * overlap)

    def _count_chars(self, text: str) -> int:
        """Count characters in text."""
        return len(text)

    def _safe_split(self, text: str, position: int) -> str:
        """Split text at position, avoiding breaking words."""
        if position >= len(text):
            return text

        # Find nearest whitespace before position
        split_pos = text.rfind(" ", 0, position)
        if split_pos == -1:
            split_pos = position

        return text[:split_pos]

    def chunk_context(self, context: str) -> List[str]:
        """Split context into chunks with overlap.

        Args:
            context: Input text to chunk

        Returns:
            List of text chunks
        """
        if not context:
            return []

        context_length = self._count_chars(context)
        chunks = []

        if context_length <= self.window_size:
            return [context]

        # Sliding window chunking
        for i in range(0, context_length, self.window_size - self.overlap_chars):
            end_pos = i + self.window_size
            if end_pos > context_length:
                end_pos = context_length
            chunk = context[i:end_pos]
            chunks.append(chunk)

        return chunks

    def chunk_messages(self, messages: List[dict]) -> List[List[dict]]:
        """Chunk a list of messages while preserving message boundaries.

        Args:
            messages: List of message dictionaries (role, content)

        Returns:
            List of message chunks
        """
        if not messages:
            return []

        chunks: List[List[dict]] = []
        current_chunk: List[dict] = []
        current_size = 0

        for message in messages:
            message_text = message.get("content", "")
            message_chars = self._count_chars(message_text)

            # If adding this message would exceed window size, finalize current chunk
            if current_size + message_chars > self.window_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0

            current_chunk.append(message)
            current_size += message_chars

        # Add final chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_context_stats(self, context: str) -> dict:
        """Get statistics about context size.

        Returns:
            Dictionary with character count and estimated chunk count
        """
        char_count = self._count_chars(context)
        chunk_count = max(1, (char_count + self.window_size - 1) // (self.window_size - self.overlap_chars))

        return {
            "char_count": char_count,
            "chunk_count": chunk_count,
            "window_size": self.window_size,
            "overlap_chars": self.overlap_chars,
        }
