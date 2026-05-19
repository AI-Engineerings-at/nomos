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

# JWTs by their unmistakable `eyJ` (base64 of `{"`) prefix.
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9._\-]{10,}")

# Known provider API key prefixes — narrowly targeted so we don't redact
# legitimate observability data (long agent IDs, file paths, stack-trace
# symbol paths) the way a blanket "40+ alphanumeric" rule did (H3
# post-judgment-day finding). Add new patterns here when adopting new
# providers rather than broadening into a catch-all.
_PROVIDER_KEY_PATTERN = re.compile(
    r"\b(?:sk-(?:proj-|svcacct-|live-|test-)?[A-Za-z0-9_-]{16,}"
    r"|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|nvapi-[A-Za-z0-9_-]{20,}|xox[bpors]-[A-Za-z0-9-]{20,}"
    r"|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|hf_[A-Za-z0-9]{20,}"
    r"|AIza[0-9A-Za-z_-]{20,})\b"
)


def redact(text: str) -> str:
    """Scrub secret-looking content from a log string.

    Order matters:
    1. Bearer first — otherwise the `authorization` KV rule would consume
       the "Bearer" keyword and leave the actual token in place.
    2. KV (key=value / key: value / 'key': 'value') for known secret keys —
       catches dict-repr and exception messages that include secret values.
    3. JWT by `eyJ` prefix (unmistakable).
    4. Provider API keys by known prefixes (sk-, ghp_, nvapi-, AKIA, ...).

    NOT included by design: a generic "long alphanumeric blob" pattern —
    that destroyed observability (paths, UUIDs, hashes, agent IDs) far
    more often than it caught real secrets.
    """
    if not text:
        return text
    text = _BEARER_PATTERN.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _KV_PATTERN.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _JWT_PATTERN.sub(_REDACTED, text)
    text = _PROVIDER_KEY_PATTERN.sub(_REDACTED, text)
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
