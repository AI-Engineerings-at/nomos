"""Regression tests for the post-judgment-day fixes.

Each test guards a specific finding from the blind adversarial review.
Failing here = a real production-grade defect crept back in.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


# -----------------------------------------------------------------------
# C3: SSRF defense in gateway_url MUST reject private / loopback / IMDS
# Unit-tested against the validator directly (no DB/auth chain noise).
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "http://127.0.0.1:8080/",
        "http://localhost:5432/",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # AWS / GCP IMDS
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://vault:8200/",
        "http://valkey:6379/",
        "http://postgres:5432/",
        "file:///etc/passwd",
        "gopher://attacker/",
    ],
)
def test_gateway_url_ssrf_reject(bad: str) -> None:
    from nomos_api.routers.settings import _validate_gateway_url

    with pytest.raises(HTTPException) as exc:
        _validate_gateway_url(bad)
    assert exc.value.status_code == 422, f"SSRF target {bad!r} must be rejected with 422"


def test_gateway_url_external_https_is_allowed() -> None:
    """Positive control: legitimate external URLs must pass."""
    from nomos_api.routers.settings import _validate_gateway_url

    assert _validate_gateway_url("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert _validate_gateway_url("http://openclaw-gateway:18789") == "http://openclaw-gateway:18789"


# -----------------------------------------------------------------------
# C2: /api/system/unseal-key concurrent race — only ONE caller wins.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unseal_key_concurrent_race_is_atomic(client: AsyncClient, tmp_path: Path) -> None:
    key_file = tmp_path / "k"
    key_file.write_text("s.UNSEAL-FROM-RACE")
    marker = tmp_path / "served-marker"  # marker MUST NOT exist initially

    with (
        patch("nomos_api.routers.system._get_unseal_key_paths", return_value=[key_file]),
        patch("nomos_api.routers.system._get_served_marker_path", return_value=marker),
    ):
        # Fire many concurrent calls; only the OS-arbitrated O_EXCL winner
        # may receive 200. All others MUST get 410 (already served).
        responses = await asyncio.gather(*[client.get("/api/system/unseal-key") for _ in range(8)])

    statuses = [r.status_code for r in responses]
    n_winners = statuses.count(200)
    assert n_winners == 1, f"exactly one winner expected, got {n_winners}: {statuses}"
    assert all(s in (200, 410) for s in statuses), f"unexpected status mix: {statuses}"


# -----------------------------------------------------------------------
# H1-B: orphan user-turn must NOT be persisted when the LLM call fails.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_does_not_orphan_user_turn_on_llm_failure(monkeypatch) -> None:
    """If the LLM call fails, no user turn may be persisted (post-fix).

    Pre-judgment-day proxy_chat persisted the user turn BEFORE the LLM
    call. On failure the request 502'd but the user turn remained,
    corrupting future history into [user, user, ...]. The fix moved
    persistence (process_new_message + memory.store_message) to AFTER a
    successful LLM response.

    This unit test calls the proxy_chat handler directly with mocked DB,
    auth, agent, and LLM — asserts no memory.store_message /
    process_new_message call occurred when LLM returned None (502 path).
    """
    from unittest.mock import AsyncMock, MagicMock

    from nomos_api.models import Agent, User
    from nomos_api.routers import proxy as proxy_module
    from nomos_api.schemas import ProxyChatRequest

    fake_db = MagicMock()
    agent = Agent(
        id="agent-orphan",
        name="x",
        role="external-secretary",
        company="acme",
        email="user@acme",
        risk_class="limited",
        manifest_hash="x" * 64,
        manifest_data={},
    )
    fake_db.get = AsyncMock(return_value=agent)
    user = User(
        id="u1", email="user@acme", password_hash="x", role="user", is_active=True, session_timeout_hours=8
    )

    # Spy on persistence — must NOT be called on the failure path.
    pipeline_spy = AsyncMock()
    store_spy = AsyncMock()
    monkeypatch.setattr(proxy_module, "_has_direct_llm", lambda: True)
    monkeypatch.setattr(proxy_module, "_direct_llm_chat", AsyncMock(return_value=None))
    monkeypatch.setattr(
        proxy_module,
        "ContextPipeline",
        lambda: MagicMock(
            process_new_message=pipeline_spy,
            get_managed_context=AsyncMock(return_value=[]),
        ),
    )
    monkeypatch.setattr(proxy_module.memory, "store_message", store_spy)
    monkeypatch.setattr(proxy_module, "check_agent_access", lambda *_: None)

    body = ProxyChatRequest(agent_id="agent-orphan", message="m", session_id="s1")
    fake_request = MagicMock()
    fake_request.state.request_id = "rid"
    with pytest.raises(Exception) as exc:
        await proxy_module.proxy_chat(body, fake_request, user=user, db=fake_db)
    # Should raise HTTPException 502
    from fastapi import HTTPException as _HE

    assert isinstance(exc.value, _HE) and exc.value.status_code == 502, (
        f"LLM failure should raise 502, got {exc.value!r}"
    )
    assert pipeline_spy.await_count == 0, "process_new_message must NOT be called on LLM failure"
    assert store_spy.await_count == 0, "memory.store_message must NOT be called on LLM failure"


# -----------------------------------------------------------------------
# C-Recovery: BIP-39 wordlist must be the FULL 2048 (not the 128-word stub).
# -----------------------------------------------------------------------


def test_recovery_wordlist_is_full_bip39() -> None:
    from nomos_api.auth.recovery import _WORDLIST

    assert len(_WORDLIST) == 2048, f"BIP-39 wordlist must be 2048 entries, got {len(_WORDLIST)}"
    # Sanity: known first/last words from the canonical English list.
    assert _WORDLIST[0] == "abandon"
    assert _WORDLIST[-1] == "zoo"
