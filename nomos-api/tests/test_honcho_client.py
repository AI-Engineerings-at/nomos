"""Tests for Honcho in-memory client — workspace, session, message CRUD."""

from __future__ import annotations

from nomos_api.services.honcho import HonchoClient


def test_create_client():
    client = HonchoClient(base_url="http://honcho:5055")
    assert client.base_url == "http://honcho:5055"


def test_create_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    workspace = client.create_workspace("mani")
    assert workspace["id"] is not None
    assert workspace["name"] == "mani"


def test_get_workspace():
    client = HonchoClient(base_url="http://mock:5055")
    ws = client.create_workspace("mani")
    retrieved = client.get_workspace(ws["id"])
    assert retrieved is not None
    assert retrieved["name"] == "mani"


def test_get_workspace_not_found():
    client = HonchoClient(base_url="http://mock:5055")
    assert client.get_workspace("nonexistent") is None


def test_create_session():
    client = HonchoClient(base_url="http://mock:5055")
    session = client.create_session("workspace-1", agent_id="mani")
    assert session["id"] is not None
    assert session["agent_id"] == "mani"


def test_add_message():
    client = HonchoClient(base_url="http://mock:5055")
    msg = client.add_message("session-1", role="user", content="Hello")
    assert msg["id"] is not None
    assert msg["role"] == "user"
    assert msg["content"] == "Hello"


def test_add_message_to_existing_session():
    client = HonchoClient(base_url="http://mock:5055")
    sess = client.create_session("ws-1", agent_id="mani")
    client.add_message(sess["id"], role="user", content="Hello")
    assert len(client._sessions[sess["id"]]["messages"]) == 1


def test_list_sessions():
    client = HonchoClient(base_url="http://mock:5055")
    client.create_session("workspace-1", agent_id="mani")
    client.create_session("workspace-1", agent_id="mani")
    client.create_session("workspace-2", agent_id="lisa")
    sessions = client.list_sessions("workspace-1")
    assert isinstance(sessions, list)
    assert len(sessions) == 2


def test_delete_session():
    client = HonchoClient(base_url="http://mock:5055")
    sess = client.create_session("ws-1", agent_id="mani")
    result = client.delete_session(sess["id"])
    assert result is True
    assert client.list_sessions("ws-1") == []


def test_delete_session_not_found():
    client = HonchoClient(base_url="http://mock:5055")
    result = client.delete_session("nonexistent")
    assert result is False


def test_delete_messages_by_content():
    client = HonchoClient(base_url="http://mock:5055")
    sess = client.create_session("ws-1", agent_id="mani")
    client.add_message(sess["id"], "user", "My email is max@example.com")
    client.add_message(sess["id"], "assistant", "Hello Max!")
    deleted = client.delete_messages_by_content("max@example.com")
    assert deleted == 1


def test_delete_messages_by_content_none_found():
    client = HonchoClient(base_url="http://mock:5055")
    deleted = client.delete_messages_by_content("nobody@example.com")
    assert deleted == 0
