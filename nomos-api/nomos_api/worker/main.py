"""ARQ Worker Settings — connects to Valkey, schedules cron jobs.

Run with: python -m arq nomos_api.worker.main.WorkerSettings
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.config import settings
from nomos_api.worker.jobs.alerts import process_alerts
from nomos_api.worker.jobs.approvals import expire_approvals
from nomos_api.worker.jobs.heartbeat import detect_stale_agents
from nomos_api.worker.jobs.incidents import check_incident_deadlines
from nomos_api.worker.jobs.retention import retention_cleanup

# Module-level session factory — shared by all jobs in this worker process.
# Separate from the API's request-scoped sessions.
_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


def get_session_factory() -> async_sessionmaker:
    """Return the worker's session factory. Used by jobs when no override is given."""
    return _session_factory


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
        """ARQ worker configuration — 5 cron jobs on Valkey."""

        redis_settings = RedisSettings(**_valkey_kwargs)  # type: ignore[arg-type]

        functions = [
            retention_cleanup,
            detect_stale_agents,
            check_incident_deadlines,
            expire_approvals,
            process_alerts,
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
        ]

        max_jobs = 5
        job_timeout = 300

except ImportError:
    # ARQ not installed — worker module can still be imported for testing
    pass
