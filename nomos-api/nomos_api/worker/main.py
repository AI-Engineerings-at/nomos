"""ARQ Worker Settings — connects to Valkey, schedules cron jobs.

Run with: python -m arq nomos_api.worker.main.WorkerSettings
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.config import settings
from nomos_api.worker.jobs.alerts import process_alerts
from nomos_api.worker.jobs.approvals import expire_approvals
from nomos_api.worker.jobs.audit_anchor import anchor_audit_heads
from nomos_api.worker.jobs.audit_retention import audit_integrity_checkpoint
from nomos_api.worker.jobs.heartbeat import detect_stale_agents
from nomos_api.worker.jobs.incidents import check_incident_deadlines
from nomos_api.worker.jobs.retention import retention_cleanup

# v0.4.0 (P2 / C-F9): API metrics no longer go through this worker. The
# API drains its own in-memory buffer via a lifespan-managed asyncio task
# every 30s (see services.metrics_buffer). Cross-process queueing through
# Valkey would also work, but the simpler in-process drain has lower
# latency, no Valkey traffic, and the same fail-closed semantics (buffer
# capped at 10k entries; overflow is dropped + counted).

logger = logging.getLogger("nomos.worker.main")

# Module-level session factory — shared by all jobs in this worker process.
# Separate from the API's request-scoped sessions. v0.4.0 (O1, audit C-F1):
# explicit pool sizing matches the API engine; engine.dispose() registered on
# worker shutdown so the pool drains cleanly on SIGTERM.
_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
)
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


def get_session_factory() -> async_sessionmaker:
    """Return the worker's session factory. Used by jobs when no override is given."""
    return _session_factory


async def _on_worker_startup(ctx: dict) -> None:
    """ARQ on_startup hook — surface the worker engine via ctx so jobs can
    inject it via ctx['session_factory'] instead of re-importing this module
    (closes the late-binding reverse-import audit C-F5 partially)."""
    ctx["session_factory"] = _session_factory
    logger.info(
        "nomos-worker startup — engine=%s pool_size=10 max_overflow=5",
        settings.database_url.split("@")[-1] if "@" in settings.database_url else "<configured>",
    )


async def _on_worker_shutdown(ctx: dict) -> None:
    """ARQ on_shutdown hook — dispose the worker's engine + pool. Audit C-F1:
    previously no shutdown handler ran, so SIGTERM left connections dangling
    until Postgres timed them out."""
    try:
        await _engine.dispose()
        logger.info("nomos-worker shutdown — engine pool disposed")
    except Exception:
        logger.exception("nomos-worker shutdown — engine.dispose() failed")


def _parse_valkey_dsn(dsn: str) -> dict[str, str | int]:
    """Parse valkey://host:port into ARQ RedisSettings kwargs.

    Supports valkey:// and redis:// schemes.
    """
    # Strip scheme
    cleaned = dsn
    for scheme in ("valkey://", "redis://"):
        if cleaned.startswith(scheme):
            cleaned = cleaned[len(scheme) :]
            break

    # Split host:port
    if ":" in cleaned:
        host, port_str = cleaned.rsplit(":", 1)
        port = int(port_str.split("/")[0])  # Handle trailing /db
    else:
        host = cleaned.split("/")[0]
        port = 6379

    return {"host": host, "port": port}


try:
    from arq import cron
    from arq.connections import RedisSettings

    _valkey_kwargs = _parse_valkey_dsn(settings.valkey_url)

    class WorkerSettings:
        """ARQ worker configuration — 7 cron jobs on Valkey (5 ops + 2 audit-v2)."""

        redis_settings = RedisSettings(**_valkey_kwargs)  # type: ignore[arg-type]

        functions = [
            retention_cleanup,
            detect_stale_agents,
            check_incident_deadlines,
            expire_approvals,
            process_alerts,
            anchor_audit_heads,
            audit_integrity_checkpoint,
        ]

        cron_jobs = [
            cron(retention_cleanup, hour=3, minute=0),  # type: ignore[arg-type]
            cron(  # type: ignore[arg-type]
                detect_stale_agents,
                minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
            ),
            cron(check_incident_deadlines, minute=0),  # type: ignore[arg-type]
            cron(expire_approvals, minute={0, 10, 20, 30, 40, 50}),  # type: ignore[arg-type]
            cron(process_alerts, minute=set(range(60))),  # type: ignore[arg-type]
            # Phase-A2: anchor every chain head externally once per hour.
            cron(anchor_audit_heads, minute=15),  # type: ignore[arg-type]
            # Phase-A3: daily Article 12 integrity checkpoint at 04:00.
            cron(audit_integrity_checkpoint, hour=4, minute=0),  # type: ignore[arg-type]
        ]

        max_jobs = 7
        job_timeout = 300

        on_startup = _on_worker_startup
        on_shutdown = _on_worker_shutdown

except ImportError:
    # ARQ not installed — worker module can still be imported for testing
    pass
