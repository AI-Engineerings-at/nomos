"""Tests for DSGVO Art. 17 Forget service — delete PII, preserve audit trail."""

from __future__ import annotations

from nomos_api.services.forget import ForgetService
from nomos_api.services.honcho import HonchoClient


def test_forget_removes_pii():
    client = HonchoClient(base_url="http://mock:5055")
    ws = client.create_workspace("mani")
    sess = client.create_session(ws["id"], "mani")
    client.add_message(sess["id"], "user", "My email is max@example.com")
    client.add_message(sess["id"], "assistant", "Hello Max!")

    svc = ForgetService(client)
    result = svc.forget("max@example.com")
    assert result["deleted_messages"] >= 1
    assert result["audit_event"] == "data.erased"


def test_forget_unknown_email():
    client = HonchoClient(base_url="http://mock:5055")
    svc = ForgetService(client)
    result = svc.forget("nobody@example.com")
    assert result["deleted_messages"] == 0


def test_forget_preserves_audit():
    client = HonchoClient(base_url="http://mock:5055")
    ws = client.create_workspace("mani")
    sess = client.create_session(ws["id"], "mani")
    client.add_message(sess["id"], "user", "Contact: max@example.com")

    svc = ForgetService(client)
    result = svc.forget("max@example.com")
    assert result["audit_preserved"] is True


def test_forget_returns_search_term():
    client = HonchoClient(base_url="http://mock:5055")
    ws = client.create_workspace("test")
    sess = client.create_session(ws["id"], "test")
    client.add_message(sess["id"], "user", "Email: joe@test.com here")

    svc = ForgetService(client)
    result = svc.forget("joe@test.com")
    assert result["search_term"] == "joe@test.com"


def test_forget_multiple_messages():
    client = HonchoClient(base_url="http://mock:5055")
    ws = client.create_workspace("mani")
    sess = client.create_session(ws["id"], "mani")
    client.add_message(sess["id"], "user", "Email: max@example.com")
    client.add_message(sess["id"], "user", "Please contact max@example.com")
    client.add_message(sess["id"], "assistant", "No PII here")

    svc = ForgetService(client)
    result = svc.forget("max@example.com")
    assert result["deleted_messages"] == 2
