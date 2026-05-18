"""Structured JSON logging for the NomOS CLI.

The CLI emits two distinct output streams:

* **User-facing UX** — rendered via ``rich`` / ``click.echo`` to *stdout*.
  This is unchanged and is what users and tests depend on.
* **Diagnostics** — structured JSON log records written to *stderr* for
  operators, log shippers and SIEM ingestion. This module owns that stream.

The JSON record shape is intentionally consistent with the nomos-api
``JSONFormatter`` (``nomos-api/nomos_api/middleware/logging.py``): the
standard fields are ``timestamp`` (UTC ISO-8601), ``level``, ``logger`` and
``message``; exceptions are serialized into an ``exception`` string field.

Log verbosity is controlled by the ``NOMOS_LOG_LEVEL`` environment variable
(case-insensitive). Accepted values: ``DEBUG``, ``INFO``, ``WARNING``,
``ERROR``. Anything else (or unset) falls back to ``INFO``; an invalid value
additionally emits a one-time warning on the configured logger.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

LOGGER_NAME = "nomos.cli"

_DEFAULT_LEVEL = "INFO"
_VALID_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def resolve_level(raw: str | None) -> tuple[int, bool]:
    """Resolve a raw ``NOMOS_LOG_LEVEL`` value to a logging level.

    Returns a ``(level, invalid)`` tuple. ``invalid`` is ``True`` when a
    non-empty value was given that did not match a known level — in that
    case the level falls back to ``INFO`` and the caller should warn.
    """
    if raw is None or raw.strip() == "":
        return _VALID_LEVELS[_DEFAULT_LEVEL], False
    normalized = raw.strip().upper()
    if normalized in _VALID_LEVELS:
        return _VALID_LEVELS[normalized], False
    return _VALID_LEVELS[_DEFAULT_LEVEL], True


class JSONFormatter(logging.Formatter):
    """Format CLI log records as single-line JSON objects.

    Field shape mirrors ``nomos_api.middleware.logging.JSONFormatter``:
    ``timestamp``, ``level``, ``logger``, ``message`` always; ``exception``
    only when exception info is attached to the record.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(level_env: str | None = None) -> logging.Logger:
    """Configure and return the CLI diagnostics logger.

    Idempotent: repeated calls reconfigure the level and reuse a single
    JSON ``StreamHandler`` on *stderr* so user-facing stdout stays clean.

    ``level_env`` defaults to ``os.environ['NOMOS_LOG_LEVEL']`` when not
    explicitly passed (explicit argument wins, mainly for tests).
    """
    raw = level_env if level_env is not None else os.environ.get("NOMOS_LOG_LEVEL")
    level, invalid = resolve_level(raw)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    # Drop any prior JSON handler and attach a fresh one bound to the
    # current sys.stderr. Recreating (rather than reusing) avoids flushing
    # a stale/closed stream and guarantees no duplicate handlers stack.
    for existing in list(logger.handlers):
        if getattr(existing, "_nomos_json", False):
            logger.removeHandler(existing)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler._nomos_json = True  # type: ignore[attr-defined]
    handler.setFormatter(JSONFormatter())
    handler.setLevel(level)
    logger.addHandler(handler)

    if invalid:
        logger.warning(
            "Invalid NOMOS_LOG_LEVEL=%r — falling back to %s", raw, _DEFAULT_LEVEL
        )
    return logger


def get_logger() -> logging.Logger:
    """Return the shared CLI diagnostics logger (configuring on first use)."""
    logger = logging.getLogger(LOGGER_NAME)
    if not any(getattr(h, "_nomos_json", False) for h in logger.handlers):
        return configure_logging()
    return logger
