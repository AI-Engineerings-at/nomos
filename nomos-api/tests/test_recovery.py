from nomos_api.auth.recovery import generate_recovery_key, hash_recovery_key, verify_recovery_key

def test_generate_recovery_key():
    words = generate_recovery_key()
    assert len(words) == 12
    assert all(isinstance(w, str) for w in words)
    assert all(len(w) > 0 for w in words)

def test_hash_and_verify_recovery_key():
    words = generate_recovery_key()
    phrase = " ".join(words)
    hashed = hash_recovery_key(phrase)
    assert hashed != phrase
    assert verify_recovery_key(phrase, hashed) is True
    assert verify_recovery_key("wrong words here now please try again later ok bye", hashed) is False

def test_two_keys_are_different():
    key1 = generate_recovery_key()
    key2 = generate_recovery_key()
    assert key1 != key2
