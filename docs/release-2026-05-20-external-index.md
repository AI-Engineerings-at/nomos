# Release 0.2.0 — External Indexing Punchlist

> Erstellt 2026-05-20 nach Abschluss der Audit-Trail-v2-Linie
> (PRs #5-#9). Mappt die Release-Artefakte auf die externen
> Wissens-/Task-/Projekt-Systeme im AI-Engineering-Ökosystem.

## Aufteilung (strukturiert, per Joe's Anweisung 2026-05-20)

| Kategorie | Ziel-System | Was wohin |
|---|---|---|
| **Wissen** | open-notebook (`10.40.10.82:5055`) → Notebook `v7s87re90iyxxlv7dd5x` (AI Engineering KB) | Audit-Trail v2 als referenzierbare Source — Ed25519, RFC 6962, EU AI Act Art. 12 |
| **Tasks** | ERPNext (`10.40.10.82:8082`) | PRs #5-#9 als abgeschlossene Tasks, Phase-K (vault-init + anchors-volume) als Follow-up-Tasks, K-Tasks (live-eval Run) |
| **Projekt** | `Documents/STATUS.md` + `Documents/wiki/` | STATUS.md ✅ aktualisiert (nomos-Zeile auf 0.2.0). Wiki-Eintrag offen (Next.js-Project, separater Job) |
| **Code** | `AI-Engineering-at/nomos` | ✅ Tag `v0.2.0` gepusht, GitHub Release auto-generiert via release.yml |

---

## 1. open-notebook (Wissen) — empfohlene Source-Einträge

| Titel | Inhalt | Tags |
|---|---|---|
| **NomOS 0.2.0 — Audit-Trail v2** | Was 0.2.0 bringt: Ed25519 + HMAC + externe Anker + RFC 6962 Merkle-Transparency-Log. Vor EU AI Act Art. 12 (wirksam 2026-08-02). Link: `CHANGELOG.md` Section `[0.2.0]`. | `eu-ai-act` `audit-trail` `nomos` `compliance` `rfc-6962` |
| **Ed25519 Audit-Signatures Pattern** | Warum HMAC allein nicht reicht (Single-Key-Leak = Retroactive-Forgery). Ed25519 als Public-Key-Verifizierung ohne Shared-Secret. Implementierung: `nomos-cli/nomos/core/hash_chain.py`. | `ed25519` `cryptography` `audit` `non-repudiation` |
| **RFC 6962 Merkle-Log für Audit-Trails** | Implementation: `nomos-cli/nomos/core/merkle.py`. Sigstore-Rekor-Pattern ohne Trillian. STH + Inclusion-Proofs erlauben Regulator-Verifikation einzelner Events mit Public-Key allein. | `merkle` `transparency-log` `sigstore` `rekor` |
| **EU AI Act Art. 12 Implementation** | Event-Mapping (a/b/c), 180-Tage-Retention-Floor, durchgesetzt über Manifest-Validierung + tägliche `audit_integrity_checkpoint`-Cron. Quelle: `docs/compliance-guide.md`. | `eu-ai-act` `art-12` `record-keeping` `retention` |

**Befehl:** `/full-sync` (orchestriert open-notebook source-creation laut Top-Level CLAUDE.md).

---

## 2. ERPNext (Tasks) — empfohlene Task-Einträge

### Bereits abgeschlossen (Tasks zum Closing)

- **TASK** „PR #5: Audit-Trail Phase-A1 — Ed25519 signatures" — geschlossen 2026-05-20, Commit `47b8809`.
- **TASK** „PR #6: Audit-Trail Phase-A2/A3/A5 — Anchoring + Retention + Verify enrichment" — geschlossen 2026-05-20, Commit `20ee2c1`.
- **TASK** „PR #7: Audit-Trail Phase-B1 — RFC 6962 Merkle transparency log" — geschlossen 2026-05-20, Commit `c1602b8`.
- **TASK** „PR #8: 0.2.0 Release — CHANGELOG + version bump" — geschlossen 2026-05-20, Commit `e6f948e`.
- **TASK** „PR #9: 0.2.0 follow-up — docs sync + CI hardening + Phase-K source gaps" — geschlossen 2026-05-20, Commit `4822f54`.

### Follow-up (offen — empfohlene neue Tasks)

- **TASK** „Phase-I live-eval auf clean docker-compose Stack" — Procedure in `docs/hardening-2026-05-20/EVAL-2026-05-20.md`. Erst nach diesem Lauf ist 0.2.0 wirklich „regulator-ready".
- **TASK** „Wiki-Eintrag `nomos.md` im `Documents/wiki/` Next.js Repo" — separater Cross-Project-Job, nicht autonom erledigbar.
- **TASK** „Phase-B2 evaluieren: opt-in Sigstore-Rekor public anchoring" — offen, Datenschutz-Trade-off (`PLAN.md` Phase-B2).
- **TASK** „WORM-Storage-Backing für `nomos-anchors` Volume in Produktions-Deployment dokumentieren" — Operator-Concern, gehört in einen Deployment-Guide.

---

## 3. STATUS.md (Projekt-Cockpit)

✅ Erledigt:
- `Documents/STATUS.md` Zeile 595: nomos-Eintrag von „324+ Tests" auf
  „v0.2.0 LIVE, 693+ Tests, Audit-Trail v2 (Phase A1-A6 + B1), PRs
  #5-#9 merged 2026-05-20" gehoben.

---

## 4. Wiki (Documents/wiki/, Next.js)

Offen. Wiki ist ein eigenes Next.js-Repo (`AI-Engineering-at/wiki`).
Empfohlener Eintrag: Seite `Produkte/NomOS` mit Kurz-Pitch + Link
auf `https://github.com/AI-Engineering-at/nomos` + Hinweis auf
Release `v0.2.0`. Cross-Project-Job, nicht in dieser Session erledigt.

---

## Verifikation (was hier wirklich verifiziert wurde)

- `gh release view v0.2.0` → published 2026-05-20T03:01:20Z, author
  github-actions[bot] (release.yml hat auto-getriggert).
- `STATUS.md` diff: 1 Zeile geändert, Inhalt nomos-Stand 0.2.0.
- Dieses Indexing-Punchlist-Dokument: lokal in
  `docs/release-2026-05-20-external-index.md` committed.
- ERPNext + open-notebook + Wiki: **NICHT** in dieser autonomen
  Session bespielt — gehört in einen `/full-sync` Lauf oder eine
  separate, Cred-bewusste Session.
