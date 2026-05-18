"""JSON structured logging formatter for SIEM-compatible log output.

H5 hardening: every formatted message (and serialized exception) is passed
through a redaction step that scrubs token-like patterns and the values of
known secret keys, so raw Vault/LLM-provider exception or response bodies
cannot leak credentials into the structured log stream.
"""

from __future__ import annotations

import json
import logging
import re
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

_REDACTED = "***REDACTED***"

# Keys whose value must never appear in logs. Matches `key=value`,
# `key: value`, `"key": "value"` and `key value` shapes.
_SECRET_KEYS = (
    "jwt_secret",
    "plugin_api_key",
    "gateway_token",
    "db_password",
    "password",
    "recovery_phrase",
    "recovery_key",
    "secret_id",
    "role_id",
    "api_key",
    "openai_api_key",
    "anthropic_api_key",
    "nvidia_api_key",
    "token",
    "authorization",
    "secret",
)

# `secret_key = "value"` / `secret_key: value` / `"secret_key": "value"`
_KV_PATTERN = re.compile(
    r"(?i)(\"?\b(?:" + "|".join(re.escape(k) for k in _SECRET_KEYS) + r")\b\"?\s*[:=]\s*)"
    r"(\"[^\"]*\"|'[^']*'|[^\s,&;}\"']+)"
)

# Bearer tokens in Authorization-style strings.
_BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-]+)")

# Long high-entropy-ish token blobs (JWTs, hex/secret strings) standing alone.
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9._\-]{10,}")
_LONG_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9._\-]{40,}\b")


def redact(text: str) -> str:
    """Scrub secret-looking content from a log string."""
    if not text:
        return text
    # Bearer first: otherwise the `authorization` KV rule would consume the
    # "Bearer" word and leave the actual token in place.
    text = _BEARER_PATTERN.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _KV_PATTERN.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _JWT_PATTERN.sub(_REDACTED, text)
    text = _LONG_TOKEN_PATTERN.sub(_REDACTED, text)
    return text


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Standard fields: timestamp, level, logger, message.
    Extra fields (request_id, method, path, status, duration_ms, user_id,
    agent_id) are included only when present on the LogRecord.
    Exceptions are serialized into an 'exception' string field.
    The message and exception text are redacted (H5).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        for key in _EXTRA_FIELDS:
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = redact(val) if isinstance(val, str) else val
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(log_entry, ensure_ascii=False)
