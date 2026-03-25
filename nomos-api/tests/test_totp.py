import pyotp
from nomos_api.auth.totp import generate_totp_secret, verify_totp, get_provisioning_uri

def test_generate_secret():
    secret = generate_totp_secret()
    assert len(secret) == 32
    assert secret.isalnum()

def test_verify_totp_valid():
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp(secret, code) is True

def test_verify_totp_invalid():
    secret = generate_totp_secret()
    assert verify_totp(secret, "000000") is False

def test_provisioning_uri():
    secret = generate_totp_secret()
    uri = get_provisioning_uri(secret, "admin@nomos.local", "NomOS")
    assert "otpauth://totp/" in uri
    assert "NomOS" in uri
    assert secret in uri
