# State-of-the-Art Audit / Backend Roadmap

> Created 2026-05-20. Goal: bring the NomOS audit trail (and the
> question of alternative agent backends) to documented state-of-the-art
> per EU AI Act Article 12 enforcement date (Aug 2, 2026) and current
> 2025-2026 industry practice.

## 0. Goal (single sentence)

Make the NomOS audit trail **publicly verifiable, non-repudiable,
externally anchored, and retention-automated** before the EU AI Act
Article 12 obligations for high-risk AI systems take effect on
**2026-08-02**, while keeping operational simplicity for the Docker
single-host deployment target.

## 1. Research summary (2025-2026 SOTA, sources at the bottom)

### EU AI Act Article 12 (record-keeping)
- High-risk AI systems MUST automatically record events over their
  lifetime — no manual logging.
- Minimum retention: **6 months**.
- Events recorded must enable: identifying risk/substantial-modification
  situations, post-market monitoring, operational monitoring.
- For biometric ID systems: extra fields (use period start/end,
  reference DB, input that matched, verifying natural persons).
- Annex III obligations effective **2026-08-02**. Fines up to **€15 M
  or 3 % of worldwide annual turnover**.

### Industry state-of-the-art tamper-evident logs
- **HMAC hash-chained logs** (what we have) — solid for tamper-detection
  during write, but if the key leaks the chain is retroactively
  forgeable (single point of failure).
- **Ed25519 per-entry signatures** — public-key, non-repudiable, no
  shared secret required for verification; verifier-compromise
  resistant. Production consensus: combine HMAC (fast write path) +
  Ed25519 (non-repudiation).
- **External anchoring** — periodically write the chain head (or
  Merkle root) to an external system (S3 Object Lock, KMS-signed
  artifact, public transparency log). Makes rewrites detectable even
  if the HMAC key leaks.
- **Sigstore Rekor / Trillian Merkle transparency log** — the open-
  source gold standard. Append-only Merkle tree, periodically signed,
  publicly verifiable by any third party. Rekor v2 + rekor-monitor in
  production use.

### OpenClaw 2026.5.18 (verified via release research)
- Plugin SDK bundles zod, restored memory-core alias, Node 22.19+,
  @openclaw/proxyline 0.3.3, Pi 0.75.1. No breaking change vs the
  plugin contract we depend on. Live golden path returns chat 200.
- **Decision: keep the bump.** No regression evidence; the Batch-E
  pin-back hypothesis was correctly not acted on.

### NemoClaw — current status (verified in-repo)
- In nomos: a **manifest field only** (`manifest.nemoclaw.network_policy`)
  + a text mention in the generated compliance doc. **No active code
  backend.**
- Upstream status: documented "Alpha, optional, kein Handlungsbedarf"
  (`docs/references/openclaw-nemoclaw-reference.md`, `.claude/CLAUDE.md`).
- Activating NemoClaw as a real sandbox backend would be weeks of
  architecture work; out of scope for this hardening cycle.

### Hermes — clarification
- **Not part of nomos.** No code, doc, or schema reference. Hermes is
  used in two unrelated contexts: (a) Nous Research's Hermes-agent /
  Hermes models, (b) HQ-side `phantom-ai/NomOS-B-V2` Phantom Neural
  Cortex agent fleet ("Paperclip + OpenClaw + Hermes v3"). Neither
  belongs in this product.

## 2. Current state (verified, post-judgment-day-2)

| Capability | Status |
|---|---|
| HMAC-SHA256 hash chain | ✓ fail-closed key, no legacy bypass |
| AuthZ on all 5 audit endpoints | ✓ admin-only global, owner-or-service per-agent, owner-or-service for writes |
| DB mirror of chain | ✓ `AuditLog` table |
| Console UI | ✓ `/admin/audit` page |
| Per-agent event types catalog | ✓ `nomos.core.events` enum |
| Compliance docs auto-generated | ✓ `gate.py` |
| Encrypted-at-rest | ✓ via Docker volume + customer-controlled |
| **Ed25519 per-entry signature** | ✗ |
| **External anchoring of chain head** | ✗ |
| **Retention automation** (Art. 12 ≥6 months) | ✗ manifest field exists, no enforcement |
| **Merkle / Rekor-style transparency log** | ✗ |
| **Annex IV event-category audit** | ✗ never explicitly mapped |

## 3. Phased roadmap

### Phase A — ship state-of-the-art before Aug 2 2026 (THIS effort)

**A1. Ed25519 per-entry signatures (non-repudiation).**
- Generate Ed25519 keypair at Vault-init (private to Vault, public
  exported to `/vault/init/audit-signing.pub`).
- Each `HashChainEntry` gains a `signature` field = Ed25519 sign of
  the entry hash with the Vault-held private key.
- `verify_chain` checks both HMAC (key-bound integrity) AND Ed25519
  (non-repudiation). Verification only needs the PUBLIC key — anyone
  can verify, no secret sharing required.
- Done when: round-trip test passes, missing signature → invalid,
  forged signature with attacker key → invalid.

**A2. External anchoring of the chain head.**
- ARQ cron job `anchor_audit_heads` (every 1h): for each agent, write
  `{agent_id, chain_length, head_hash, head_hmac, head_signature,
  anchored_at}` JSON line into `/data/audit-anchors/anchors.jsonl`
  (separate volume mount).
- Documented for prod: configure the anchor volume on WORM-capable
  storage (S3 Object Lock / Azure immutable blob); deferred from
  product code (customer choice).
- Done when: cron registered, anchors file grows, manual rewrite of
  the chain (with valid HMAC+signature recomputed) is still detected
  via mismatch with the durable anchor.

