"""Context pipeline service — orchestrate context management operations.

Coordinates chunking, summarization, and memory management.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.context_chunker import ContextChunker
from nomos_api.services.context_summarizer import ContextSummarizer
from nomos_api.services import memory
from nomos_api.models import AgentMemory

logger = logging.getLogger("nomos-api")


class ContextPipeline:
    """Orchestrate context management operations."""

    def __init__(self):
        self.chunker = ContextChunker()
        self.summarizer = ContextSummarizer()
        self.max_recent_messages = 50
        self.summary_threshold = 20  # Generate summary after 20 messages

    async def process_new_message(
        self, db: AsyncSession, agent_id: str, session_id: str, role: str, content: str, importance_score: float = 1.0
    ) -> AgentMemory:
        """Process a new message through the context pipeline.

        Args:
            db: Database session
            agent_id: Agent ID
            session_id: Session ID
            role: Message role (user, assistant, etc.)
            content: Message content
            importance_score: Importance score for retention

        Returns:
            Stored message
        """
        # 1. Store the new message
        message = await memory.store_message(db, agent_id, session_id, role, content)

        # 2. Check if context management is needed
        messages = await memory.list_messages(db, agent_id, session_id)

        if len(messages) >= self.summary_threshold:
            await self._manage_context(db, agent_id, session_id, messages)

        return message

    async def _manage_context(
        self, db: AsyncSession, agent_id: str, session_id: str, messages: List[AgentMemory]
    ) -> None:
        """Apply context management strategies."""
        logger.info("Applying context management for agent %s, session %s", agent_id, session_id)

        # Summarize the turns older than the most recent summary_threshold
        # window. The trigger fires at summary_threshold, so the retained
        # tail must be threshold-sized for the trigger to be meaningful
        # (a max_recent_messages-sized tail would never have older turns
        # until 50+ messages, making summary_threshold dead code).
        keep_recent = min(self.max_recent_messages, self.summary_threshold)
        older_messages = messages[:-keep_recent] if keep_recent else messages

        if older_messages:
            await self._generate_and_store_summary(db, agent_id, session_id, older_messages)

        logger.info("Context management completed for agent %s", agent_id)

    async def _generate_and_store_summary(
        self, db: AsyncSession, agent_id: str, session_id: str, messages: List[AgentMemory]
    ) -> Optional[AgentMemory]:
        """Generate summary and store as a special message."""
        # Convert AgentMemory objects to dict format for summarizer
        message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]

        # Generate summary
        summary_result = await self.summarizer.summarize(message_dicts, summary_type="conversation")

        if not summary_result:
            logger.warning("Summary generation failed for agent %s", agent_id)
            return None

        # Store summary as a system message
        summary_text = f"[SUMMARY]: {summary_result.summary}"

        summary_message = await memory.store_message(
            db,
            agent_id,
            session_id,
            "system",
            summary_text,
            importance_score=2.0,  # Higher importance for summaries
        )

        logger.info(
            "Generated summary for agent %s: %d tokens saved",
            agent_id,
            summary_result.original_token_count - summary_result.token_count,
        )

        return summary_message

    async def get_managed_context(self, db: AsyncSession, agent_id: str, session_id: str) -> List[Dict]:
        """Get context with management applied (summaries + recent messages).

        Returns:
            List of messages ready for LLM processing
        """
        messages = await memory.list_messages(db, agent_id, session_id)

        if not messages:
            return []

        # Separate summaries and recent messages
        summaries = [msg for msg in messages if msg.content and msg.content.startswith("[SUMMARY]")]
        recent_messages = [msg for msg in messages if not (msg.content and msg.content.startswith("[SUMMARY]"))][
            -self.max_recent_messages :
        ]

        # Convert to dict format
        context = []

        # Add summaries first (as system messages)
        for summary in summaries:
            context.append({"role": summary.role, "content": summary.content})

        # Add recent messages
        for msg in recent_messages:
            context.append({"role": msg.role, "content": msg.content})

        return context

    async def get_context_stats(self, db: AsyncSession, agent_id: str, session_id: str) -> Dict:
        """Get statistics about current context state."""
        messages = await memory.list_messages(db, agent_id, session_id)

        total_messages = len(messages)
        summary_count = len([m for m in messages if m.content and m.content.startswith("[SUMMARY]")])
        recent_count = min(self.max_recent_messages, total_messages - summary_count)

        # Estimate token counts (approximate)
        total_chars = sum(len(m.content) for m in messages if m.content)
        estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token

        return {
            "agent_id": agent_id,
            "session_id": session_id,
            "total_messages": total_messages,
            "summary_count": summary_count,
            "recent_messages": recent_count,
            "estimated_token_count": estimated_tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def prune_old_context(self, db: AsyncSession, agent_id: str, session_id: str, keep_recent: int = 50) -> int:
        """Prune old messages, keeping only recent turns and all summaries.

        Delegates to ``memory.prune_messages`` which performs the actual
        DB deletion. Summaries are always retained (DSGVO-safe: only the
        oldest non-summary turns beyond ``keep_recent`` are deleted).

        Returns:
            Number of messages actually pruned (rows deleted).
        """
        pruned = await memory.prune_messages(db, agent_id, session_id, keep_recent)
        logger.info("Pruned %d old messages for agent %s", pruned, agent_id)
        return pruned


class ContextManager:
    """High-level context manager with pipeline coordination."""

    def __init__(self):
        self.pipeline = ContextPipeline()
        self.max_context_tokens = 131072  # 131k token limit

    async def process_message(self, db: AsyncSession, agent_id: str, session_id: str, role: str, content: str) -> Dict:
        """Process a message through the full context pipeline."""
        # Process through pipeline
        message = await self.pipeline.process_new_message(db, agent_id, session_id, role, content)

        # Get current context stats
        stats = await self.pipeline.get_context_stats(db, agent_id, session_id)

        # Check if context exceeds limits
        context_ok = stats["estimated_token_count"] < self.max_context_tokens

        return {
            "message_id": message.id,
            "context_stats": stats,
            "context_within_limits": context_ok,
            "action_taken": "processed" if context_ok else "needs_pruning",
        }

    async def ensure_context_limits(self, db: AsyncSession, agent_id: str, session_id: str) -> Dict:
        """Ensure context stays within token limits."""
        stats = await self.pipeline.get_context_stats(db, agent_id, session_id)

        if stats["estimated_token_count"] >= self.max_context_tokens:
            pruned = await self.pipeline.prune_old_context(db, agent_id, session_id)
            return {
                "action": "pruned",
                "messages_pruned": pruned,
                "new_stats": await self.pipeline.get_context_stats(db, agent_id, session_id),
            }

        return {"action": "none", "current_stats": stats}
