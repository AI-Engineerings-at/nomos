# OpenClaw + NemoClaw — Vollstaendige Technische Referenz

> Verifiziert am 25.03.2026 aus offiziellen Quellen + funktionierender Kimi-Referenz.
> Diese Datei ist die EINZIGE Wahrheitsquelle fuer OpenClaw/NemoClaw-Integration in NomOS.
> open-notebook: note:yvfdrdgdozeqcztjncwm

---

## 1. OpenClaw — Ueberblick

| Feld | Wert |
|------|------|
| GitHub | https://github.com/openclaw/openclaw |
| Docs | https://docs.openclaw.ai |
| Lizenz | MIT |
| Sprache | TypeScript (ESM) |
| Stars | ~335.000 |
| Docker Image | `ghcr.io/openclaw/openclaw:latest` |
| Default Port | 18789 |
| Config | `~/.openclaw/openclaw.json` (JSON5) |
| ClawHub | https://clawhub.ai (Skill Directory) |
| Beschreibung | Personal AI Assistant Framework, lokaler Gateway, 20+ Messaging-Kanaele |

## 2. OpenClaw Gateway

### Environment Variables (verifiziert)

- `OPENCLAW_GATEWAY_TOKEN` — Auth-Token fuer Gateway-Zugriff
- `OPENCLAW_GATEWAY_PASSWORD` — Alternative Auth per Passwort
- `OPENCLAW_STATE_DIR` — Default `~/.openclaw`
- `OPENCLAW_CONFIG_PATH` — Default `~/.openclaw/openclaw.json`
- `OPENCLAW_LOAD_SHELL_ENV` — Shell-Environment importieren
- Provider-Keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

### Health Endpoints (WICHTIG — nicht /health!)

- **`/healthz`** — Liveness Probe (unauthenticated)
- **`/readyz`** — Readiness Probe (unauthenticated)
- Deeper Health: nur via CLI mit Token

### Gateway Config (funktionierende Referenz aus Kimi-Projekt)

```json
{
  "tools": { "profile": "coding", "fs": { "workspaceOnly": true } },
  "commands": { "native": "auto", "nativeSkills": "auto", "restart": true },
  "session": { "dmScope": "per-channel-peer" },
  "discovery": { "mdns": { "mode": "off" } },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "enabled": true,
      "allowedOrigins": ["http://localhost:18789", "http://127.0.0.1:18789"],
      "allowInsecureAuth": false
    },
    "auth": { "mode": "token", "token": "CHANGE-ME" }
  }
}
```

### Bind Modes

- `"lan"` — Lauscht auf allen Interfaces (fuer Docker Container NOETIG!)
- `"loopback"` — Nur 127.0.0.1 (NICHT in Docker verwenden!)
- Legacy: `0.0.0.0` und `127.0.0.1` sind EXPLIZIT ABGERATEN

## 3. OpenClaw Plugin System

### Plugin Entry Point (KORREKT — nicht export default function!)

```typescript
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export default definePluginEntry({
  id: "nomos",
  name: "NomOS",
  description: "EU AI Act + DSGVO compliance",
  register(api) {
    // Hooks und Tools registrieren
  },
});
```

### Plugin Manifest (openclaw.plugin.json)

```json
{
  "id": "nomos",
  "name": "NomOS",
  "configSchema": { "type": "object", "additionalProperties": false }
}
```

### Registration API (api Objekt)

| Methode | Registriert |
|---------|------------|
| `api.registerProvider(...)` | LLM Text Inference |
| `api.registerChannel(...)` | Messaging Channel |
| `api.registerSpeechProvider(...)` | TTS/STT |
| `api.registerTool(tool, opts?)` | Agent-Tool |
| `api.registerCommand(def)` | Custom Command |
| `api.registerHook(events, handler, opts?)` | Event Hook |
| `api.registerHttpRoute(params)` | Gateway HTTP-Endpunkt |
| `api.registerGatewayMethod(name, handler)` | Gateway RPC |
| `api.registerCli(registrar, opts?)` | CLI Subcommand |
| `api.registerService(service)` | Background Service |
| `api.on(hookName, handler, opts?)` | Typed Lifecycle Hook |

### api Objekt Felder

- `api.id`, `api.name`, `api.version`
- `api.config` — Gateway Config
- `api.pluginConfig` — Plugin-spezifische Config
- `api.logger` — `{ info, warn, error, debug }`
- `api.runtime` — Agent, Subagent, TTS, Config, System, Events
- `api.resolvePath(input)` — Pfad-Resolution

### api.runtime Namespaces

- `api.runtime.agent` — Agent Identity, Workspace, Sessions
- `api.runtime.subagent` — Subagent-Runs starten/warten
- `api.runtime.tts` — Text-to-Speech
- `api.runtime.config` — Config laden/schreiben
- `api.runtime.system` — System Events, Heartbeat
- `api.runtime.events` — Event Subscriptions

### Hook Decision Semantics

