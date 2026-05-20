# Changelog

All notable changes to NomOS are documented here.
Versioning follows [SemVer](https://semver.org/) per component.
Date format: ISO-8601.

---

## [0.2.0] — 2026-05-20

> "Audit-Trail v2" — bring the audit trail to documented state-of-the-art
> before EU AI Act Article 12 takes effect on **2026-08-02**.

Components bumped: `nomos-api 0.2.0`, `nomos-cli 0.2.0`,
`nomos-console 0.2.0`. Plugin stays on its own track (`nomos-plugin 2.0.0`).

### Added — Audit-Trail Phase A (PR #5, #6)

- **Ed25519 per-entry signatures** alongside the existing HMAC-SHA256
  hash chain. Public-key non-repudiation; verifier no longer needs a
  shared secret. Fail-closed key handling — missing key = chain
  invalid.
- **External anchoring cron** `anchor_audit_heads` (hourly, ARQ).
  Appends `{agent_id, chain_length, head_hash, head_hmac,
  head_signature, anchored_at}` to `/data/audit-anchors/anchors.jsonl`
  on a separate volume (WORM-capable in production).
- **Periodic integrity checkpoint** `audit_integrity_checkpoint`
  (daily, ARQ). Verifies every agent's chain and writes a
  `audit.retention.checkpoint` row that itself joins the chain.
- **Retention floor** `manifest.governance.audit_retention_days`
  with code-level floor `>= 180` (Article 12 ≥6 months). Manifest
  loader rejects sub-floor values.
- **Annex IV event-category coverage**: added `AUDIT_CHAIN_ANCHORED`
  and `AUDIT_RETENTION_CHECKPOINT` event types and mapped Article 12
  / Annex IV categories to existing entry types. Mapping documented
  in `docs/compliance-guide.md`.
- **`/audit/verify` enrichment**: response now carries
  `last_anchored_at`, `last_anchored_head_hash`, and a boolean
  indicating whether the current head matches the latest anchor.
- **Operations runbook**: how to verify the chain with the public key,
  how to roll the signing key, how to export for a regulator, where
  the anchors live, WORM-storage recommendation. See
  `docs/operations-runbook.md`.

### Added — Audit-Trail Phase B1 (PR #7)

- **Embedded RFC 6962 Merkle transparency log** in
  `nomos.core.merkle`: leaf prefix `0x00`, node prefix `0x01`, Merkle
  Tree Hash (MTH), inclusion-proof PATH, signed tree heads (STH)
  signed by the same Ed25519 key.
- **API endpoint** `GET /api/agents/{id}/audit/sth` — returns
  `{origin, tree_size, root_hash, timestamp, signature}`
  (Sigstore-Rekor-style checkpoint).
- **API endpoint** `GET /api/agents/{id}/audit/proof/{sequence}` —
  returns a per-entry inclusion proof
  `{leaf_index, tree_size, root_hash, audit_path[]}`. Out-of-range
  returns 404.
- **Pure-function verifier** `verify_inclusion_proof` — recomputes
  the root from leaf + audit path; needs only the data the regulator
  was handed.
- **Anchor record** extended: `merkle_tree_size` and
  `merkle_root_hash` are now also persisted so historical proofs can
  be verified against time-stamped roots from the WORM-ready volume.

### Changed

- `nomos-api/pyproject.toml`, `nomos-cli/pyproject.toml`,
  `nomos-console/package.json`: version `0.1.0 → 0.2.0`.
- `nomos-api/pyproject.toml`, `nomos-cli/pyproject.toml`: explicit
  `cryptography>=42,<46` dep so Ed25519 is no longer transitive.
- `nomos-cli`: `[project.optional-dependencies] dev` adds
  `pytest>=8,<9` + `pytest-asyncio>=0.23,<1` so `uv run python -m
  pytest` works inside the cli venv.

### Tests

- **nomos-api**: 454 passed / 0 failed (chunked 170 + 119 + 165;
  +10 new tests in `test_audit_merkle_phase_b1.py`).
- **nomos-cli**: 239 passed / 0 failed.
- ruff + format clean.

### Deferred (explicitly)

- **Phase B2** — public Sigstore-Rekor anchoring. Opt-in only;
  off by default; would expose chain roots externally
  (data-protection trade-off).
- **NemoClaw backend** — manifest field stays as marker.
- **Hermes** — not a NomOS concern (separate product).

### References

- Roadmap: `docs/hardening-2026-05-20/PLAN.md`.
- Compliance: `docs/compliance-guide.md`.
- Ops: `docs/operations-runbook.md`.
- EU AI Act Art. 12: enforcement 2026-08-02, fines up to €15 M or 3 %.

---

## [0.1.0] — 2026-04 (pre-changelog era)

Initial production-ready release. 10/10 production-readiness verified
on a pristine `docker compose up`. Login → Hire → Compliant → Chat →
LLM responds. Auth (RBAC + state-change endpoints), 14
risk-class-dependent compliance documents, ARQ worker, TLS via Caddy,
Hire-to-Chat auto-generation, dual-mode chat proxy. 324+ compliance
tests. Pre-history captured in `Documents/nomos/.claude/CLAUDE.md`
"Aktiver Plan".
