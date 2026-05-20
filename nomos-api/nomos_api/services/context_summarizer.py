"""Context summarizer service — compress conversation history using LLM.

Provides hierarchical summarization for efficient context management.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional
import httpx
from pydantic import BaseModel

from nomos_api.config import settings

logger = logging.getLogger("nomos-api")


class SummaryRequest(BaseModel):
    """Request model for summarization."""

    messages: List[Dict[str, str]]
    summary_type: str = "conversation"
    max_length: int = 500


class SummaryResponse(BaseModel):
    """Response model for summarization."""

    summary: str
    token_count: int
    original_token_count: int


class ContextSummarizer:
    """Generate summaries of conversation history using LLM."""

    def __init__(self):
        self.max_retries = 3
        self.timeout = 30.0

    async def _call_llm_api(self, prompt: str) -> Optional[dict]:
        """Call LLM API for summarization."""
        if not settings.llm_base_url or not settings.llm_api_key:
            logger.warning("LLM API not configured for summarization")
            return None

        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": "You are a helpful summarization assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=body, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    logger.warning("LLM rate limit reached, retrying (%d/%d)", attempt + 1, self.max_retries)
                    continue
                # M4 (0.3.0): audit D-#10. Do NOT log exc.response.text —
                # the body can contain provider API keys or other tenant
                # PII echoed back in the error envelope. Status code only.
                logger.error(
                    "LLM API error status=%d reason=%s attempt=%d/%d",
                    exc.response.status_code,
                    exc.response.reason_phrase,
                    attempt + 1,
                    self.max_retries,
                )
                return None
            except httpx.TimeoutException as exc:
                # M4: previously bundled into the generic Exception branch.
                # Surface explicitly + retry once, then fail.
                logger.warning(
                    "LLM API timed out: %s (attempt %d/%d)",
                    type(exc).__name__,
                    attempt + 1,
                    self.max_retries,
                )
                continue
            except Exception:
                # M4: log type + traceback, NOT exc's repr (some httpx
                # exceptions stringify the response body).
                logger.exception("LLM API call failed (attempt %d/%d)", attempt + 1, self.max_retries)
                return None

        return None

    def _build_summary_prompt(self, messages: List[Dict[str, str]], summary_type: str = "conversation") -> str:
        """Construct prompt for summarization."""
        if summary_type == "conversation":
            return (
                "Summarize this conversation in a concise manner, capturing the main points "
                "and key decisions. Use bullet points if appropriate. Limit to 200 words:\n\n"
                + self._format_messages(messages)
            )

        elif summary_type == "action_items":
            return (
                "Extract action items and decisions from this conversation. "
                "Format as a numbered list. Be specific about who needs to do what:\n\n"
                + self._format_messages(messages)
            )

        else:  # default
            return "Provide a brief summary of this conversation:\n\n" + self._format_messages(messages)

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for prompt."""
        return "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in messages])

    async def summarize(
        self, messages: List[Dict[str, str]], summary_type: str = "conversation"
    ) -> Optional[SummaryResponse]:
        """Generate summary of conversation history.

        Args:
            messages: List of message dictionaries
            summary_type: Type of summary to generate

        Returns:
            SummaryResponse or None if summarization fails
        """
        if not messages:
            return SummaryResponse(summary="", token_count=0, original_token_count=0)

        prompt = self._build_summary_prompt(messages, summary_type)
        result = await self._call_llm_api(prompt)

        if not result or "choices" not in result:
            return None

        summary_text = result["choices"][0]["message"]["content"].strip()

        # Count tokens (approximate)
        summary_tokens = len(summary_text.split())
        original_tokens = sum(len(msg.get("content", "").split()) for msg in messages)

        return SummaryResponse(summary=summary_text, token_count=summary_tokens, original_token_count=original_tokens)

    async def hierarchical_summarize(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Generate hierarchical summaries at different levels.

        Returns:
            List of summaries with level information
        """
        summaries = []

        # Level 1: Full conversation summary
        full_summary = await self.summarize(messages, "conversation")
        if full_summary:
            summaries.append(
                {"level": 1, "type": "full", "summary": full_summary.summary, "token_count": full_summary.token_count}
            )

        # Level 2: Action items
        action_summary = await self.summarize(messages, "action_items")
        if action_summary:
            summaries.append(
                {
                    "level": 2,
                    "type": "actions",
                    "summary": action_summary.summary,
                    "token_count": action_summary.token_count,
                }
            )

        return summaries

    def estimate_token_savings(self, original_messages: List[Dict[str, str]], summaries: List[Dict]) -> float:
        """Estimate token savings from summarization."""
        original_tokens = sum(len(msg.get("content", "").split()) for msg in original_messages)
        summary_tokens = sum(s["token_count"] for s in summaries)

        if original_tokens == 0:
            return 0.0

        return 1.0 - (summary_tokens / original_tokens)
