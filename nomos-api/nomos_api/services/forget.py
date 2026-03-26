"""DSGVO forget/export service — DB-backed via agent memory."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.memory import delete_by_content, search_messages


async def forget(db: AsyncSession, search_term: str) -> dict:
    """Delete all messages containing search_term (Art. 17 DSGVO).

    Returns a dict with deletion count, audit metadata, and timestamp.
    """
    count = await delete_by_content(db, search_term)
    return {
        "deleted_messages": count,
        "search_term": search_term,
        "audit_event": "data.erased" if count > 0 else "",
        "audit_preserved": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def export_data(db: AsyncSession, search_term: str) -> dict:
    """Export all messages containing search_term (Art. 15 DSGVO).

    Returns a dict with matching messages and total count.
    """
    messages = await search_messages(db, search_term)
    return {
        "email": search_term,
        "messages": [
            {
                "agent_id": m.agent_id,
                "session_id": m.session_id,
                "role": m.role,
                "content": m.content,
            }
            for m in messages
        ],
        "total": len(messages),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
