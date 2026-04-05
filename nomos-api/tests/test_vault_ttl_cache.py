"""Tests for VaultClient TTL cache behavior."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from nomos_api.vault_client import VaultClient


class TestTTLCache:
    def _make_client(self) -> tuple[VaultClient, MagicMock]:
        with patch("nomos_api.vault_client.hvac.Client") as mock_cls:
            mock_hvac = MagicMock()
            mock_cls.return_value = mock_hvac
            mock_hvac.is_authenticated.return_value = True
            client = VaultClient(
                addr="http://vault:8200",
                role_id="test",
                secret_id="test",
                cache_ttl=0.5,  # 500ms for fast tests
            )
            return client, mock_hvac

    def test_cache_hit_within_ttl(self) -> None:
        client, mock = self._make_client()
        mock.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {"key": "value"}}}
        result1 = client.get_secret("test/path")
        assert result1 == {"key": "value"}
        mock.secrets.kv.v2.read_secret_version.reset_mock()
        result2 = client.get_secret("test/path")
        assert result2 == {"key": "value"}
        mock.secrets.kv.v2.read_secret_version.assert_not_called()

    def test_cache_miss_after_ttl(self) -> None:
        client, mock = self._make_client()
        mock.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {"key": "old"}}}
        client.get_secret("test/path")
        time.sleep(0.6)
        mock.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {"key": "new"}}}
        result = client.get_secret("test/path")
        assert result == {"key": "new"}

    def test_fallback_on_error_uses_stale_cache(self) -> None:
        client, mock = self._make_client()
        mock.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {"key": "cached"}}}
        client.get_secret("test/path")
        time.sleep(0.6)  # TTL expired
        mock.secrets.kv.v2.read_secret_version.side_effect = Exception("vault down")
        result = client.get_secret("test/path")
        assert result == {"key": "cached"}  # Stale cache returned
