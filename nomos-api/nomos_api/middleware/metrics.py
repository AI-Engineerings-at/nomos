"""API Metrics Middleware — collect request/response metrics for monitoring."""

from __future__ import annotations

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from nomos_api.database import async_session
from nomos_api.services.metrics import MetricsService

logger = logging.getLogger("nomos-api.metrics")


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects API performance metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.monotonic()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        # Record metrics. This must NEVER turn a successful request into an
        # error: metrics persistence is best-effort observability, not part
        # of the request contract. Any failure is logged and swallowed.
        try:
            async with async_session() as db:
                metrics_service = MetricsService(db)
                await metrics_service.record_metric(
                    metric_name="api.requests",
                    value=1.0,
                    dimensions={
                        "endpoint": request.url.path,
                        "method": request.method,
                        "status_code": str(response.status_code),
                    },
                    source="api",
                )
                await metrics_service.record_metric(
                    metric_name="api.latency",
                    value=duration_ms,
                    dimensions={"endpoint": request.url.path, "method": request.method},
                    source="api",
                )
                if response.status_code >= 400:
                    await metrics_service.record_metric(
                        metric_name="api.errors",
                        value=1.0,
                        dimensions={
                            "endpoint": request.url.path,
                            "method": request.method,
                            "status_code": str(response.status_code),
                        },
                        source="api",
                    )
        except Exception:
            logger.warning(
                "metrics recording failed for %s %s",
                request.method,
                request.url.path,
                exc_info=True,
            )

        return response
