"""Tests for config startup validation.

K3 regression: dev_mode must NEVER skip validation of jwt_secret /
plugin_api_key, and database_url must not ship working cleartext creds.
"""

from __future__ import annotations

import pytest

from nomos_api.config import (
    _DATABASE_URL_PLACEHOLDER,
    _MIN_SECRET_LENGTH,
    Settings,
    validate_settings,
)

# A valid >=32-char secret usable as both jwt_secret and plugin_api_key.
_GOOD_SECRET = "x" * 40
assert len(_GOOD_SECRET) >= _MIN_SECRET_LENGTH


class TestConfigValidation:
    """Test that insecure defaults are caught at startup."""

    def test_insecure_jwt_default_causes_exit(self):
        s = Settings(
            jwt_secret="change-me-in-production",
            plugin_api_key=_GOOD_SECRET,
            gateway_token="safe-token-12345",
            db_password="safe-password-12345",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_insecure_plugin_key_causes_exit(self):
        s = Settings(
            jwt_secret=_GOOD_SECRET,
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

    def test_safe_values_pass_validation(self):
        # v0.4.0 (M3d): cors_origins with localhost is rejected in production.
        # This regression test must therefore supply a non-localhost origin.
        s = Settings(
            jwt_secret="production-secret-32chars-min!!!!!!!!",
            plugin_api_key="prod-plugin-key-abc123-32chars-min!!!",
            gateway_token="prod-gateway-token-xyz789",
            db_password="strong-db-password-2024",
            cors_origins=["https://app.example.com"],
            dev_mode=False,
        )
        # Should NOT exit
        validate_settings(s)

    def test_cors_localhost_rejected_in_production(self):
        """v0.4.0 (M3d / audit A-#19): production startup must refuse
        ``cors_origins`` that contains a localhost entry. Otherwise an
        allow_credentials=True deployment would accept credentialed
        cross-origin requests from any service on localhost."""
        s = Settings(
            jwt_secret="production-secret-32chars-min!!!!!!!!",
            plugin_api_key="prod-plugin-key-abc123-32chars-min!!!",
            gateway_token="prod-gateway-token-xyz789",
            db_password="strong-db-password-2024",
            cors_origins=["http://localhost:3040", "https://app.example.com"],
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_vault_pending_default_causes_exit(self):
        """vault-pending sentinel must be rejected in production."""
        s = Settings(
            jwt_secret="vault-pending",
            plugin_api_key="vault-pending",
            gateway_token="vault-pending",
            db_password="vault-pending",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_single_vault_pending_field_causes_exit(self):
        """Even one vault-pending field must block startup."""
        s = Settings(
            jwt_secret="vault-pending",
            plugin_api_key=_GOOD_SECRET,
            gateway_token="prod-gateway-token-xyz789",
            db_password="strong-db-password-2024",
            dev_mode=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1


class TestK3DevModeNeverBypassesAuthSecrets:
    """K3: dev_mode must NOT skip validation of jwt_secret / plugin_api_key."""

    def test_dev_mode_still_rejects_vault_pending_jwt_secret(self):
        """The default jwt_secret is 'vault-pending' — must fail even in dev."""
        s = Settings(
            jwt_secret="vault-pending",
            plugin_api_key=_GOOD_SECRET,
            dev_mode=True,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_dev_mode_still_rejects_vault_pending_plugin_key(self):
        s = Settings(
            jwt_secret=_GOOD_SECRET,
            plugin_api_key="vault-pending",
            dev_mode=True,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_dev_mode_still_rejects_empty_jwt_secret(self):
        s = Settings(jwt_secret="", plugin_api_key=_GOOD_SECRET, dev_mode=True)
        with pytest.raises(SystemExit):
            validate_settings(s)

    def test_dev_mode_still_rejects_short_jwt_secret(self):
        """A 31-char jwt_secret must be rejected even in dev_mode."""
        s = Settings(
            jwt_secret="x" * (_MIN_SECRET_LENGTH - 1),
            plugin_api_key=_GOOD_SECRET,
            dev_mode=True,
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_settings(s)
        assert exc_info.value.code == 1

    def test_dev_mode_still_rejects_short_plugin_key(self):
        s = Settings(
            jwt_secret=_GOOD_SECRET,
            plugin_api_key="short-key",
            dev_mode=True,
        )
        with pytest.raises(SystemExit):
            validate_settings(s)

    def test_dev_mode_passes_with_strong_auth_secrets(self):
        """dev_mode may relax gateway_token/db_password, NOT jwt/plugin."""
        s = Settings(
            jwt_secret=_GOOD_SECRET,
            plugin_api_key=_GOOD_SECRET,
            gateway_token="vault-pending",  # relaxed in dev
            db_password="vault-pending",  # relaxed in dev
            dev_mode=True,
        )
        # Should NOT exit — auth secrets strong, only non-security relaxed.
        validate_settings(s)

    def test_class_default_jwt_secret_is_vault_pending_sentinel(self):
        """The Settings class default (ignoring env) is the fail-closed sentinel."""
        # model_fields default, independent of conftest's NOMOS_ env overrides.
        assert Settings.model_fields["jwt_secret"].default == "vault-pending"
        assert Settings.model_fields["plugin_api_key"].default == "vault-pending"


class TestK3DatabaseUrlNoCleartextCreds:
    """K3: database_url default must not embed working cleartext creds."""

    def test_database_url_default_has_no_working_creds(self):
        # The shipped class default (model_fields), independent of any
        # NOMOS_DATABASE_URL env override. CI injects a real Postgres DSN
        # (postgresql+asyncpg://nomos:nomos@...) so the live test DB works;
        # that runtime value must NOT be what this K3 regression inspects.
        # The security property under test is that the *default that ships
        # in code* embeds no working cleartext credentials and fails closed.
        # Mirrors test_class_default_jwt_secret_is_vault_pending_sentinel.
        default_url = Settings.model_fields["database_url"].default
        # No 'nomos:nomos@' working credential pair in the default.
        assert "nomos:nomos@" not in default_url
        assert default_url == _DATABASE_URL_PLACEHOLDER

    def test_placeholder_fails_closed_invalid_host(self):
        """The placeholder points at a non-resolvable host, failing closed."""
        assert "invalid-host" in _DATABASE_URL_PLACEHOLDER
        assert "CONFIGURE_NOMOS_DATABASE_URL" in _DATABASE_URL_PLACEHOLDER
