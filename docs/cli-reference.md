# NomOS CLI Reference

## Installation

```bash
cd nomos-cli
pip install -e .
nomos --version
```

Requires Python 3.11+.

---

## Global Options

```
nomos --version    Show version (0.1.0) and exit
nomos --help       Show help and exit
```

---

## nomos hire

Create a new AI agent with full compliance manifest, hash integrity, and audit chain.

### Usage

```bash
nomos hire --name NAME --role ROLE --company COMPANY --email EMAIL \
  [--risk-class CLASS] --output-dir DIR
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | yes | — | Agent name (e.g. `"Mani Ruf"`) |
| `--role` | yes | — | Agent role (e.g. `"external-secretary"`) |
| `--company` | yes | — | Company name (e.g. `"Acme GmbH"`) |
| `--email` | yes | — | Agent email address |
| `--risk-class` | no | `limited` | EU AI Act risk class: `minimal`, `limited`, or `high` |
| `--output-dir` | yes | — | Output directory for agent files |

### What it creates

```
<output-dir>/
  manifest.yaml        Agent manifest (Pydantic-validated YAML)
  manifest.sha256      SHA-256 hash of the manifest
  compliance/          Empty directory for compliance documents
  audit/chain.jsonl    Hash chain with "agent.created" event
```

### Example

```bash
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf
```

Output:

```
╭──────── nomos hire ────────╮
│ Agent created: Mani Ruf    │
│ ID: mani-ruf               │
│ Role: external-secretary   │
│ Risk Class: limited        │
│ Manifest Hash: a1b2c3d4... │
│ Compliance: blocked        │
│ Directory: ./data/agents/  │
│            mani-ruf        │
╰────────────────────────────╯

Missing documents: dpia, verarbeitungsverzeichnis, art50_transparency, art14_killswitch, art12_logging
Run compliance gate to generate required documents.
```

### Exit codes

- `0` — Agent created successfully
- `1` — Error (directory exists, invalid name, validation failure)

---

## nomos gate

Generate all required compliance documents for an agent. This is the compliance gate — it generates the 5 EU AI Act + DSGVO documents from the agent manifest.

### Usage

```bash
nomos gate --agent-dir DIR
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--agent-dir` | yes | — | Path to agent directory (must contain `manifest.yaml`) |

### Documents generated

| # | Document | Filename | Legal Basis |
|---|----------|----------|-------------|
| 1 | DPIA | `compliance/dpia.md` | Art. 35 DSGVO |
| 2 | Verarbeitungsverzeichnis | `compliance/verarbeitungsverzeichnis.md` | Art. 30 DSGVO |
| 3 | Transparency Declaration | `compliance/art50_transparency.md` | Art. 50 EU AI Act |
| 4 | Human Oversight Policy | `compliance/art14_killswitch.md` | Art. 14 EU AI Act |
| 5 | Record-Keeping Policy | `compliance/art12_logging.md` | Art. 12 EU AI Act |

### Example

```bash
nomos gate --agent-dir ./data/agents/mani-ruf
```

Output:

```
╭──────── nomos gate ────────────────────────────╮
│ Compliance Gate: 5 documents generated         │
│                                                │
│   V dpia.md                                    │
│   V verarbeitungsverzeichnis.md                │
│   V art50_transparency.md                      │
│   V art14_killswitch.md                        │
│   V art12_logging.md                           │
│                                                │
│ Agent: Mani Ruf                                │
│ Directory: ./data/agents/mani-ruf/compliance   │
╰────────────────────────────────────────────────╯

Compliance Status: PASSED — Agent is ready for deployment.
```

If documents already exist, the command exits early:

```
All compliance documents already exist.
```

### Exit codes

- `0` — Documents generated (or already exist)
- `1` — Error (no manifest.yaml found)

---

## nomos verify

Run a full compliance verification: manifest schema, compliance documents, manifest hash integrity, and audit chain integrity.

### Usage

```bash
nomos verify --agent-dir DIR
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--agent-dir` | yes | — | Path to agent directory (must contain `manifest.yaml`) |

### Checks performed

| Check | What it verifies |
|-------|-----------------|
| Manifest Schema | Pydantic v2 validation of manifest.yaml |
| Compliance Gate | All 5 required documents exist and are non-empty |
| Manifest Hash | manifest.sha256 matches recomputed SHA-256 |
| Audit Chain | Hash chain integrity (every entry's hash and chain links) |

### Example

```bash
nomos verify --agent-dir ./data/agents/mani-ruf
```

Output (all passing):

```
      Compliance Report: Mani Ruf
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check           ┃ Status┃ Detail                    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Manifest Schema │ PASS  │ Valid                     │
│ Compliance Gate │ passed│ All documents present     │
│ Manifest Hash   │ PASS  │ Integrity verified        │
│ Audit Chain     │ PASS  │ 1 entries verified        │
└─────────────────┴───────┴───────────────────────────┘
```

### Exit codes

- `0` — All checks pass
- `1` — Any check fails (blocked compliance, hash mismatch, or chain invalid)

---

## nomos fleet

List all agents in a local directory. Scans for subdirectories containing `manifest.yaml` files.

### Usage

```bash
nomos fleet [--agents-dir DIR]
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--agents-dir` | no | `./data/agents` | Directory containing agent subdirectories |

### Example

```bash
nomos fleet --agents-dir ./data/agents
```

Output:

```
       NomOS Fleet (2 agents)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID         ┃ Name       ┃ Role               ┃ Risk    ┃ Compliance ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ mani-ruf   │ Mani Ruf   │ external-secretary │ limited │ passed     │
│ alex-test  │ Alex Test  │ research-agent     │ minimal │ blocked    │
└────────────┴────────────┴────────────────────┴─────────┴────────────┘
```

### Exit codes

- `0` — Always (even if no agents found)

---

## nomos audit

Show or verify the audit trail for an agent.

### Usage

```bash
nomos audit --agent-dir DIR [--verify]
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--agent-dir` | yes | — | Path to agent directory |
| `--verify` | no | `false` | Verify chain integrity instead of displaying entries |

### Example: Show audit trail

```bash
nomos audit --agent-dir ./data/agents/mani-ruf
```

Output:

```
          Audit Trail
┏━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Event          ┃ Agent      ┃ Timestamp          ┃ Hash               ┃
┡━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 0 │ agent.created  │ mani-ruf   │ 2026-03-24T10:00:0 │ e4f5a6b7c8d9...    │
└───┴────────────────┴────────────┴────────────────────┴────────────────────┘
```

### Example: Verify chain integrity

```bash
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

Output (valid):

```
Audit chain VALID — 1 entries verified
```

Output (tampered):

```
Audit chain INVALID
  - Entry 0: hash mismatch (stored=e4f5a6b7c8d9..., computed=1234567890ab...)
```

### Exit codes

- `0` — Trail displayed or chain valid
- `1` — Chain invalid (with `--verify`) or no audit directory
