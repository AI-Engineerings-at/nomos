"""Tests for Workspace service — isolation, mount/unmount, retire."""

from __future__ import annotations

from nomos_api.services.workspace import WorkspaceService
from nomos_api.services.honcho import HonchoClient


def test_create_agent_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    ws = svc.create_agent_workspace("mani")
    assert ws["name"] == "mani"


def test_agent_can_read_own_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    assert svc.can_access("mani", "mani", "read") is True
    assert svc.can_access("mani", "mani", "write") is True


def test_agent_cannot_access_other_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    svc.create_agent_workspace("lisa")
    assert svc.can_access("mani", "lisa", "read") is False
    assert svc.can_access("mani", "lisa", "write") is False


def test_agent_can_read_company_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_company_workspace()
    assert svc.can_access("mani", "company", "read") is True
    assert svc.can_access("mani", "company", "write") is False


def test_mount_collection():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    result = svc.mount_collection("mani", "brand-guidelines")
    assert result is True
    assert "brand-guidelines" in svc.get_mounted_collections("mani")


def test_mount_collection_idempotent():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    svc.mount_collection("mani", "brand-guidelines")
    svc.mount_collection("mani", "brand-guidelines")
    collections = svc.get_mounted_collections("mani")
    assert collections.count("brand-guidelines") == 1


def test_unmount_collection():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    svc.mount_collection("mani", "brand-guidelines")
    svc.unmount_collection("mani", "brand-guidelines")
    assert "brand-guidelines" not in svc.get_mounted_collections("mani")


def test_unmount_nonexistent_collection():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    result = svc.unmount_collection("mani", "nonexistent")
    assert result is False


def test_retire_revokes_access():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    svc.create_agent_workspace("mani")
    svc.mount_collection("mani", "brand-guidelines")
    svc.retire_agent("mani")
    assert svc.can_access("mani", "mani", "read") is False
    assert svc.get_mounted_collections("mani") == []


def test_get_mounted_collections_unknown_agent():
    client = HonchoClient(base_url="http://mock:5055")
    svc = WorkspaceService(client)
    assert svc.get_mounted_collections("unknown") == []
