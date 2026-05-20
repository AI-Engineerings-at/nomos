"""API Metrics Middleware — collects request/response metrics for monitoring.

v0.4.0 (P2 / audit C-F9): the hot path no longer opens a DB session per
request. Events are enqueued into a process-local in-memory buffer
(``services.metrics_buffer``) and a lifespan-managed background task
drains the buffer into the metrics table every 30 s. At 1000 req/s this
drops DB transactions for metrics from 2000+/s to 1 batch every 30 s.

Fail-closed: if the buffer fills (drain stuck / DB outage) the oldest
events are evicted. Metrics observability MUST never block or fail a
user request.
"""

from __future__ import annotations

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from nomos_api.services.metrics_buffer import enqueue_request

logger = logging.getLogger("nomos-api.metrics")


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects API performance metrics.

    Hot path = one ``deque.append()`` per metric. No DB session, no IO.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        try:
            enqueue_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=duration_ms,
            )
        except Exception:
            # Truly defensive — deque.append cannot raise under documented
            # conditions, but if the buffer module breaks the request must
            # still succeed.
            logger.warning(
                "metrics enqueue failed for %s %s (suppressed)",
                request.method,
                request.url.path,
                exc_info=True,
            )
        return response
