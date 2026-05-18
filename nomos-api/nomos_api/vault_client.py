"""HashiCorp Vault client for NomOS secret management.

Uses AppRole authentication via hvac. Provides in-memory TTL cache to reduce
Vault load and graceful degradation (stale cache) when Vault is unavailable.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import hvac

logger = logging.getLogger(__name__)


class VaultError(Exception):
    """Base class for Vault-related errors."""

    pass


class VaultConnectionError(VaultError):
    """Vault connection failed."""

    pass


class VaultAuthError(VaultError):
    """Vault authentication failed."""

    pass


class VaultNotReadyError(VaultError):
    """Vault is not ready (sealed/uninitialized)."""

    pass


class VaultSecretNotFoundError(VaultError):
    """Requested secret not found in Vault."""

    pass


class VaultClient:
    """Vault KV v2 client with AppRole auth and cache fallback."""

    def __init__(
        self,
        addr: str = "http://vault:8200",
        role_id: str = "",
        secret_id: str = "",
        mount: str = "nomos",
        cache_ttl: float = 60.0,
    ) -> None:
        self._addr = addr
        self._mount = mount
        self._cache_ttl = cache_ttl
        self._client: Any = None
        self._connected = False
        # Cache stores (data, timestamp) tuples for TTL tracking.
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

        if not role_id or not secret_id:
            logger.warning("Vault role_id/secret_id not provided — running without Vault")
            return

        try:
            self._client = hvac.Client(url=addr)
            self._client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            if self._client.is_authenticated():
                self._connected = True
                logger.info("Vault connected via AppRole at %s", addr)
                # Validate Vault is ready
                health_status = self.health_status()
                if health_status != "healthy":
                    logger.warning("Vault is not healthy (status: %s) — running in degraded mode", health_status)
            else:
                logger.warning("Vault AppRole login failed — running without Vault")
        except Exception as exc:
            logger.warning("Vault connection failed: %s — running without Vault", exc)

    @property
    def connected(self) -> bool:
        return self._connected

    def get_secret(self, path: str) -> dict[str, Any] | None:
        """Read secret from Vault KV v2 with TTL cache.

        Cache hit (within TTL): return cached value, skip Vault read.
        Cache miss or TTL expired: read from Vault and refresh cache.
        Vault error with stale cache: return stale cache (graceful degradation).
        Vault error without cache: return None.
        """
        now = time.time()

        # Return cached value if within TTL.
        cached_entry = self._cache.get(path)
        if cached_entry is not None:
            data, timestamp = cached_entry
            if now - timestamp < self._cache_ttl:
                logger.debug("Cache hit (within TTL) for %s", path)
                return data

        if self._client and self._connected:
            try:
                resp = self._client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._mount,
                )
                if not resp or "data" not in resp or "data" not in resp["data"]:
                    raise VaultSecretNotFoundError(f"Secret not found at {path}")

                data = resp["data"]["data"]
                self._cache[path] = (data, time.time())
                logger.debug("Vault read successful for %s", path)
                return data
            except Exception as exc:
                # Vault-typed errors (e.g. VaultSecretNotFoundError raised
                # above) are real, classified failures — propagate them
                # instead of swallowing into graceful-degradation/None.
                if isinstance(exc, VaultError):
                    raise
                if "invalid path" in str(exc).lower():
                    raise VaultSecretNotFoundError(f"Invalid path {path}: {exc}") from exc
                elif "permission denied" in str(exc).lower() or "forbidden" in str(exc).lower():
                    raise VaultAuthError(f"Permission denied for {path}: {exc}") from exc

                logger.error("Vault read failed for %s: %s", path, exc)
                # Graceful degradation: return stale cache regardless of TTL.
                if cached_entry is not None:
                    logger.warning("Returning stale cache for %s due to Vault failure", path)
                    return cached_entry[0]
                logger.critical("No cached value available for %s during Vault failure", path)
                return None

        # Not connected — return stale cache if available.
        if cached_entry is not None:
            logger.warning("Vault not connected, returning cached value for %s", path)
            return cached_entry[0]

        logger.warning("Vault not connected and no cached value for %s", path)
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
            self._cache[path] = (value, time.time())
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
                logger.warning("Vault health check returned status code: %s", health.status_code)
                return "unavailable"
            # Dict response = 200 OK
            return "healthy"
        except Exception as exc:
            logger.error("Vault health check failed: %s", exc)
            return "unavailable"
