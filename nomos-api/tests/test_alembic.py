"""Tests for Alembic migration infrastructure."""

from __future__ import annotations

import configparser
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

NOMOS_API_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = NOMOS_API_DIR / "alembic.ini"
ALEMBIC_DIR = NOMOS_API_DIR / "alembic"
VERSIONS_DIR = ALEMBIC_DIR / "versions"


class TestAlembicConfig:
    """alembic.ini exists and is correctly configured."""

    def test_alembic_ini_exists(self) -> None:
        assert ALEMBIC_INI.exists(), "alembic.ini must exist in nomos-api root"

    def test_alembic_ini_parsable(self) -> None:
        parser = configparser.ConfigParser()
        read_files = parser.read(str(ALEMBIC_INI))
        assert len(read_files) == 1, "alembic.ini must be parsable by configparser"
        assert parser.has_section("alembic"), "alembic.ini must have [alembic] section"

    def test_no_hardcoded_database_url(self) -> None:
        content = ALEMBIC_INI.read_text()
        assert "postgresql://" not in content, "alembic.ini must not contain hardcoded postgresql:// URL"
        assert "asyncpg://" not in content, "alembic.ini must not contain hardcoded asyncpg:// URL"
        assert "sqlite://" not in content, "alembic.ini must not contain hardcoded sqlite:// URL"

    def test_script_location_set(self) -> None:
        parser = configparser.ConfigParser()
        parser.read(str(ALEMBIC_INI))
        assert parser.get("alembic", "script_location") == "alembic"


class TestAlembicStructure:
    """Alembic directory structure is correct."""

    def test_env_py_exists(self) -> None:
        assert (ALEMBIC_DIR / "env.py").exists()

    def test_script_mako_exists(self) -> None:
        assert (ALEMBIC_DIR / "script.py.mako").exists()

    def test_versions_dir_exists(self) -> None:
        assert VERSIONS_DIR.is_dir()


class TestMigrationHistory:
    """Migration history is linear and complete."""

    def test_history_is_linear(self) -> None:
        """No branch points in migration history."""
        cfg = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(cfg)
        heads = script.get_heads()
        assert len(heads) == 1, f"Migration history must be linear, found {len(heads)} heads: {heads}"

    def test_initial_migration_exists(self) -> None:
        """At least one migration revision exists."""
        cfg = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(cfg)
        revisions = list(script.walk_revisions())
        assert len(revisions) >= 1, "At least the initial migration must exist"

    def test_all_models_covered_in_initial_migration(self) -> None:
        """The initial migration creates all tables defined in models.py."""
        from nomos_api.models import Base

        model_tables = set(Base.metadata.tables.keys())
        assert len(model_tables) >= 9, f"Expected at least 9 tables in models, found {len(model_tables)}"

        # Read the initial migration and verify it references all tables
        migration_files = sorted(VERSIONS_DIR.glob("*.py"))
        assert len(migration_files) >= 1, "No migration files found"

        initial_migration = migration_files[0].read_text()
        for table_name in model_tables:
            assert table_name in initial_migration, (
                f"Table '{table_name}' from models.py not found in initial migration"
            )


class TestMainNoCreateAll:
    """main.py must not use Base.metadata.create_all."""

    def test_no_create_all_in_main(self) -> None:
        main_py = NOMOS_API_DIR / "nomos_api" / "main.py"
        content = main_py.read_text()
        assert "create_all" not in content, "main.py must use Alembic migrations, not create_all"
