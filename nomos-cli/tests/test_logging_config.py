"""Tests for nomos.logging_config — structured JSON CLI diagnostics.

Covers: NOMOS_LOG_LEVEL resolution (incl. case-insensitivity and
invalid → INFO fallback with a warning), JSON record shape, default
level INFO, and that the CLI entrypoint wires logging without
disturbing user-facing stdout.
"""

from __future__ import annotations

import json
import logging

import pytest
from click.testing import CliRunner

from nomos.cli import main
from nomos.logging_config import (
    LOGGER_NAME,
    JSONFormatter,
    configure_logging,
    get_logger,
    resolve_level,
)


# ── resolve_level ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected_level", "expected_invalid"),
    [
        (None, logging.INFO, False),
        ("", logging.INFO, False),
        ("   ", logging.INFO, False),
        ("DEBUG", logging.DEBUG, False),
        ("debug", logging.DEBUG, False),
        ("  Info  ", logging.INFO, False),
        ("WARNING", logging.WARNING, False),
        ("error", logging.ERROR, False),
        ("TRACE", logging.INFO, True),
        ("loud", logging.INFO, True),
    ],
)
def test_resolve_level(raw, expected_level, expected_invalid) -> None:
    level, invalid = resolve_level(raw)
    assert level == expected_level
    assert invalid is expected_invalid


# ── configure_logging: env handling ──────────────────────────────────────


def test_default_level_is_info(monkeypatch) -> None:
    monkeypatch.delenv("NOMOS_LOG_LEVEL", raising=False)
    logger = configure_logging()
    assert logger.level == logging.INFO


def test_env_var_respected(monkeypatch) -> None:
    monkeypatch.setenv("NOMOS_LOG_LEVEL", "debug")
    logger = configure_logging()
    assert logger.level == logging.DEBUG


def test_invalid_env_falls_back_to_info_and_warns(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NOMOS_LOG_LEVEL", "bogus")
    logger = configure_logging()
    captured = capsys.readouterr()
    assert logger.level == logging.INFO
    # Logger does not propagate; the warning is emitted on its JSON stderr
    # handler. Assert on the structured record.
    payload = json.loads(captured.err.strip().splitlines()[-1])
    assert payload["level"] == "WARNING"
    assert "Invalid NOMOS_LOG_LEVEL" in payload["message"]


def test_explicit_arg_overrides_env(monkeypatch) -> None:
    monkeypatch.setenv("NOMOS_LOG_LEVEL", "ERROR")
    logger = configure_logging(level_env="DEBUG")
    assert logger.level == logging.DEBUG


def test_get_logger_returns_configured_logger() -> None:
    logger = get_logger()
    assert logger.name == LOGGER_NAME
    assert any(getattr(h, "_nomos_json", False) for h in logger.handlers)


def test_idempotent_no_duplicate_handlers() -> None:
    configure_logging()
    configure_logging()
    logger = logging.getLogger(LOGGER_NAME)
    json_handlers = [h for h in logger.handlers if getattr(h, "_nomos_json", False)]
    assert len(json_handlers) == 1


# ── JSON output shape ────────────────────────────────────────────────────


def test_formatter_emits_expected_keys() -> None:
    record = logging.LogRecord(
        name="nomos.cli",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    payload = json.loads(JSONFormatter().format(record))
    assert set(payload) == {"timestamp", "level", "logger", "message"}
    assert payload["level"] == "INFO"
    assert payload["logger"] == "nomos.cli"
    assert payload["message"] == "hello world"
    assert payload["timestamp"].endswith("+00:00")


def test_formatter_serializes_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="nomos.cli",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="failed",
            args=(),
            exc_info=sys.exc_info(),
        )
    payload = json.loads(JSONFormatter().format(record))
    assert "exception" in payload
    assert "ValueError: boom" in payload["exception"]


def test_logger_emits_json_to_stderr(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NOMOS_LOG_LEVEL", "INFO")
    logger = configure_logging()
    logger.info("structured diagnostic %d", 42)
    captured = capsys.readouterr()
    assert captured.out == ""  # user-facing stdout untouched
    payload = json.loads(captured.err.strip().splitlines()[-1])
    assert payload["message"] == "structured diagnostic 42"
    assert payload["level"] == "INFO"


# ── CLI entrypoint wiring ────────────────────────────────────────────────


def test_cli_entrypoint_keeps_stdout_clean(monkeypatch) -> None:
    """--help (UX output) must not be polluted by JSON log lines."""
    monkeypatch.setenv("NOMOS_LOG_LEVEL", "DEBUG")
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "NomOS" in result.output
    assert '"logger": "nomos.cli"' not in result.output
