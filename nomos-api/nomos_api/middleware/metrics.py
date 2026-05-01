"""API Metrics Middleware — collect request/response metrics for monitoring."""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from nomos_api.database import get_db
from nomos_api.services.metrics import MetricsService


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects API performance metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.monotonic()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        # Record metrics
        db = await anext(get_db())
        metrics_service = MetricsService(db)
        try:
            # Record request count
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

            # Record latency
            await metrics_service.record_metric(
                metric_name="api.latency",
                value=duration_ms,
                dimensions={"endpoint": request.url.path, "method": request.method},
                source="api",
            )

            # Record error if applicable
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
        finally:
            await db.close()

        return response
