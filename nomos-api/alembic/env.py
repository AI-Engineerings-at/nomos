"""Alembic environment — async migration runner.

Loads database_url from nomos_api.config so no credentials are hardcoded.
Uses async engine because NomOS runs on asyncpg.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from nomos_api.config import settings
from nomos_api.models import Base

# Alembic Config object for .ini access
config = context.config

# Set the SQLAlchemy URL from application config (never hardcoded)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Standard Python logging from alembic.ini — DISABLED.
# In a long-running uvicorn process (lifespan startup migrations),
# alembic.fileConfig() would overwrite the app's JSON-to-stdout root
# handler with alembic.ini's plain `[handler_console]` formatter, and
# subsequent per-request logs would never reach docker stdout. The app
# configures logging itself (nomos_api.main._force_json_stdout_logging);
# alembic uses whatever the host process has set up. Stand-alone
# alembic CLI usage still gets the basicConfig fallback below.
if config.config_file_name is not None and config.attributes.get("configure_logger") is True:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure context with a live connection and run migrations."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — against a live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