- `before_tool_call`: `{ block: true }` = TERMINAL (untere Handler uebersprungen)
- `message_sending`: `{ cancel: true }` = TERMINAL
- `tool_result_persist`: SYNCHRON (kein async!)

### Plugin Installation

```bash
openclaw plugins install <package-name>  # Sucht ClawHub, dann npm
```

### Plugin-Verzeichnis

- Extensions: `~/.openclaw/extensions/<name>/`
- Im Container: `/home/node/.openclaw/extensions/<name>/`
- Docker ENV: `OPENCLAW_PLUGINS_DIR` (nicht offiziell dokumentiert, aus docker-compose abgeleitet)

## 4. OpenClaw Docker Deployment

### Offizielles Image

`ghcr.io/openclaw/openclaw` (Tags: `latest`, `main`, `<version>` z.B. `2026.2.26`)

### Docker Compose (aus Kimi-Referenz, funktioniert)

```yaml
services:
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:latest
    ports:
      - "18789:18789"
    volumes:
      - ./config/openclaw.json:/home/node/.openclaw/openclaw.json:ro
      - ./workspace:/home/node/.openclaw/workspace
      - ./extensions:/home/node/.openclaw/extensions
      - ./logs:/home/node/.openclaw/logs
      - ./sessions:/home/node/.openclaw/sessions
    environment:
      - OPENCLAW_GATEWAY_TOKEN=your-token-here
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

### Volume Mounts (WICHTIG — Container-Pfade!)

| Host | Container | Zweck |
|------|-----------|-------|
| `./config/openclaw.json` | `/home/node/.openclaw/openclaw.json:ro` | Gateway Config |
| `./workspace` | `/home/node/.openclaw/workspace` | Agent Workspace |
| `./extensions` | `/home/node/.openclaw/extensions` | Plugins |
| `./logs` | `/home/node/.openclaw/logs` | Log-Dateien |
| `./sessions` | `/home/node/.openclaw/sessions` | Session-Daten |

## 5. OpenClaw Agent-Konfiguration

- `AGENTS.md` — Repository-Guidelines
- `SOUL.md` — Agent-Persoenlichkeit (via onlycrabs.ai Registry)
- `IDENTITY.md` — Agent-Identitaet
- `TOOLS.md` — Tool-Konfiguration
- Workspace: `~/.openclaw/workspace/`
- Multi-Agent: `agents.list[]` Konfiguration
- 50+ Bundled Skills (1password, github, notion, slack, etc.)

## 6. OpenClaw Onboarding

Befehl: `openclaw onboard`
7 Schritte: Model/Auth → Workspace → Gateway → Channels → Daemon → Health → Skills
Modi: QuickStart (Defaults) vs Advanced
Automation: `--non-interactive` Flag

---

## 7. NemoClaw — Ueberblick

| Feld | Wert |
|------|------|
| GitHub | https://github.com/NVIDIA/NemoClaw |
| Lizenz | Apache 2.0 |
| Status | **Alpha** (seit 16.03.2026) |
| Stars | ~16.700 |
| Sprache | TypeScript (Plugin) + Python (Blueprint) |
| Baut auf | NVIDIA OpenShell (Rust Runtime) |
| Beschreibung | Security-Wrapper der OpenClaw in gehaerteten Containern ausfuehrt |

### WICHTIG: NemoClaw ist KEIN Docker-Service!

NemoClaw ist ein **CLI-Tool + Blueprint-System** das Sandbox-Container DYNAMISCH erstellt.
Es gehoert NICHT als fester Service in docker-compose.
Die Sandbox-Container werden **pro Agent** erstellt und verwaltet.

## 8. NemoClaw Installation (v0.0.14 - April 13, 2026)

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
# Startet automatisch nemoclaw onboard
```

Installiert: Node.js (falls noetig) + OpenShell Gateway + nemoclaw CLI

## 9. NemoClaw Architektur

| Komponente | Rolle |
|------------|-------|
| Plugin | TypeScript CLI (nemoclaw-Befehle) |
| Blueprint | Versioniertes Python-Artefakt (Sandbox, Policy, Inference) |
| Sandbox | Isolierter OpenShell-Container mit OpenClaw |
| Inference | Provider-geroutete Modellaufrufe ueber OpenShell Gateway |

### Sandbox-Image

`ghcr.io/nvidia/openshell-community/sandboxes/openclaw:latest` (~2.4 GB)

### Hardware-Anforderungen

4 vCPU, 8 GB RAM, 20 GB Disk

### Unterstuetzte Runtimes

- Linux: Docker
- macOS (Apple Silicon): Colima, Docker Desktop
- Windows: Docker Desktop (WSL-Backend)

## 10. NemoClaw Sicherheit (4 Schichten)

| Schicht | Schuetzt | Wann |
|---------|----------|------|
| Network | Blockiert unautorisierte Verbindungen | Hot-reloadable |
| Filesystem | Verhindert R/W ausserhalb /sandbox + /tmp | Bei Erstellung gesperrt |
| Process | Blockiert Privilege Escalation | Bei Erstellung gesperrt |
| Inference | Leitet API-Calls an kontrollierte Backends | Hot-reloadable |

