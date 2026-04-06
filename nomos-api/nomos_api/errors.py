"""Standardized error response model and HTTP error code mapping.

Every error response from NomOS includes a machine-readable code, a
human-readable detail message, and the request correlation ID for
traceability across frontend, API, and logs.
"""

from __future__ import annotations

from pydantic import BaseModel


class NomOSErrorResponse(BaseModel):
    """Standardized error response body returned by all NomOS API error handlers."""

    detail: str
    code: str
    request_id: str


ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "GATEWAY_ERROR",
    503: "SERVICE_UNAVAILABLE",
}
