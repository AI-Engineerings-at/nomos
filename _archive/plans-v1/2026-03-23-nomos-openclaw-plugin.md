# NomOS OpenClaw Plugin — Implementation Plan

> NomOS muss sich beim Gateway-Start registrieren wie NemoClaw.
> Nicht ein Script das nebenher laeuft, sondern ein INTEGRIERTES Plugin.

---

## Ziel

Beim `openclaw gateway` Start erscheint:

```
[plugins]   ┌─────────────────────────────────────────────────────┐
[plugins]   │  NomOS registered                                   │
[plugins]   │                                                     │
[plugins]   │  Compliance:  Gate active (10 docs signed)          │
[plugins]   │  Governance:  8 hooks enabled                       │
[plugins]   │  Vault:       Hash-chain audit active               │
[plugins]   │  Console:     http://localhost:3040                  │
[plugins]   │  Commands:    openclaw nomos <command>               │
[plugins]   └─────────────────────────────────────────────────────┘
```

Und im CLI:
```
openclaw nomos status     → Compliance Score, Agent Status
openclaw nomos verify     → Alle Checks ausfuehren
openclaw nomos hire       → Compliance Gate Wizard starten
openclaw nomos audit      → Audit Trail exportieren
```

---

## Wie OpenClaw Plugins funktionieren

Aus dem Gateway-Log und NemoClaw-Analyse:

1. Plugin-Verzeichnis: `~/.openclaw/extensions/<name>/`
2. Entry Point: `index.ts` (TypeScript)
3. Manifest: registriert Commands und Hooks
4. Lifecycle: Plugin wird beim Gateway-Start geladen

NemoClaw-Beispiel:
```
~/.openclaw/extensions/nemoclaw/   (existiert schon!)
  → Registriert sich als Plugin
  → Zeigt Banner-Box
  → Registriert `openclaw nemoclaw` Commands
```

---

## NomOS Plugin Struktur

```
~/.openclaw/extensions/nomos/
├── index.ts                    # Plugin Entry Point
├── package.json                # Dependencies
├── tsconfig.json
├── src/
│   ├── plugin.ts               # Plugin Registration + Banner
│   ├── commands/
│   │   ├── status.ts           # openclaw nomos status
│   │   ├── verify.ts           # openclaw nomos verify
│   │   ├── hire.ts             # openclaw nomos hire (startet Gate)
│   │   └── audit.ts            # openclaw nomos audit
│   ├── hooks/
│   │   ├── pre-message.ts      # Hook: VOR jeder Agent-Nachricht
│   │   ├── post-message.ts     # Hook: NACH jeder Agent-Nachricht
│   │   └── compliance-gate.ts  # Hook: Blockiert wenn Docs fehlen
│   ├── governance/
│   │   ├── safety-gate.ts      # R1: Destruktive Befehle
│   │   ├── quality-gate.ts     # R3: Placeholder/Fake
│   │   ├── credential-guard.ts # R5: API Keys
│   │   ├── kill-switch.ts      # R6: Sofort-Halt
│   │   ├── escalation.ts       # R4: Korrektur-Tracking
│   │   ├── audit-logger.ts     # R7: Hash-Chain Audit
│   │   ├── art50-labeler.ts    # Art. 50: AI-Kennzeichnung
│   │   └── session-init.ts     # Kontext bei Start
│   └── api/
│       ├── nomos-api-client.ts # Verbindung zu NomOS API :8060
│       └── honcho-client.ts    # Verbindung zu Honcho :8055
└── dist/                        # Compiled JS
```

---

## Was das Plugin TUNT bei Gateway-Start

```typescript
// index.ts (vereinfacht)
export default function register(gateway) {

  // 1. Banner anzeigen
  gateway.log.info(bannerBox({
    title: "NomOS registered",
    lines: [
      `Compliance:  ${complianceStatus}`,
      `Governance:  ${hookCount} hooks enabled`,
      `Vault:       Hash-chain audit active`,
      `Console:     http://localhost:3040`,
      `Commands:    openclaw nomos <command>`,
    ]
  }));

  // 2. Compliance Gate prufen
  const manifest = loadManifest();
  const gateResult = checkComplianceGate(manifest);
  if (gateResult === "BLOCK") {
    gateway.log.error("NomOS: Compliance Gate BLOCKED — run 'openclaw nomos hire' first");
    // Agent wird nicht gestartet
  }

  // 3. Governance Hooks registrieren
  gateway.hooks.register("pre-message", safetyGate);
  gateway.hooks.register("pre-message", credentialGuard);
  gateway.hooks.register("pre-message", qualityGate);
  gateway.hooks.register("post-message", auditLogger);
  gateway.hooks.register("post-message", art50Labeler);
  gateway.hooks.register("on-error", escalationTracker);
  gateway.hooks.register("on-kill", killSwitch);

  // 4. Commands registrieren
  gateway.commands.register("nomos status", statusCommand);
  gateway.commands.register("nomos verify", verifyCommand);
  gateway.commands.register("nomos hire", hireCommand);
  gateway.commands.register("nomos audit", auditCommand);

  // 5. Audit-Chain starten
  startAuditChain(manifest);
}
```

---

## Was sich im Master Plan aendert

**VORHER (Phase 2.1):** Hooks als separate OpenClaw Skills (SKILL.md)
**NACHHER:** Hooks als Teil des NomOS Plugin (TypeScript, nativ integriert)

Das ist BESSER weil:
- Plugin registriert sich beim Start (sichtbar wie NemoClaw)
- Hooks greifen auf Gateway-Ebene (nicht Application-Level)
- Commands unter `openclaw nomos` (einheitlich)
- Compliance Gate blockiert BEVOR Agent startet
- Audit Logger auf Gateway-Ebene (jede Nachricht, nicht nur Tool Calls)

---

## Aufwand

| Task | Was | Tage |
|------|-----|------|
| Plugin Skeleton | index.ts, package.json, Registration, Banner | 1 |
| Commands | status, verify, hire, audit | 2 |
| Governance Hooks | 8 Hooks als TypeScript (portiert von Python) | 3 |
| Compliance Gate | Pre-Start Check, Blocking, Manifest Validation | 2 |
| Audit Logger | Hash-Chain Integration, Honcho Write | 2 |
| Art. 50 Labeler | Output-Injection fuer alle Channels | 1 |
| NomOS API Client | Verbindung zu :8060 Fleet API | 1 |
| Tests | Unit + Integration | 2 |
| **Gesamt** | | **14 Tage** |

---

## Abhaengigkeiten

```
NomOS Plugin braucht:
  ✓ OpenClaw v2026.3.13 (installiert)
  ✓ NemoClaw (registriert)
  ✓ Manifest Schema (Phase 0.2 DONE)
  → NomOS API (Phase 4.1 — parallel bauen)
  → Honcho (deployed auf .82)
```

---

## Auch zu fixen (aus dem Gateway-Log)

1. **Duplicate mattermost plugin** — `plugins.entries.mattermost` + Extension kollidieren
2. **Interactions callbackUrl** — localhost nicht erreichbar von MM Server
3. **@r-mani statt @mani** — MM Username pruefen

---

## Erste Schritte

1. NemoClaw Plugin als Referenz lesen (`~/.openclaw/extensions/nemoclaw/`)
2. NomOS Plugin Skeleton erstellen
3. Banner-Box bei Gateway-Start
4. Erster Command: `openclaw nomos status`
5. Dann Hooks portieren