**A3. Retention automation per Article 12.**
- ARQ cron job `enforce_audit_retention` (daily): for each agent, read
  `manifest.governance.audit_retention_days` (floor 180 days = 6 months
  Art. 12 minimum), prune chain entries older than retention while
  ALWAYS retaining `[SUMMARY]` rows and the most recent N entries.
- Crucially: before pruning, write a `retention.checkpoint` audit
  entry that records the pruning event itself (auditable
  retention).
- Done when: cron registered, test with backdated entries proves
  retention enforced + checkpoint recorded.

**A4. Annex IV event-category coverage audit.**
- Read `nomos.core.events.EventType`. Map every event category Article
  12 demands to an entry-type in our enum. Add what's missing
  (e.g. risk-situation events, post-market monitoring events).
- Document the mapping in `docs/compliance-guide.md`.

**A5. /audit/verify endpoint returns checkpoint info.**
- Response includes `last_anchored_at`, `last_anchored_head_hash`,
  whether the current head matches the latest anchor. Lets external
  auditors verify continuity without DB access.

**A6. Operations runbook update.**
- Document: how to verify the chain manually (with the public key),
  how to roll the Vault-held private key (re-anchor required), how to
  audit-export for a regulator, where the anchors live, what WORM-
  capable backing store to use in production.

### Phase B — community-grade transparency log

**B1. Embedded Merkle transparency log (RFC 6962). ✓ SHIPPED.**
- `nomos.core.merkle`: RFC 6962 leaf/internal hashing, MTH, inclusion
  proofs, signed tree heads (STH) signed by the existing Ed25519 key.
- New API endpoints (owner-or-service-or-admin AuthZ):
  - `GET /api/agents/{id}/audit/sth` — STH (origin, tree_size,
    root_hash, timestamp, signature). Sigstore-Rekor-style checkpoint.
  - `GET /api/agents/{id}/audit/proof/{sequence}` — inclusion proof
    for any single chain entry (audit_path).
- Anchor cron records now also carry `merkle_tree_size` + `merkle_root_hash`.
- A regulator with only the Ed25519 public key + an STH + an inclusion
  proof can confirm any single audit event was committed in the
  transparency log at a known historical root — no DB / chain access
  required.

**B2. Public Rekor anchoring (optional, customer choice).** Open.
- For customers who want public verifiability, allow opting into
  publishing anchored roots to the Sigstore Rekor public instance.
- Disabled by default (data-protection trade-off — would expose chain
  roots externally).

### Phase C — out of scope for nomos product

- **NemoClaw sandbox backend implementation** — separate architecture
  effort, weeks. Keep the manifest field as a "planned" marker; the
  generated compliance doc accurately states current status.
- **Hermes integration** — not a nomos concern. Documented as a
  separate Nous Research / HQ-side project. Cross-link only.

## 4. Done-criteria (Phase A acceptance gate)

1. All A1–A6 changes committed, ruff/format/tests green.
2. New regression tests: signature roundtrip, missing-signature
   rejection, forged-with-attacker-key rejection, anchor-mismatch
   detected, retention enforced + checkpoint recorded.
3. nomos-api full chunked suite 0 failed.
4. Live verify against pristine docker stack: write some entries,
   inspect `/data/audit-anchors/anchors.jsonl`, manually flip a byte
   in the chain — verify_chain returns `valid=false` AND anchor
   mismatch is reported.
5. `docs/compliance-guide.md` updated with Annex IV event mapping.
6. `docs/operations-runbook.md` updated with the new procedures.
7. PR opened to main; CI green.

## 5. Out of scope (explicitly)

- Hermes integration (separate product).
- NemoClaw backend code (deferred — manifest field stays as marker).
- Bitcoin / on-chain timestamping (OpenTimestamps integration is
  Phase-B at earliest; over-engineered for current customer scale).
- Internal IP / 10.40.10.x deployments (this is the product repo;
  rule 01 applies).

## 6. Risk table

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Vault loses the signing key | Low | All future signatures broken; verify_chain warns | Document key-rotation procedure; old entries verifiable with archived public key |
| Cron job missed (anchor gap) | Med | Verifiable gap window (1h) | Backfill on next run; alert if gap > threshold |
| Customer disables retention via manifest | Med | Compliance violation | Hard floor of 180d at the code level; reject manifests below the floor |
| Performance: signature per entry | Low | ~50 µs/entry Ed25519 sign; negligible | Tested before rollout |
| Anchor file deleted | Med | Anchors lost, but chain still HMAC/signature-verifiable | WORM-capable volume documented; alert on missing anchor file |

## Sources (research feed)

- [EU AI Act Article 12 — Record-Keeping (EC AI Act Service Desk)](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12)
- [Article 12 logging requirements — Help Net Security 2026-04](https://www.helpnetsecurity.com/2026/04/16/eu-ai-act-logging-requirements/)
- [Article 12 — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/12/)
- [Sigstore Rekor introduction — Chainguard Academy](https://edu.chainguard.dev/open-source/sigstore/rekor/an-introduction-to-rekor/)
- [Tamper-Evident Audit Trail for AI Agents — nono.sh](https://nono.sh/blog/secure-agent-audit)
- [Trillian — transparency.dev](https://transparency.dev/)
- [Immutable audit log with HMAC hash chaining — Tracehold](https://tracehold.ai/blog/immutable-audit-log-hmac-hash-chain/)
- [Ed25519 provable security paper](https://eprint.iacr.org/2020/823.pdf)
- [OpenClaw 2026.5.18 changelog (multiple sources via search)](https://github.com/openclaw/openclaw/releases)
