"""HashiCorp Vault client for NomOS secret management.

Uses AppRole authentication via hvac. Provides in-memory cache fallback
when Vault is unavailable (graceful degradation).
"""

from __future__ import annotations

import logging
from typing import Any

import hvac

logger = logging.getLogger(__name__)


class VaultClient:
    """Vault KV v2 client with AppRole auth and cache fallback."""

    def __init__(
        self,
        addr: str = "http://vault:8200",
        role_id: str = "",
        secret_id: str = "",
        mount: str = "nomos",
    ) -> None:
        self._addr = addr
        self._mount = mount
        self._client: Any = None
        self._connected = False
        self._cache: dict[str, dict[str, Any]] = {}

        if not role_id or not secret_id:
            logger.warning("Vault role_id/secret_id not provided — running without Vault")
            return

        try:
            self._client = hvac.Client(url=addr)
            self._client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            if self._client.is_authenticated():
                self._connected = True
                logger.info("Vault connected via AppRole at %s", addr)
            else:
                logger.warning("Vault AppRole login failed — running without Vault")
        except Exception as exc:
            logger.warning("Vault connection failed: %s — running without Vault", exc)

    @property
    def connected(self) -> bool:
        return self._connected

    def get_secret(self, path: str) -> dict[str, Any] | None:
        """Read secret from Vault KV v2. Falls back to cache on error."""
        if self._client and self._connected:
            try:
                resp = self._client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._mount,
                )
                data = resp["data"]["data"]
                self._cache[path] = data
                return data
            except Exception as exc:
                logger.warning("Vault read failed for %s: %s — using cache", path, exc)

        # Cache fallback
        cached = self._cache.get(path)
        if cached is not None:
            logger.info("Returning cached value for %s", path)
            return cached

        return None

    def put_secret(self, path: str, value: dict[str, Any]) -> bool:
        """Write secret to Vault KV v2."""
        if not self._client or not self._connected:
            return False

        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=value,
                mount_point=self._mount,
            )
            self._cache[path] = value
            return True
        except Exception as exc:
            logger.warning("Vault write failed for %s: %s", path, exc)
            return False

    def list_secrets(self, prefix: str) -> list[str]:
        """List secret keys under a prefix."""
        if not self._client or not self._connected:
            return []

        try:
            resp = self._client.secrets.kv.v2.list_secrets(
                path=prefix,
                mount_point=self._mount,
            )
            return resp["data"]["keys"]
        except Exception as exc:
            logger.warning("Vault list failed for %s: %s", prefix, exc)
            return []

    def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault KV v2."""
        if not self._client or not self._connected:
            return False

        try:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self._mount,
            )
            self._cache.pop(path, None)
            return True
        except Exception as exc:
            logger.warning("Vault delete failed for %s: %s", path, exc)
            return False

    def health_status(self) -> str:
        """Return Vault health: 'healthy', 'degraded', or 'unavailable'."""
        if not self._client:
            return "unavailable"

        try:
            health = self._client.sys.read_health_status(method="GET")
            if hasattr(health, "status_code"):
                # hvac returns a Response object for non-200 codes
                if health.status_code == 200:
                    return "healthy"
                elif health.status_code == 429:
                    return "degraded"  # standby node
                elif health.status_code == 503:
                    return "degraded"  # sealed
                return "unavailable"
            # Dict response = 200 OK
            return "healthy"
        except Exception:
            return "unavailable"
