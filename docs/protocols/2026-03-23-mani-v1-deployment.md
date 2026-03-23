# Mani v1 Deployment Protocol — NomOS Pilot #1

| Field          | Value                                      |
|----------------|--------------------------------------------|
| Date           | 2026-03-23                                 |
| Deployer       | Joe (via HQ dispatcher)                    |
| Agent          | Mani Ruf (mani-v1)                         |
| Manifest Hash  | 1613431064a99aec...                        |
| Status         | PRE-DEPLOYMENT (validation complete)       |

---

## Step 0.4.1: Create Mani Manifest from Template

- **Timestamp**: 2026-03-23
- **Source**: `templates/external-secretary/manifest.yaml`
- **Output**: `templates/external-secretary/mani-v1-manifest.yaml`
- **Changes from template**:
  - `agent.id`: `mani-ruf-01` -> `mani-v1`
  - `identity.display_name`: added `| AI Engineering` suffix
  - `identity.company`: `Phantom AI GmbH` -> `AI Engineering`
  - `identity.email`: `mani@phantom-ai.de` -> `r.mani.stack@gmx.at`
  - `memory.namespace`: `mani-ruf-01` -> `mani-v1`
- **Result**: OK

## Step 0.4.2: Validate Manifest

- **Timestamp**: 2026-03-23
- **Tool**: `nomos-cli` manifest_validator (v0.1.0)
- **Validation result**: VALID
- **Manifest hash**: `1613431064a99aec...`
- **Agent**: Mani Ruf (mani-v1)
- **Role**: external-secretary
- **Risk class**: limited
- **Result**: OK

## Step 0.4.3: Deployment Protocol

- **This document** serves as the audit trail for Mani's deployment.
- Created at: `docs/protocols/2026-03-23-mani-v1-deployment.md`

## Step 0.4.4: OpenClaw Config Verification

- **File**: `C:\Users\Legion\.openclaw\openclaw.json`
- **API Key check**:
  - `NVIDIA_API_KEY`: uses `${NVIDIA_API_KEY}` — OK
  - `MOONSHOT_API_KEY`: uses `${MOONSHOT_API_KEY}` — OK
  - `BRAVE_API_KEY`: uses `${BRAVE_API_KEY}` — OK
  - `ELEVENLABS_API_KEY`: uses `${ELEVENLABS_API_KEY}` — OK
  - `MATTERMOST_BOT_TOKEN`: uses `${MATTERMOST_BOT_TOKEN}` — OK
  - `SAG_API_KEY`: uses `${SAG_API_KEY}` — OK
- **FINDING**: `gateway.auth.token` contains a hardcoded token value (`9e42...5e5`). This is a static gateway auth token, not an external API key. Noted but NOT modified per instructions.
- **Result**: All external API keys use env-var references. One hardcoded gateway token noted.

## Step 0.4.5: Service Status Check

| Service             | Endpoint                                  | Status        |
|---------------------|-------------------------------------------|---------------|
| OpenClaw Gateway    | `http://127.0.0.1:18789/health`           | UNREACHABLE   |
| Honcho API          | `http://10.40.10.82:8055/docs`            | UP (Swagger UI responding) |
| Mattermost          | `http://10.40.10.83:8065/api/v4/system/ping` | UP (status: OK) |

- **OpenClaw Gateway**: Not running. Expected — gateway start requires Joe's manual intervention.
- **Honcho**: Running, API docs accessible.
- **Mattermost**: Running, system ping returns OK.

## Next Steps (require Joe)

1. Start OpenClaw Gateway manually
2. Register Mani agent in gateway
3. Run first end-to-end test session
4. Verify Honcho memory namespace isolation for `mani-v1`
5. Confirm Mattermost channel binding
