"""Tests for config startup validation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from nomos_api.config import Settings, validate_settings


class TestConfigValidation:
    """Test that insecure defaults are caught at startup."""

    def test_insecure_jwt_default_causes_exit(self):
        s = Settings(
            jwt_secret="change-me-in-production",
            plugin_api_key="safe-key-12345",
            gateway_token="safe-token-12345",
            db_password="safe-password-12345",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_insecure_plugin_key_causes_exit(self):
        s = Settings(
            jwt_secret="safe-jwt-secret-12345",
            plugin_api_key="nomos-plugin-dev",
            gateway_token="safe-token-12345",
            db_password="safe-password-12345",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_all_insecure_defaults_cause_exit(self):
        s = Settings(
            jwt_secret="change-me-in-production",
            plugin_api_key="nomos-plugin-dev",
            gateway_token="nomos-dev-token",
            db_password="nomos",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_dev_mode_skips_validation(self):
        s = Settings(dev_mode=True)
        # Should NOT exit — dev_mode bypasses validation
        validate_settings(s)

    def test_safe_values_pass_validation(self):
        s = Settings(
            jwt_secret="production-secret-32chars-min!!!!",
            plugin_api_key="prod-plugin-key-abc123",
            gateway_token="prod-gateway-token-xyz789",
            db_password="strong-db-password-2024",
            dev_mode=False,
        )
        # Should NOT exit
        validate_settings(s)
