"""Tests for vault_source.py — AppRole file reading and VAULT_FIELD_MAP."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestReadCredsFromFile:
    """Test _read_creds_from_file reads AppRole credentials from shared volume."""

    def test_reads_valid_creds_file(self, tmp_path):
        creds_file = tmp_path / "approle-creds.env"
        creds_file.write_text("VAULT_ROLE_ID=test-role-123\nVAULT_SECRET_ID=test-secret-456\n")

        from nomos_api.vault_source import _read_creds_from_file

        role_id, secret_id = _read_creds_from_file(str(creds_file))
        assert role_id == "test-role-123"
        assert secret_id == "test-secret-456"

    def test_returns_empty_strings_when_file_missing(self):
        from nomos_api.vault_source import _read_creds_from_file

        role_id, secret_id = _read_creds_from_file("/nonexistent/path/creds.env")
        assert role_id == ""
        assert secret_id == ""

    def test_ignores_comments_and_blank_lines(self, tmp_path):
        creds_file = tmp_path / "approle-creds.env"
        creds_file.write_text(
            "# This is a comment\n\nVAULT_ROLE_ID=role-abc\n# Another comment\nVAULT_SECRET_ID=secret-xyz\n"
        )

        from nomos_api.vault_source import _read_creds_from_file

        role_id, secret_id = _read_creds_from_file(str(creds_file))
        assert role_id == "role-abc"
        assert secret_id == "secret-xyz"

    def test_handles_extra_keys_gracefully(self, tmp_path):
        creds_file = tmp_path / "approle-creds.env"
        creds_file.write_text("VAULT_ROLE_ID=role-123\nVAULT_SECRET_ID=secret-456\nSOME_OTHER_KEY=ignored\n")

        from nomos_api.vault_source import _read_creds_from_file

        role_id, secret_id = _read_creds_from_file(str(creds_file))
        assert role_id == "role-123"
        assert secret_id == "secret-456"

    def test_returns_empty_when_keys_missing(self, tmp_path):
        creds_file = tmp_path / "approle-creds.env"
        creds_file.write_text("SOMETHING_ELSE=value\n")

        from nomos_api.vault_source import _read_creds_from_file

        role_id, secret_id = _read_creds_from_file(str(creds_file))
        assert role_id == ""
        assert secret_id == ""


class TestVaultFieldMap:
    """Test VAULT_FIELD_MAP matches init-entrypoint.sh paths."""

    def test_jwt_secret_maps_to_secrets_system(self):
        from nomos_api.vault_source import VAULT_FIELD_MAP

        path, key = VAULT_FIELD_MAP["jwt_secret"]
        assert path == "secrets/system"
        assert key == "jwt_secret"

    def test_plugin_api_key_maps_to_secrets_system(self):
        from nomos_api.vault_source import VAULT_FIELD_MAP

        path, key = VAULT_FIELD_MAP["plugin_api_key"]
        assert path == "secrets/system"
        assert key == "plugin_api_key"

    def test_gateway_token_maps_to_secrets_system(self):
        from nomos_api.vault_source import VAULT_FIELD_MAP

        path, key = VAULT_FIELD_MAP["gateway_token"]
        assert path == "secrets/system"
        assert key == "gateway_token"

    def test_db_password_maps_to_secrets_database(self):
        from nomos_api.vault_source import VAULT_FIELD_MAP

        path, key = VAULT_FIELD_MAP["db_password"]
        assert path == "secrets/database"
        assert key == "password"

    def test_llm_api_key_maps_to_secrets_llm_keys(self):
        from nomos_api.vault_source import VAULT_FIELD_MAP

        path, key = VAULT_FIELD_MAP["llm_api_key"]
        assert path == "secrets/llm_keys"
        assert key == "nvidia_api_key"


class TestGetVaultClientFileFirst:
    """Test _get_vault_client reads creds from file first, then ENV."""

    def test_uses_file_creds_when_available(self, tmp_path):
        """When approle-creds.env exists, use those credentials."""
        import nomos_api.vault_source as vs

        # Reset singleton
        vs._vault_client_instance = None

        creds_file = tmp_path / "approle-creds.env"
        creds_file.write_text("VAULT_ROLE_ID=file-role\nVAULT_SECRET_ID=file-secret\n")

        with (
            patch.object(vs, "APPROLE_CREDS_PATH", str(creds_file)),
            patch("nomos_api.vault_client.VaultClient") as mock_vc_cls,
            patch.dict("os.environ", {"VAULT_ROLE_ID": "env-role", "VAULT_SECRET_ID": "env-secret"}),
        ):
            mock_vc_cls.return_value = MagicMock()
            vs._vault_client_instance = None
            vs._get_vault_client()

            # Should use file creds, not ENV
            call_kwargs = mock_vc_cls.call_args[1]
            assert call_kwargs["role_id"] == "file-role"
            assert call_kwargs["secret_id"] == "file-secret"

        # Clean up singleton
        vs._vault_client_instance = None

    def test_falls_back_to_env_when_file_missing(self):
        """When approle-creds.env does not exist, fallback to ENV."""
        import nomos_api.vault_source as vs

        vs._vault_client_instance = None

        with (
            patch.object(vs, "APPROLE_CREDS_PATH", "/nonexistent/path"),
            patch("nomos_api.vault_client.VaultClient") as mock_vc_cls,
            patch.dict(
                "os.environ",
                {"VAULT_ROLE_ID": "env-role-fallback", "VAULT_SECRET_ID": "env-secret-fallback"},
            ),
        ):
            mock_vc_cls.return_value = MagicMock()
            vs._vault_client_instance = None
            vs._get_vault_client()

            call_kwargs = mock_vc_cls.call_args[1]
            assert call_kwargs["role_id"] == "env-role-fallback"
            assert call_kwargs["secret_id"] == "env-secret-fallback"

        vs._vault_client_instance = None