**Technologie:** Landlock + seccomp + Network Namespaces
**Network-Policy:** Deny-by-Default, Binary-restringiert

### Sandbox Dockerfile Details

- Multi-Stage Build (Node.js Builder + Runtime)
- Privilege-Separation: `gateway`-User (nicht vom Agent toetbar) + `sandbox`-User
- Immutable Config: `/sandbox/.openclaw/openclaw.json` ist root-owned, chmod 444
- Config-Integritaetspruefung via SHA256-Hash
- Writable State nur in `/sandbox/.openclaw-data/` via Symlinks

## 11. NemoClaw Blueprint System

`blueprint.yaml` definiert:
- Version: 0.1.0
- Min: OpenShell 0.1.0, OpenClaw 2026.3.0
- Sandbox-Image + Port-Forwarding

### 4 Inference-Profile

1. `default` — NVIDIA Endpoints (nemotron-3-super-120b-a12b)
2. `ncp` — NVIDIA Cloud Platform mit dynamischem Endpoint
3. `nim-local` — Lokaler NIM-Service
4. `vllm` — Lokaler vLLM-Server

### Policy-Presets

discord, docker, huggingface, jira, npm, outlook, pypi, slack, telegram

## 12. NemoClaw CLI

| Befehl | Beschreibung |
|--------|-------------|
| `nemoclaw onboard` | Interaktiver Setup-Wizard |
| `nemoclaw <name> connect` | Shell in Sandbox |
| `nemoclaw <name> status` | Status pruefen |
| `nemoclaw <name> logs --follow` | Logs anzeigen |
| `nemoclaw start/stop/status` | Dienste verwalten |
| `openshell term` | TUI fuer Monitoring + Approvals |
| `openshell policy set <file>` | Policy dynamisch aendern |
| `openshell sandbox list` | Sandbox-Status |

### Inference-Routing

Credentials bleiben auf dem Host in `~/.nemoclaw/credentials.json`.
Die Sandbox sieht nur `inference.local` — nie den echten Provider-Key.

## 13. NemoClaw Docker-Integration (aus Kimi-Referenz)

Fuer NemoClaw-Typ-Instanzen wird ein Policy-Agent Sidecar gestartet:

```yaml
nemoclaw-policy-agent:
  image: ghcr.io/nvidia/openshell/policy-agent:latest
  volumes:
    - ./config/policy.yaml:/etc/openshell/policy.yaml:ro
  depends_on: [gateway]
  privileged: true
```

---

## 14. Implikationen fuer NomOS

### Was an NomOS geaendert werden MUSS

1. **Plugin Entry**: `definePluginEntry()` statt `export default function register()`
2. **Health Check**: `/healthz` statt `/health` in docker-compose
3. **Volume Mounts**: `/home/node/.openclaw/` Pfade statt `/plugins/` und `/data/`
4. **NemoClaw**: KEIN Docker Service — CLI-basiert, Sandbox-Container dynamisch
5. **Gateway Config**: `openclaw.json` Datei mounten mit modernem Format
6. **Plugin-Verzeichnis**: `/home/node/.openclaw/extensions/nomos/` statt `/plugins/nomos/`
7. **Gateway Token**: Auth-Token konfigurieren fuer API-Zugriff

### Was an NomOS KORREKT war

1. `api.on(hookName, handler, { priority })` — stimmt
2. `openclaw.plugin.json` Format — grundsaetzlich korrekt
3. Port 18789 — stimmt
4. Docker Image `ghcr.io/openclaw/openclaw:latest` — stimmt
5. `bind: "lan"` fuer Docker — stimmt
6. Hook-Namen (gateway_start, before_agent_start, etc.) — muessen noch verifiziert werden

### NemoClaw-Integration in NomOS

NemoClaw ist OPTIONAL und nur sinnvoll wenn:
- Der Kunde maximale Sandbox-Isolation will
- NVIDIA Hardware/Services verfuegbar sind
- Alpha-Status akzeptabel ist

Fuer NomOS v2: OpenClaw Gateway OHNE NemoClaw starten.
NemoClaw als optionales Add-on in spaeterer Phase.

---

## Quellen

- https://github.com/openclaw/openclaw
- https://docs.openclaw.ai
- https://docs.openclaw.ai/install/docker
- https://docs.openclaw.ai/start/wizard
- https://docs.openclaw.ai/concepts/models
- https://github.com/NVIDIA/NemoClaw
- https://docs.nvidia.com/nemoclaw/latest/reference/commands.html
- https://github.com/NVIDIA/OpenShell
- Kimi-Projekt: `Kimi/infra/runtime/gateway/config/openclaw.json`
- Kimi-Projekt: `Kimi/docs/EXTERNAL_RUNTIME_REFERENCES.md`
- Kimi-Projekt: `Kimi/core/protocol/wizard/openclaw_gateway.py`
