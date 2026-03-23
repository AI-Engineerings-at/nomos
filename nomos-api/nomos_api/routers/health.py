"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from nomos_api.config import settings
from nomos_api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.api_title, version=settings.api_version)
