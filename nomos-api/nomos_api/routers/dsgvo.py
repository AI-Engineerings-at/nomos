"""DSGVO endpoints — Art. 17 forget, Art. 15 export."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from nomos_api.schemas import (
    DSGVOExportRequest,
    DSGVOExportResponse,
    DSGVOForgetRequest,
    DSGVOForgetResponse,
)
from nomos_api.services.forget import ForgetService
from nomos_api.services.honcho import HonchoClient

router = APIRouter(prefix="/api", tags=["dsgvo"])

_client = HonchoClient(base_url="http://localhost:5055")
_forget_service = ForgetService(_client)


def get_forget_service() -> ForgetService:
    """Return the forget service singleton."""
    return _forget_service


@router.post("/dsgvo/forget", response_model=DSGVOForgetResponse)
async def dsgvo_forget(request: DSGVOForgetRequest) -> DSGVOForgetResponse:
    """Art. 17 DSGVO — delete all messages containing the email address."""
    svc = get_forget_service()
    result = svc.forget(request.email)
    return DSGVOForgetResponse(
        deleted_messages=result["deleted_messages"],
        search_term=result["search_term"],
        audit_event=result["audit_event"],
        audit_preserved=result["audit_preserved"],
        timestamp=result["timestamp"],
    )


@router.post("/dsgvo/export", response_model=DSGVOExportResponse)
async def dsgvo_export(request: DSGVOExportRequest) -> DSGVOExportResponse:
    """Art. 15 DSGVO — export all data for an email address."""
    svc = get_forget_service()
    client = svc.client
    matching_messages = [
        msg for msg in client._messages.values() if request.email in msg["content"]
    ]
    return DSGVOExportResponse(
        email=request.email,
        messages=matching_messages,
        total=len(matching_messages),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
