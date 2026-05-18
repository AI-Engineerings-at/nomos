"""H5 regression: secret-looking values must be redacted in formatted logs."""

from __future__ import annotations

import json
import logging
import sys

from nomos_api.middleware.logging import JSONFormatter, redact

_FAKE_JWT = "eyJhbGciOiJIUzI1Ni9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQabcdef"
_FAKE_KEY = "sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef"


def _fmt(msg: str, *, exc_info=None) -> dict:
    rec = logging.LogRecord(
        name="t", level=logging.WARNING, pathname="", lineno=0,
        msg=msg, args=(), exc_info=exc_info,
    )
    return json.loads(JSONFormatter().format(rec))


class TestRedactHelper:
    def test_kv_secret_is_redacted(self):
        out = redact('jwt_secret=supersecretvalue123')
        assert "supersecretvalue123" not in out
        assert "REDACTED" in out

    def test_quoted_json_secret_is_redacted(self):
        out = redact('{"plugin_api_key": "test-plugin-key-at-least-32-characters"}')
        assert "test-plugin-key-at-least-32-characters" not in out

    def test_bearer_token_is_redacted(self):
        out = redact("Authorization: Bearer abcDEF123ghiJKL456")
        assert "abcDEF123ghiJKL456" not in out
        assert "REDACTED" in out

    def test_jwt_blob_is_redacted(self):
        out = redact(f"token leaked: {_FAKE_JWT}")
        assert _FAKE_JWT not in out

    def test_long_api_key_is_redacted(self):
        out = redact(f"provider said: {_FAKE_KEY}")
        assert _FAKE_KEY not in out

    def test_password_key_is_redacted(self):
        out = redact("password=Hunter2Hunter2")
        assert "Hunter2Hunter2" not in out

    def test_normal_text_untouched(self):
        assert redact("GET /api/health 200") == "GET /api/health 200"


class TestJSONFormatterRedaction:
    def test_message_secret_redacted(self):
        data = _fmt('db_password="MyP@ssw0rdValue"')
        assert "MyP@ssw0rdValue" not in data["message"]

    def test_exception_body_redacted(self):
        try:
            raise ValueError(f"vault rejected token Bearer {_FAKE_KEY}")
        except ValueError:
            data = _fmt("vault error", exc_info=sys.exc_info())
        assert _FAKE_KEY not in data["exception"]
        assert "ValueError" in data["exception"]

    def test_clean_message_still_works(self):
        data = _fmt("count: 42")
        assert data["message"] == "count: 42"
        assert data["level"] == "WARNING"
