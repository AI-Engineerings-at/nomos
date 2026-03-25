"""PII filter endpoints — scan and redact PII from text."""

from __future__ import annotations

from fastapi import APIRouter

from nomos_api.schemas import PIIFilterRequest, PIIFilterResponse, PIIMatchResponse
from nomos_api.services.pii import filter_text

router = APIRouter(prefix="/api", tags=["pii"])


@router.post("/pii/filter", response_model=PIIFilterResponse)
async def filter_pii(request: PIIFilterRequest) -> PIIFilterResponse:
    """Scan text for PII and return redacted version."""
    result = filter_text(request.text)
    return PIIFilterResponse(
        filtered=result.filtered,
        pii_count=result.pii_count,
        matches=[
            PIIMatchResponse(type=m["type"], start=m["start"], end=m["end"])
            for m in result.matches
        ],
    )
