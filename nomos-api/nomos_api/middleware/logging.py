"""JSON structured logging formatter for SIEM-compatible log output."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

_EXTRA_FIELDS: tuple[str, ...] = (
    "request_id",
    "method",
    "path",
    "status",
    "duration_ms",
    "user_id",
    "agent_id",
)


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Standard fields: timestamp, level, logger, message.
    Extra fields (request_id, method, path, status, duration_ms, user_id,
    agent_id) are included only when present on the LogRecord.
    Exceptions are serialized into an 'exception' string field.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _EXTRA_FIELDS:
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)
