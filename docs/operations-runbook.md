# NomOS Operations Runbook

> Last reconciled against `docker-compose.yml` and router source:
> 2026-05-20 (0.3.0 — Audit-Trail v2 Phase-A + B1 plus M1 anchor/checkpoint sibling-file separation, M3 container hardening, M2 performance quickwins). All service names, ports,
> healthchecks and volumes below are taken from `docker-compose.yml`.

This runbook covers bring-up, verification, secrets, backup and
troubleshooting for a Docker self-hosted NomOS deployment. For the
first-time install walkthrough see [Quickstart](quickstart.md).

---

## 1. Services & bring-up order

Compose enforces ordering via `depends_on` / `condition`
(`docker-compose.yml`). The effective start order is:

1. **`vault`** — HashiCorp Vault 1.17. Healthcheck: `wget` on
   `127.0.0.1:8200/v1/sys/health` (`compose:58-59`).
2. **`vault-init`** — one-shot init/unseal job
   (`condition: service_completed_successfully` is a dependency for
   gateway/api/worker, `compose:29,118,153`).
3. **`postgres`** — pgvector/pgvector:pg16. Healthcheck:
   `pg_isready -U nomos` (`compose:193`).
4. **`valkey`** — valkey/valkey:8-alpine. Healthcheck:
   `valkey-cli ping` (`compose:210`).
5. **`openclaw-gateway`** — depends on vault healthy + vault-init done;
   healthcheck `curl /healthz` on 18789 (`compose:25-32`).
6. **`nomos-api`** — depends on postgres + valkey + vault healthy and
   vault-init complete; healthcheck `curl localhost:8000/health`
   (`compose:110-121`).
7. **`nomos-worker`** — ARQ worker, same deps as api; healthcheck
   `python -c "import arq"` (`compose:145-156`).
8. **`nomos-console`** — depends on `nomos-api` healthy; healthcheck
   `wget localhost:3000` (`compose:171-176`).
9. **`caddy`** — TLS reverse proxy on 80/443 (`compose:218-228`).
10. Optional: **`piper-tts`**, **`whisper-stt`** (voice, optional).

Bring up:

```bash
docker compose up -d
docker compose ps          # wait until all show healthy/running
```

Host-published ports: console `${NOMOS_CONSOLE_PORT:-3040}`, API
`${NOMOS_API_PORT:-8060}`, gateway `${NOMOS_GATEWAY_PORT:-3050}`, Caddy
80/443, Vault 8200. `postgres`, `valkey` and `nomos-worker` are
compose-network only (no host port).

---

## 2. Healthchecks & verification

```bash
# API + dependency rollup (status=healthy only if PostgreSQL reachable)
curl -s http://localhost:8060/health | jq

# Gateway
curl -s http://localhost:3050/healthz

# Per-service container health
docker compose ps
docker inspect --format '{{.State.Health.Status}}' nomos-nomos-api-1
```

`GET /health` returns `status`, `service`, `version`, `vault`, and a
`components` map (`vault`/`postgres`/`valkey`/`gateway`). `status` is
`degraded` (not failed) if the gateway is offline; it is `healthy` only
when PostgreSQL is reachable (`nomos-api/nomos_api/routers/health.py:71-87`).

Admin-only operational metrics/alerts are under `/api/monitoring/*`
(requires an admin JWT — `routers/monitoring.py`).

---

## 3. Secrets via Vault

All credentials are managed by Vault (KV v2) and consumed through a
Vault-first settings source. The required secrets (never defaulted in
code or compose) are:

| Secret | Used by |
|---|---|
| `NOMOS_JWT_SECRET` | Session token signing |
| `NOMOS_PLUGIN_API_KEY` | Plugin / service-to-service auth |
| `NOMOS_GATEWAY_TOKEN` | Gateway ↔ API bidirectional auth |
| `NOMOS_DB_PASSWORD` | PostgreSQL (compose guards with `:?`) |
| `NOMOS_HASHCHAIN_HMAC_KEY` | Audit hash-chain HMAC (≥32 bytes, fail-closed). Vault path: `nomos/secrets/audit` field `hashchain_hmac_key`. Provisioned by `vault/init-entrypoint.sh` on first init. |
| `NOMOS_AUDIT_SIGNING_KEY` | Audit hash-chain Ed25519 signing seed (exactly 64 hex chars = 32 bytes, fail-closed). Vault path: `nomos/secrets/audit` field `audit_signing_key`. Provisioned by `vault/init-entrypoint.sh` on first init. The public key is derivable from this private seed and is what regulators / external auditors need to verify the chain. |
| One LLM provider key | `NVIDIA_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` |

### Audit-key rotation procedure

