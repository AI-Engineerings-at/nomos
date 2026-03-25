"""DSGVO Art. 17 Forget service — delete messages containing PII.

Deletes all messages containing the search term (e.g., email address)
from the Honcho message store. Preserves an audit trail entry that
records the deletion event without storing the deleted content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from nomos_api.services.honcho import HonchoClient


@dataclass
class ForgetService:
    """Implements DSGVO Art. 17 right to erasure against Honcho message store."""

    client: HonchoClient

    def forget(self, search_term: str) -> dict:
        """Delete all messages containing search_term and return audit result.

        Returns a dict with:
        - deleted_messages: number of messages deleted
        - search_term: the term that was searched for
        - audit_event: "data.erased" if any messages were deleted, empty otherwise
        - audit_preserved: True (audit trail is always preserved)
        - timestamp: ISO 8601 timestamp of the operation
        """
        deleted_count = self.client.delete_messages_by_content(search_term)

        return {
            "deleted_messages": deleted_count,
            "search_term": search_term,
            "audit_event": "data.erased" if deleted_count > 0 else "",
            "audit_preserved": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
