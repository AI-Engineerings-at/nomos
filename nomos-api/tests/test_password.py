from nomos_api.auth.password import hash_password, verify_password, validate_password_strength

def test_hash_and_verify():
    pw = "SecureP@ss123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_password_strength_valid():
    errors = validate_password_strength("SecureP@ss123!")
    assert errors == []

def test_password_strength_too_short():
    errors = validate_password_strength("Short1!")
    assert any("12" in e for e in errors)

def test_password_strength_no_uppercase():
    errors = validate_password_strength("nouppercase123!")
    assert len(errors) > 0

def test_password_strength_no_digit():
    errors = validate_password_strength("NoDigitsHere!")
    assert len(errors) > 0