The HMAC key and the Ed25519 signing key may be rotated. Important: an
entry's HMAC and signature are bound to the key in force at write time;
**rotating a key does NOT invalidate older entries**, but the verifier
must have access to the prior public key to verify the older signatures
(keep an archive of retired public keys in your evidence vault).

1. Generate a new 32-byte secret in Vault (both fields live at the SAME
   path `nomos/secrets/audit` as one KV-v2 record — see
   `vault/init-entrypoint.sh` for the authoritative location):

   ```bash
   vault kv put nomos/secrets/audit \
     hashchain_hmac_key="$(openssl rand -hex 32)" \
     audit_signing_key="$(openssl rand -hex 32)"
   ```

   (NOTE: earlier 0.2.0 documentation listed three different Vault paths
   for these keys — `secrets/audit/hmac_key`,
   `secret/nomos/audit/hmac_key`, `secret/nomos/audit-signing/...`.
   None of those existed. 0.2.1 reconciles to the single
   `nomos/secrets/audit` path that the init-entrypoint actually writes.)
2. Export the **OLD public key** for verifier archival (before swap):
   `python -c "from nomos.core.hash_chain import _signing_key; print(_signing_key().public_key().public_bytes_raw().hex())"`
   Store in your evidence vault tagged with the date.
3. Restart `nomos-api` and `nomos-worker` so they pick up the new env.
4. New entries from this point sign with the new key. Old entries
   continue to verify with the **archived old public key** — keep that
   archive for at least the Art. 12 minimum retention (6 months) plus a
   buffer.

### Regulator-facing audit export

A regulator with only the chain export does NOT need access to your
HMAC key. They need only the **Ed25519 public key** corresponding to
each retention window.

1. Export the chain:
   `GET /api/agents/{id}/audit/export` (admin or owning user JWT cookie)
2. Provide the regulator with the current public key (and any archived
   public keys for older entries):
   `python -c "from nomos.core.hash_chain import _signing_key; print(_signing_key().public_key().public_bytes_raw().hex())"`
3. They verify independently with any Ed25519-capable tool; no shared
   secret is exchanged.

### Phase-B1: Signed Tree Head + inclusion-proof for a single event

For a regulator who needs to prove a **single** audit event was
committed without obtaining the whole chain (data-minimisation under
GDPR Art. 5(1)(c)), use the transparency-log endpoints introduced in
0.2.0 (`docs/hardening-2026-05-20/PLAN.md` Phase-B1).

1. **Pull the Signed Tree Head** (regulator runs):

   ```bash
   curl -H "X-NomOS-API-Key: $KEY" \
        https://YOUR_HOST/api/agents/AGENT_ID/audit/sth | tee sth.json
   ```

   Returns `{origin, tree_size, root_hash, timestamp, signature}`.

2. **Pull the inclusion proof** for the entry of interest (sequence N):

   ```bash
   curl -H "X-NomOS-API-Key: $KEY" \
        https://YOUR_HOST/api/agents/AGENT_ID/audit/proof/N | tee proof.json
   ```

   Returns `{leaf_index, tree_size, root_hash, audit_path[]}`.

3. **Verify locally**, no DB / no shared secret. Hand the regulator
   only `sth.json`, `proof.json`, the leaf JSON line from the chain
   export, and your Ed25519 public key. They run:

   ```python
   from nomos.core.merkle import (
       verify_signed_tree_head, verify_inclusion_proof,
   )
   import json
   sth = json.load(open("sth.json"))
   proof = json.load(open("proof.json"))
   assert verify_signed_tree_head(sth), "STH signature invalid"
   leaf_hex = "..."  # "hash" field of the leaf line from chain export
   ok = verify_inclusion_proof(
       leaf_data=leaf_hex.encode("utf-8"),
       leaf_index=proof["leaf_index"],
       tree_size=proof["tree_size"],
       audit_path_hex=proof["audit_path"],
       root_hash_hex=proof["root_hash"],
   )
   assert ok, "leaf not in tree at the claimed position"
   ```

   Two `assert` lines = full third-party audit. The regulator never
   sees other events.

4. **Historical proofs** verify against the `merkle_tree_size`
   + `merkle_root_hash` recorded in
   `/data/audit-anchors/anchors.jsonl` at anchor-cron time (Phase-A2).
   Pull the matching anchor record (same `agent_id`, anchored before
   the regulatory question), then verify the proof against that
   historical root rather than the current one. This neutralises the
   "what if the operator re-signed yesterday's chain?" attack —
   yesterday's root is on a separate WORM volume with its own
   timestamp.

Bootstrap/unseal flow:

- `vault` + `vault-init` initialize and unseal Vault on first run
  (scripts: `vault/init-entrypoint.sh`, `vault/init.sh`).
