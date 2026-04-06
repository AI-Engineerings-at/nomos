"""Request correlation ID middleware.

Assigns a unique ID to every request for end-to-end traceability.
If the client sends an ``X-Request-ID`` header, the server echoes it.
Otherwise a UUID4 is generated.  The ID is stored on ``request.state``
and added to the response headers.

This middleware is registered as the outermost layer, so it also acts as
a safety net for unhandled exceptions — guaranteeing a structured JSON
error body even when inner middleware or handlers raise.
"""

from __future__ import annotations

import json
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nomos-api")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject and propagate ``X-Request-ID`` on every request/response cycle."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id: str = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception as exc:
            # Safety net: unhandled exceptions must still produce a structured response
            logger.error(
                "Unhandled exception: %s",
                exc,
                exc_info=True,
                extra={"request_id": request_id},
            )
            body = json.dumps(
                {
                    "detail": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "request_id": request_id,
                }
            )
            return Response(
                content=body,
                status_code=500,
                media_type="application/json",
                headers={"X-Request-ID": request_id},
            )
        response.headers["X-Request-ID"] = request_id
        return response
