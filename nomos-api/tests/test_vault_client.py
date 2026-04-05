"""Tests for VaultClient — with and without Vault connection."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from nomos_api.vault_client import VaultClient


class TestVaultClientWithoutVault:
    """Tests when no credentials are provided."""

    def test_not_connected_without_credentials(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.connected is False

    def test_get_returns_none(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.get_secret("any/path") is None

    def test_put_returns_false(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.put_secret("any/path", {"key": "val"}) is False

    def test_list_returns_empty(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.list_secrets("prefix") == []

    def test_delete_returns_false(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.delete_secret("any/path") is False

    def test_health_unavailable(self):
        client = VaultClient(role_id="", secret_id="")
        assert client.health_status() == "unavailable"

    def test_cache_fallback_works(self):
        client = VaultClient(role_id="", secret_id="")
        # Manually populate cache with (data, timestamp) tuple.
        client._cache["test/secret"] = ({"username": "admin"}, time.time())
        result = client.get_secret("test/secret")
        assert result == {"username": "admin"}


class TestVaultClientWithMock:
    """Tests with mocked hvac.Client."""

    @patch("nomos_api.vault_client.hvac")
    def test_connected_after_login(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(
            addr="http://vault:8200",
            role_id="test-role",
            secret_id="test-secret",
        )
        assert client.connected is True
        mock_client.auth.approle.login.assert_called_once_with(role_id="test-role", secret_id="test-secret")

    @patch("nomos_api.vault_client.hvac")
    def test_get_reads_from_vault_and_caches(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {"password": "s3cret"}}}
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(role_id="r", secret_id="s")
        result = client.get_secret("db/creds")

        assert result == {"password": "s3cret"}
        cached_data, cached_ts = client._cache["db/creds"]
        assert cached_data == {"password": "s3cret"}
        assert cached_ts > 0

    @patch("nomos_api.vault_client.hvac")
    def test_put_writes_to_vault(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(role_id="r", secret_id="s")
        result = client.put_secret("db/creds", {"password": "new"})

        assert result is True
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()

    @patch("nomos_api.vault_client.hvac")
    def test_cache_fallback_on_read_error(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("timeout")
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(role_id="r", secret_id="s")
        # Pre-populate cache with (data, timestamp) tuple; timestamp in past to ensure
        # TTL is not fresh — error path must return stale cache regardless of TTL.
        client._cache["db/creds"] = ({"password": "cached"}, 0.0)

        result = client.get_secret("db/creds")
        assert result == {"password": "cached"}

    @patch("nomos_api.vault_client.hvac")
    def test_health_healthy(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.sys.read_health_status.return_value = {"initialized": True, "sealed": False}
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(role_id="r", secret_id="s")
        assert client.health_status() == "healthy"

    @patch("nomos_api.vault_client.hvac")
    def test_health_unavailable_on_exception(self, mock_hvac):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.sys.read_health_status.side_effect = Exception("down")
        mock_hvac.Client.return_value = mock_client

        client = VaultClient(role_id="r", secret_id="s")
        assert client.health_status() == "unavailable"