- During first-run setup only, `GET /api/system/unseal-key` returns the
  unseal key. It returns **403** once any admin user exists and **410**
  after a durable one-shot serve (`routers/system.py:129-156`). Treat
  the unseal key as break-glass material and store it offline.
- Create the first admin: `POST /api/users/bootstrap`
  (`{email, password, role:"admin"}`). The response includes a one-time
  recovery phrase — store it securely (`routers/users.py:66`).

Rotation: rotate a secret in Vault, then restart the consuming services
(`docker compose restart nomos-api nomos-worker openclaw-gateway`).

---

## 4. Backup & restore

Persistent state lives in named Docker volumes
(`docker-compose.yml:267-276`):

| Volume | Contents | Backup priority |
|---|---|---|
| `nomos-pgdata` | PostgreSQL (agents, users, audit index, tasks, ...) | Critical |
| `nomos-agents` | Agent files + audit hash chains (`/data/agents`) | Critical |
| `nomos-anchors` | Audit chain external anchors (`/data/audit-anchors/anchors.jsonl`). MUST be on WORM-capable storage in production (S3 Object Lock / Azure immutable blob). Defeats the threat model if it shares the chain volume — separate `nomos-anchors` named volume since 0.2.0 (Phase-A2). | Critical (WORM in prod) |
| `nomos-vault`, `nomos-vault-init` | Vault storage + init/unseal material | Critical |
| `nomos-valkey` | Cache / rate-limit / ARQ state | Ephemeral |
| `nomos-caddy-data`, `nomos-caddy-config` | TLS certs | Recreatable |

Logical Postgres backup:

```bash
docker compose exec -T postgres pg_dump -U nomos nomos > nomos-$(date +%F).sql
# restore: docker compose exec -T postgres psql -U nomos nomos < nomos-YYYY-MM-DD.sql
```

Agent files + chains (filesystem source of truth for audit integrity):

```bash
docker run --rm -v nomos-agents:/data -v "$PWD:/backup" alpine \
  tar czf /backup/nomos-agents-$(date +%F).tgz -C /data .
```

Always back up `nomos-pgdata`, `nomos-agents` and the Vault volumes
together so the audit index and on-disk chains stay consistent.

---

## 5. Troubleshooting

| Symptom | Likely cause / action |
|---|---|
| `compose` aborts: "Set NOMOS_DB_PASSWORD in .env" | Required secret unset. Compose uses `${VAR:?}` guards — set Step-1 secrets in `.env`. |
| `/health` → `degraded` | PostgreSQL or a dependency down. Check `docker compose logs postgres`. |
| `502` on chat | Gateway still starting or offline. `docker compose logs openclaw-gateway`; gateway offline does not fail `/health`. |
| `403` on `/api/monitoring/*` | Endpoint is admin-only; authenticate as an admin user. |
| `403` on `/api/system/unseal-key` | Setup already complete (admin exists). Expected — this is break-glass-only. |
| `401`/`403` on chat or agent state-change | Not authenticated or not the agent owner (`check_agent_access`). |
| Vault sealed after restart | Re-run/inspect `vault-init`; check `docker compose logs vault vault-init`. |
| Worker not running jobs | `docker compose logs nomos-worker`; healthcheck imports `arq`; cron defined in `nomos-api/nomos_api/worker/main.py:62-83`. |
| Need CLI debug detail | Set `NOMOS_LOG_LEVEL=DEBUG` — structured JSON diagnostics go to stderr; normal output stays on stdout. |
| Port conflicts (80/443/3040/8060) | Override `NOMOS_HTTP_PORT`/`NOMOS_HTTPS_PORT`/`NOMOS_CONSOLE_PORT`/`NOMOS_API_PORT` in `.env`. |

Logs:

```bash
docker compose logs -f                # all services
docker compose logs -f nomos-api      # one service
```

Structured API logs are JSON and credential-redacted
(`nomos-api/nomos_api/middleware/logging.py`): token blobs, Bearer
tokens and known secret-key values are scrubbed before emission.

---

## 6. Routine operations

- **Upgrade:** `git pull` → review `docker-compose.yml` / Dockerfile
  pin changes (OpenClaw is pinned to `2026.5.18` in
  `nomos-plugin/Dockerfile.gateway:1`, never `:latest`) →
  `docker compose build` → `docker compose up -d`.
- **Migrations:** the API applies Alembic migrations on startup; verify
  with `docker compose logs nomos-api | grep -i alembic`.
- **Restart a single service:** `docker compose restart nomos-api`.
- **Graceful shutdown:** `docker compose down` (volumes are preserved;
  do **not** use `-v` unless you intend to wipe data).
