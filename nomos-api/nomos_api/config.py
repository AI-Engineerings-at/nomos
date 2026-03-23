"""NomOS API configuration — all settings from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API settings. All configurable via NOMOS_ prefixed env vars."""

    database_url: str = "postgresql+asyncpg://nomos:nomos@localhost:5432/nomos"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "NomOS Fleet API"
    api_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3040"]
    agents_dir: Path = Path("./data/agents")

    model_config = {"env_prefix": "NOMOS_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
