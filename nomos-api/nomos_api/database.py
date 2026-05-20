"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.config import settings

# M4 (0.3.0, audit D-#15): explicit pool sizing + connect timeout.
# Previously the engine used SQLAlchemy defaults (pool_size=5,
# max_overflow=10, no connect_timeout) which let one slow query take
# the entire app down by exhausting the pool and waiting indefinitely
# for new connections.
#
# 20+10 is a sensible baseline for a FastAPI + Postgres deployment;
# operators on big stacks can override via NOMOS_DB_* env vars
# (TODO v0.4.0: surface as settings).
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an async database session."""
    async with async_session() as session:
        yield session
