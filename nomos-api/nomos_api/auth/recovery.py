import hashlib
import secrets
import bcrypt

# BIP-39 English wordlist (first 128 words for simplicity — full 2048 in production)
# In production: load from file or use mnemonic library
_WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
    "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
    "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
    "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
    "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album",
    "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone",
    "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among",
    "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry",
    "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
    "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april",
    "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor",
    "army", "arrange", "arrest", "arrive", "arrow", "art", "artefact", "artist",
    "artwork", "ask", "aspect", "assault", "asset", "assist", "assume", "asthma",
    "athlete", "atom", "attack", "attend", "attitude", "attract", "auction", "audit",
    "august", "aunt", "author", "auto", "autumn", "average", "avocado", "avoid",
]


def generate_recovery_key() -> list[str]:
    return [secrets.choice(_WORDLIST) for _ in range(12)]


def _digest(phrase: str) -> bytes:
    """SHA-256 digest to stay within bcrypt's 72-byte limit."""
    return hashlib.sha256(phrase.encode()).hexdigest().encode()


def hash_recovery_key(phrase: str) -> str:
    return bcrypt.hashpw(_digest(phrase), bcrypt.gensalt()).decode()


def verify_recovery_key(phrase: str, hashed: str) -> bool:
    return bcrypt.checkpw(_digest(phrase), hashed.encode())
