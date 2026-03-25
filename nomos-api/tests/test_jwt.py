import time
from nomos_api.auth.jwt import create_token, decode_token, TokenPayload

def test_create_and_decode_token():
    payload = TokenPayload(user_id="user-1", email="admin@nomos.local", role="admin")
    token = create_token(payload, secret="test-secret", expires_hours=8)
    decoded = decode_token(token, secret="test-secret")
    assert decoded.user_id == "user-1"
    assert decoded.email == "admin@nomos.local"
    assert decoded.role == "admin"

def test_expired_token_returns_none():
    payload = TokenPayload(user_id="user-1", email="admin@nomos.local", role="admin")
    token = create_token(payload, secret="test-secret", expires_hours=-1)
    decoded = decode_token(token, secret="test-secret")
    assert decoded is None

def test_invalid_token_returns_none():
    decoded = decode_token("garbage.token.here", secret="test-secret")
    assert decoded is None

def test_wrong_secret_returns_none():
    payload = TokenPayload(user_id="user-1", email="admin@nomos.local", role="admin")
    token = create_token(payload, secret="correct-secret", expires_hours=8)
    decoded = decode_token(token, secret="wrong-secret")
    assert decoded is None

def test_role_validation():
    payload = TokenPayload(user_id="user-1", email="u@nomos.local", role="user")
    token = create_token(payload, secret="s", expires_hours=1)
    decoded = decode_token(token, secret="s")
    assert decoded.role == "user"
