"""M4 regression: internal-only services must not publish host ports.

vault (8200) and valkey (6379) are reachable only over the internal compose
network. Publishing them to the host widened the attack surface. This test
parses the root docker-compose.yml and asserts those services have NO `ports:`
host mapping, while the customer-facing services remain reachable.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_COMPOSE = Path(__file__).resolve().parents[2] / "docker-compose.yml"


def _services() -> dict:
    data = yaml.safe_load(_COMPOSE.read_text(encoding="utf-8"))
    return data["services"]


def test_compose_file_exists():
    assert _COMPOSE.is_file(), f"missing {_COMPOSE}"


def test_vault_has_no_host_port_mapping():
    svc = _services()["vault"]
    assert "ports" not in svc, "vault must not publish a host port (M4)"


def test_valkey_has_no_host_port_mapping():
    svc = _services()["valkey"]
    assert "ports" not in svc, "valkey must not publish a host port (M4)"


def test_postgres_has_no_host_port_mapping():
    svc = _services()["postgres"]
    assert "ports" not in svc, "postgres must not publish a host port (M4)"


def test_customer_facing_services_still_exposed():
    """Golden path intact: console/api/gateway/caddy still reachable."""
    services = _services()
    for name in ("nomos-console", "nomos-api", "openclaw-gateway", "caddy"):
        assert "ports" in services[name], f"{name} must remain reachable"
