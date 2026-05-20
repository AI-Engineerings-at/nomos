"""In-memory metrics buffer + lifespan-managed drain task.

v0.4.0 (P2 / audit C-F9): the previous ``APIMetricsMiddleware`` opened a
fresh ``AsyncSession`` per request and committed two rows (counter +
latency) plus a third on error. At 1000 req/s this produced 2-3000
DB transactions/s purely for observability, on the same pool that served
user traffic.

Pattern (in-process queue + lifespan-managed drain):

1. Middleware enqueues lightweight ``MetricEvent`` dicts into a bounded
   ``deque`` (max 10 000). Enqueue is sync, lock-free, O(1) — the request
   hot-path pays a single deque-append.
2. A background asyncio task created in ``main.py`` lifespan drains the
   buffer every 30 s under a single ``AsyncSession`` and writes one batch
   ``INSERT`` per metric name. One DB roundtrip per 30 s of traffic
   instead of one per request.
3. If the buffer fills (slow drain / DB outage), the oldest event is
   evicted and a ``dropped`` counter increments — fail-closed semantics
   on observability, never on user traffic.

The buffer + drain live in the API process, NOT the ARQ worker — API
and worker are separate containers and don't share memory. Cross-process
queuing through Valkey would also work but adds Valkey traffic on every
request; given that this is best-effort observability the simpler
in-process design wins.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from nomos_api.database import async_session
from nomos_api.services.metrics import MetricsService

logger = logging.getLogger("nomos.metrics_buffer")

# Soft cap. At 1 000 req/s and 30 s drain interval we hold 30 000 events;
# 10 000 is the cap on each METRIC NAME's buffer (we keep 3 deques —
# requests, latency, errors — so peak memory is ~30 000 events * ~200
# bytes = ~6 MB. If the drain is slow, the oldest events are evicted.
_MAX_BUFFER_PER_METRIC = 10_000


@dataclass(slots=True)
class _MetricEvent:
    """One observation. Keep it dataclass+slots for memory + speed."""

    metric_name: str
    value: float
    endpoint: str
    method: str
    status_code: Optional[str]
    ts_monotonic: float


_buffer_requests: "deque[_MetricEvent]" = deque(maxlen=_MAX_BUFFER_PER_METRIC)
_buffer_latency: "deque[_MetricEvent]" = deque(maxlen=_MAX_BUFFER_PER_METRIC)
_buffer_errors: "deque[_MetricEvent]" = deque(maxlen=_MAX_BUFFER_PER_METRIC)

# Counters that record buffer pressure for ops dashboards.
_buffer_stats = {
    "enqueued": 0,
    "drained": 0,
    "dropped": 0,
    "last_drain_at": 0.0,
    "last_drain_count": 0,
}


def enqueue_request(*, endpoint: str, method: str, status_code: int, latency_ms: float) -> None:
    """Called from middleware on every request. Lock-free, O(1)."""
    now = time.monotonic()
    sc = str(status_code)
    # If the deque is full, deque.append() will evict the oldest entry
    # automatically (maxlen contract). Track the eviction so dashboards
    # can see backpressure.
    was_full = len(_buffer_requests) == _MAX_BUFFER_PER_METRIC
    _buffer_requests.append(_MetricEvent("api.requests", 1.0, endpoint, method, sc, now))
    _buffer_latency.append(_MetricEvent("api.latency", latency_ms, endpoint, method, None, now))
    if status_code >= 400:
        _buffer_errors.append(_MetricEvent("api.errors", 1.0, endpoint, method, sc, now))
    _buffer_stats["enqueued"] += 1
    if was_full:
        _buffer_stats["dropped"] += 1


def buffer_snapshot() -> dict:
    """Return current buffer stats. Used by /api/monitoring/health."""
    return {
        **_buffer_stats,
        "requests_pending": len(_buffer_requests),
        "latency_pending": len(_buffer_latency),
        "errors_pending": len(_buffer_errors),
    }


def _drain_all() -> tuple[list[_MetricEvent], list[_MetricEvent], list[_MetricEvent]]:
    """Atomically swap each deque with a fresh one and return the drained
    snapshots. Append happens BEFORE this swap on each event; readers see
    a consistent batch."""
    req = list(_buffer_requests)
    lat = list(_buffer_latency)
    err = list(_buffer_errors)
    _buffer_requests.clear()
    _buffer_latency.clear()
    _buffer_errors.clear()
    return req, lat, err


async def _drain_once() -> int:
    """Drain the current buffer in one batch insert. Returns rows written."""
    req, lat, err = _drain_all()
    total = len(req) + len(lat) + len(err)
    if total == 0:
        return 0
    try:
        async with async_session() as db:
            ms = MetricsService(db)
            for ev in req:
                await ms.record_metric(
                    metric_name=ev.metric_name,
                    value=ev.value,
                    dimensions={
                        "endpoint": ev.endpoint,
                        "method": ev.method,
                        "status_code": ev.status_code or "",
                    },
                    source="api",
                )
            for ev in lat:
                await ms.record_metric(
                    metric_name=ev.metric_name,
                    value=ev.value,
                    dimensions={"endpoint": ev.endpoint, "method": ev.method},
                    source="api",
                )
            for ev in err:
                await ms.record_metric(
                    metric_name=ev.metric_name,
                    value=ev.value,
                    dimensions={
                        "endpoint": ev.endpoint,
                        "method": ev.method,
                        "status_code": ev.status_code or "",
                    },
                    source="api",
                )
        _buffer_stats["drained"] += total
        _buffer_stats["last_drain_at"] = time.monotonic()
        _buffer_stats["last_drain_count"] = total
    except Exception:
        # DB outage / slow drain — events are dropped, NOT retried.
        # Observability must never block a request.
        logger.exception("metrics drain failed; %d events dropped", total)
        _buffer_stats["dropped"] += total
    return total


async def metrics_drain_loop(interval_seconds: float = 30.0) -> None:
    """Background task. Lifespan-managed; cancelled cleanly on shutdown."""
    logger.info("metrics drain loop started (interval=%.1fs)", interval_seconds)
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                drained = await _drain_once()
                if drained:
                    logger.debug("metrics drained %d events", drained)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("metrics drain iteration failed; continuing")
    except asyncio.CancelledError:
        # Final flush on shutdown so we don't lose the in-flight buffer.
        try:
            drained = await _drain_once()
            logger.info("metrics drain loop shutdown — final flush: %d events", drained)
        except Exception:
            logger.exception("metrics drain final flush failed")
        raise
