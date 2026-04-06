"""Tests for JSON structured logging formatter."""

import json
import logging
import sys

from nomos_api.middleware.logging import JSONFormatter


class TestJSONFormatter:
    def test_basic_format(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "hello"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_extra_fields(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"  # type: ignore[attr-defined]
        record.method = "GET"  # type: ignore[attr-defined]
        record.path = "/health"  # type: ignore[attr-defined]
        record.status = 200  # type: ignore[attr-defined]
        record.duration_ms = 12.5  # type: ignore[attr-defined]
        output = formatter.format(record)
        data = json.loads(output)
        assert data["request_id"] == "req-123"
        assert data["method"] == "GET"
        assert data["path"] == "/health"
        assert data["status"] == 200
        assert data["duration_ms"] == 12.5

    def test_exception_included(self) -> None:
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="failed",
                args=(),
                exc_info=exc_info,
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "test error" in data["exception"]

    def test_no_extra_fields_when_absent(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="simple warning",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "request_id" not in data
        assert "method" not in data
        assert "path" not in data
        assert "status" not in data
        assert "duration_ms" not in data
        assert "user_id" not in data
        assert "agent_id" not in data

    def test_message_with_args(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="count: %d",
            args=(42,),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "count: 42"

    def test_output_is_valid_json_single_line(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="line check",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        # Must be a single line (no embedded newlines outside JSON string values)
        assert "\n" not in output
        # Must be parseable
        json.loads(output)
