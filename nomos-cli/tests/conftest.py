"""nomos-cli test session fixtures — set required env BEFORE any imports.

The hash chain now fails closed without NOMOS_HASHCHAIN_HMAC_KEY (>=32 bytes).
Inject a clearly-labelled non-production key for the test process so all
hash-chain-touching tests can run; the production path remains fail-closed.
"""

from __future__ import annotations

import os

# Strong (>=32 bytes), clearly-test-only HMAC key. Production injects via Vault.
os.environ.setdefault(
    "NOMOS_HASHCHAIN_HMAC_KEY",
    "TEST-ONLY-HMAC-key-do-not-use-in-production-32bytes+++",
)
