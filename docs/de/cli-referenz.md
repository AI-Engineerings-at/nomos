# NomOS CLI-Referenz

## Installation

```bash
cd nomos-cli
pip install -e .
nomos --version
```

Erfordert Python 3.11+.

---

## Globale Optionen

```
nomos --version    Version anzeigen (0.1.0) und beenden
nomos --help       Hilfe anzeigen und beenden
```

---

## nomos hire

Neuen AI Agent mit vollstaendigem Compliance-Manifest, Hash-Integritaet und Audit-Chain erstellen.

### Verwendung

```bash
nomos hire --name NAME --role ROLE --company COMPANY --email EMAIL \
  [--risk-class CLASS] --output-dir DIR
```

### Optionen

| Flag | Pflicht | Standard | Beschreibung |
|------|---------|----------|-------------|
| `--name` | ja | — | Agent-Name (z.B. `"Mani Ruf"`) |
| `--role` | ja | — | Agent-Rolle (z.B. `"external-secretary"`) |
| `--company` | ja | — | Firmenname (z.B. `"Acme GmbH"`) |
| `--email` | ja | — | Agent-Email-Adresse |
| `--risk-class` | nein | `limited` | EU AI Act Risikoklasse: `minimal`, `limited` oder `high` |
| `--output-dir` | ja | — | Ausgabeverzeichnis fuer Agent-Dateien |

### Was erstellt wird

```
<output-dir>/
  manifest.yaml        Agent-Manifest (Pydantic-validiertes YAML)
  manifest.sha256      SHA-256 Hash des Manifests
  compliance/          Leeres Verzeichnis fuer Compliance-Dokumente
  audit/chain.jsonl    Hash-Chain mit "agent.created" Event
```

### Beispiel

```bash
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf
```

Ausgabe:

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

### Exit-Codes

- `0` — Agent erfolgreich erstellt
- `1` — Fehler (Verzeichnis existiert, ungueltiger Name, Validierungsfehler)

---

## nomos gate

Alle Pflicht-Compliance-Dokumente fuer einen Agent generieren. Dies ist das Compliance Gate — es generiert die 5 EU AI Act + DSGVO Dokumente aus dem Agent-Manifest.

### Verwendung

```bash
nomos gate --agent-dir DIR
```

### Optionen

| Flag | Pflicht | Standard | Beschreibung |
|------|---------|----------|-------------|
| `--agent-dir` | ja | — | Pfad zum Agent-Verzeichnis (muss `manifest.yaml` enthalten) |

### Generierte Dokumente

| # | Dokument | Dateiname | Rechtsgrundlage |
|---|----------|----------|-----------------|
| 1 | DPIA | `compliance/dpia.md` | Art. 35 DSGVO |
| 2 | Verarbeitungsverzeichnis | `compliance/verarbeitungsverzeichnis.md` | Art. 30 DSGVO |
| 3 | Transparenzerklaerung | `compliance/art50_transparency.md` | Art. 50 EU AI Act |
| 4 | Human Oversight Policy | `compliance/art14_killswitch.md` | Art. 14 EU AI Act |
| 5 | Record-Keeping Policy | `compliance/art12_logging.md` | Art. 12 EU AI Act |

### Beispiel

```bash
nomos gate --agent-dir ./data/agents/mani-ruf
```

Ausgabe:

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

Wenn Dokumente bereits existieren, beendet sich der Befehl fruehzeitig:

```
All compliance documents already exist.
```

### Exit-Codes

- `0` — Dokumente generiert (oder existieren bereits)
- `1` — Fehler (kein manifest.yaml gefunden)

---

## nomos verify

Vollstaendige Compliance-Verifikation durchfuehren: Manifest-Schema, Compliance-Dokumente, Manifest-Hash-Integritaet und Audit-Chain-Integritaet.

### Verwendung

```bash
nomos verify --agent-dir DIR
```

### Optionen

| Flag | Pflicht | Standard | Beschreibung |
|------|---------|----------|-------------|
| `--agent-dir` | ja | — | Pfad zum Agent-Verzeichnis (muss `manifest.yaml` enthalten) |

### Durchgefuehrte Pruefungen

| Pruefung | Was verifiziert wird |
|----------|---------------------|
| Manifest Schema | Pydantic v2 Validierung von manifest.yaml |
| Compliance Gate | Alle 5 Pflichtdokumente existieren und sind nicht leer |
| Manifest Hash | manifest.sha256 stimmt mit neuberechnetem SHA-256 ueberein |
| Audit Chain | Hash-Chain-Integritaet (Hash und Chain-Verkettung jedes Eintrags) |

### Beispiel

```bash
nomos verify --agent-dir ./data/agents/mani-ruf
```

Ausgabe (alle bestanden):

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

### Exit-Codes

- `0` — Alle Pruefungen bestanden
- `1` — Eine Pruefung fehlgeschlagen (blockierte Compliance, Hash-Mismatch oder Chain ungueltig)

---

## nomos fleet

Alle Agents in einem lokalen Verzeichnis auflisten. Scannt nach Unterverzeichnissen die `manifest.yaml`-Dateien enthalten.

### Verwendung

```bash
nomos fleet [--agents-dir DIR]
```

### Optionen

| Flag | Pflicht | Standard | Beschreibung |
|------|---------|----------|-------------|
| `--agents-dir` | nein | `./data/agents` | Verzeichnis mit Agent-Unterverzeichnissen |

### Beispiel

```bash
nomos fleet --agents-dir ./data/agents
```

Ausgabe:

```
       NomOS Fleet (2 agents)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID         ┃ Name       ┃ Role               ┃ Risk    ┃ Compliance ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ mani-ruf   │ Mani Ruf   │ external-secretary │ limited │ passed     │
│ alex-test  │ Alex Test  │ research-agent     │ minimal │ blocked    │
└────────────┴────────────┴────────────────────┴─────────┴────────────┘
```

### Exit-Codes

- `0` — Immer (auch wenn keine Agents gefunden)

---

## nomos audit

Audit Trail fuer einen Agent anzeigen oder verifizieren.

### Verwendung

```bash
nomos audit --agent-dir DIR [--verify]
```

### Optionen

| Flag | Pflicht | Standard | Beschreibung |
|------|---------|----------|-------------|
| `--agent-dir` | ja | — | Pfad zum Agent-Verzeichnis |
| `--verify` | nein | `false` | Chain-Integritaet verifizieren statt Eintraege anzuzeigen |

### Beispiel: Audit Trail anzeigen

```bash
nomos audit --agent-dir ./data/agents/mani-ruf
```

Ausgabe:

```
          Audit Trail
┏━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Event          ┃ Agent      ┃ Timestamp          ┃ Hash               ┃
┡━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 0 │ agent.created  │ mani-ruf   │ 2026-03-24T10:00:0 │ e4f5a6b7c8d9...    │
└───┴────────────────┴────────────┴────────────────────┴────────────────────┘
```

### Beispiel: Chain-Integritaet verifizieren

```bash
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

Ausgabe (gueltig):

```
Audit chain VALID — 1 entries verified
```

Ausgabe (manipuliert):

```
Audit chain INVALID
  - Entry 0: hash mismatch (stored=e4f5a6b7c8d9..., computed=1234567890ab...)
```

### Exit-Codes

- `0` — Trail angezeigt oder Chain gueltig
- `1` — Chain ungueltig (mit `--verify`) oder kein Audit-Verzeichnis
