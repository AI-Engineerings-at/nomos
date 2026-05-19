import hashlib
import secrets

import bcrypt
from mnemonic import Mnemonic

# Full BIP-39 English wordlist (2048 words) via the `mnemonic` library.
# A 12-word draw from this list = 12 * log2(2048) = 132 bits of entropy
# (BIP-39 spec). The earlier "first 128 words for simplicity" stub gave
# only ~84 bits — security theater. Asserted at import time so a future
# import-time substitution can't silently weaken this.
_WORDLIST = Mnemonic("english").wordlist
assert len(_WORDLIST) == 2048, f"BIP-39 wordlist must have 2048 entries (got {len(_WORDLIST)})"


def generate_recovery_key() -> list[str]:
    return [secrets.choice(_WORDLIST) for _ in range(12)]


def _digest(phrase: str) -> bytes:
    """SHA-256 digest to stay within bcrypt's 72-byte limit."""
    return hashlib.sha256(phrase.encode()).hexdigest().encode()


def hash_recovery_key(phrase: str) -> str:
    return bcrypt.hashpw(_digest(phrase), bcrypt.gensalt()).decode()


def verify_recovery_key(phrase: str, hashed: str) -> bool:
    return bcrypt.checkpw(_digest(phrase), hashed.encode())
