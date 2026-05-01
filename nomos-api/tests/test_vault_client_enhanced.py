"""Tests for Vault client with improved error handling."""

import pytest
from unittest.mock import Mock, patch
from nomos_api.vault_client import (
    VaultClient,
    VaultError,
    VaultConnectionError,
    VaultAuthError,
    VaultNotReadyError,
    VaultSecretNotFoundError,
)


@pytest.fixture
def mock_hvac_client():
    """Fixture for mock HVAC client."""
    mock_client = Mock()
    mock_client.auth.approle.login.return_value = None
    mock_client.is_authenticated.return_value = True
    mock_client.sys.read_health_status.return_value = {"initialized": True, "sealed": False}
    return mock_client


def test_vault_client_initialization_success(mock_hvac_client):
    """Test successful Vault client initialization."""
    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        assert client.connected is True


def test_vault_client_initialization_failure():
    """Test Vault client initialization failure."""
    with patch("nomos_api.vault_client.hvac.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.auth.approle.login.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        assert client.connected is False


def test_vault_client_missing_credentials():
    """Test Vault client with missing credentials."""
    client = VaultClient(addr="http://vault:8200", role_id="", secret_id="")
    assert client.connected is False


def test_get_secret_success(mock_hvac_client):
    """Test successful secret retrieval."""
    mock_response = {"data": {"data": {"key": "value"}}}
    mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = mock_response

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        result = client.get_secret("secrets/test")
        assert result == {"key": "value"}


def test_get_secret_not_found(mock_hvac_client):
    """Test handling of missing secret."""
    mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = None

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        with pytest.raises(VaultSecretNotFoundError):
            client.get_secret("secrets/nonexistent")


def test_get_secret_with_cache_fallback(mock_hvac_client):
    """Test cache fallback when Vault fails."""
    # First, populate cache
    mock_response = {"data": {"data": {"key": "cached_value"}}}
    mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = mock_response

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        # Populate cache
        client.get_secret("secrets/test")

        # Now simulate Vault failure
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault unavailable")

        # Should return cached value
        result = client.get_secret("secrets/test")
        assert result == {"key": "cached_value"}


def test_put_secret_success(mock_hvac_client):
    """Test successful secret storage."""
    mock_hvac_client.secrets.kv.v2.create_or_update_secret.return_value = True

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        result = client.put_secret("secrets/test", {"key": "value"})
        assert result is True


def test_put_secret_failure(mock_hvac_client):
    """Test failed secret storage."""
    mock_hvac_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception("Write failed")

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        result = client.put_secret("secrets/test", {"key": "value"})
        assert result is False


def test_health_status_healthy(mock_hvac_client):
    """Test healthy Vault status."""
    mock_hvac_client.sys.read_health_status.return_value = {"initialized": True, "sealed": False}

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        status = client.health_status()
        assert status == "healthy"


def test_health_status_degraded(mock_hvac_client):
    """Test degraded Vault status."""
    mock_response = Mock()
    mock_response.status_code = 429  # Standby node
    mock_hvac_client.sys.read_health_status.return_value = mock_response

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        status = client.health_status()
        assert status == "degraded"


def test_health_status_unavailable(mock_hvac_client):
    """Test unavailable Vault status."""
    mock_hvac_client.sys.read_health_status.side_effect = Exception("Connection failed")

    with patch("nomos_api.vault_client.hvac.Client", return_value=mock_hvac_client):
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret")
        status = client.health_status()
        assert status == "unavailable"


def test_error_classes():
    """Test custom error classes."""
    assert issubclass(VaultConnectionError, VaultError)
    assert issubclass(VaultAuthError, VaultError)
    assert issubclass(VaultNotReadyError, VaultError)
    assert issubclass(VaultSecretNotFoundError, VaultError)


def test_disconnected_client_behavior():
    """Test behavior when Vault is disconnected."""
    client = VaultClient(addr="http://vault:8200", role_id="", secret_id="")

    # Should return None for get_secret
    result = client.get_secret("secrets/test")
    assert result is None

    # Should return False for put_secret
    result = client.put_secret("secrets/test", {"key": "value"})
    assert result is False

    # Should return empty list for list_secrets
    result = client.list_secrets("secrets/")
    assert result == []

    # Should return False for delete_secret
    result = client.delete_secret("secrets/test")
    assert result is False

    # Should return unavailable for health_status
    status = client.health_status()
    assert status == "unavailable"


def test_cache_ttl_behavior():
    """Test cache TTL behavior."""
    import time

    mock_response = {"data": {"data": {"key": "value"}}}

    with patch("nomos_api.vault_client.hvac.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.auth.approle.login.return_value = None
        mock_client.is_authenticated.return_value = True
        mock_client.sys.read_health_status.return_value = {"initialized": True, "sealed": False}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create client with short TTL
        client = VaultClient(addr="http://vault:8200", role_id="test-role", secret_id="test-secret", cache_ttl=1.0)

        # First call - should hit Vault
        result1 = client.get_secret("secrets/test")
        assert result1 == {"key": "value"}

        # Second call within TTL - should hit cache
        result2 = client.get_secret("secrets/test")
        assert result2 == {"key": "value"}

        # Wait for TTL to expire
        time.sleep(1.1)

        # Third call after TTL - should hit Vault again
        result3 = client.get_secret("secrets/test")
        assert result3 == {"key": "value"}
