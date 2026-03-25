import pytest
from nomos_api.auth.middleware import require_role, AuthError
from nomos_api.auth.jwt import create_token, TokenPayload

SECRET = "test-secret"

def test_require_admin_with_admin_token():
    payload = TokenPayload(user_id="u1", email="a@nomos.local", role="admin")
    token = create_token(payload, SECRET)
    result = require_role(token, SECRET, allowed_roles=["admin"])
    assert result.user_id == "u1"
    assert result.role == "admin"

def test_require_admin_with_user_token():
    payload = TokenPayload(user_id="u2", email="u@nomos.local", role="user")
    token = create_token(payload, SECRET)
    with pytest.raises(AuthError, match="Insufficient permissions"):
        require_role(token, SECRET, allowed_roles=["admin"])

def test_require_any_role():
    payload = TokenPayload(user_id="u3", email="o@nomos.local", role="officer")
    token = create_token(payload, SECRET)
    result = require_role(token, SECRET, allowed_roles=["admin", "officer"])
    assert result.role == "officer"

def test_no_token():
    with pytest.raises(AuthError, match="No token"):
        require_role(None, SECRET, allowed_roles=["admin"])

def test_invalid_token():
    with pytest.raises(AuthError, match="Invalid token"):
        require_role("garbage", SECRET, allowed_roles=["admin"])
