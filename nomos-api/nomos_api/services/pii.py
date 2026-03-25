"""PII filter service — wraps the core PIIFilter for the API layer."""

from __future__ import annotations

from dataclasses import dataclass

from nomos.core.pii_filter import PIIFilter


@dataclass
class PIIFilterAPIResult:
    """API-friendly result of PII filtering."""

    filtered: str
    pii_count: int
    matches: list[dict]


def filter_text(text: str) -> PIIFilterAPIResult:
    """Filter PII from text and return API-friendly result."""
    pii_filter = PIIFilter()
    result = pii_filter.filter(text)
    return PIIFilterAPIResult(
        filtered=result.filtered_text,
        pii_count=result.pii_count,
        matches=[
            {
                "type": m.pii_type,
                "start": m.start,
                "end": m.end,
            }
            for m in result.matches
        ],
    )
