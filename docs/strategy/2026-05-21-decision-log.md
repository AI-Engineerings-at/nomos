# NomOS — Decision Log: alle offenen Fragen an einem Ort

> **Zweck:** Joe's Constraint #1 ist *Übersicht*. Dieses Dokument ist
> die EINE Stelle an der jede offene Entscheidung steht — konsolidiert
> aus 4 Strategy-Docs (MASTER-PLAN §7, META-VISION §12,
> WSK-Integration §9, v0.5.0-Roadmap). Wenn die hier markierten
> Entscheidungen getroffen sind, hat der Pfad zum Goal **keine
> Gabelungen mehr** — Ausführung wird mechanisch.
>
> **Stand:** 2026-05-21, nach Joe-Runde 1. Kanonischer
> Decision-Register — ersetzt die verstreute Frage-Haltung in
> §7/§12/§9.
>
> **Joe-Runde 1 (2026-05-21) entschieden:** N1 (Lizenz), N9 (Pricing),
> N3 (Namen-Diskretion). N6 teil-beantwortet. Offen bleiben: N2, N4,
> N6-WSK-Seite + "weitere Pilot-Kunden".

---

## 1. Wie dieses Dokument zu lesen ist

5 Status-Typen — Joe muss nur 🔴 und ⚠️ aktiv durchgehen:

| Status | Bedeutung | Joe-Aktion |
|---|---|---|
| 🔴 **OFFEN** | Strategisch/faktisch, keine sichere Empfehlung möglich | **entscheiden** |
| ⚠️ **KONFLIKT** | Alte Empfehlung kollidiert mit einer Joe-Korrektur | **auflösen** |
| 🟡 **EMPFOHLEN** | Claude-Empfehlung liegt vor | ratifizieren (Default: ja) |
| 🟢 **CLAUDE** | Rein technisch — Claude entscheidet, hier nur Transparenz | nichts |
| ✅ **ENTSCHIEDEN** | Fix, hier nur als Record | nichts |

**ID-Schema:** `M1–M19` = MASTER-PLAN §7 (Nummer identisch).
`N1–N9` = neu, nicht in §7. `DEC-00x` = Zeroth-Decisions.

---

## 2. Übersicht — alle 28 Entscheidungen auf einen Blick

| ID | Thema | Status | Blockt | Deadline |
|---|---|---|---|---|
| **N1** | Lizenz final | ✅ **AGPL-3.0 + Trademark** | — | erledigt |
| **N9** | Pricing-Philosophie | ✅ **individuell pro Kunde** | — | erledigt (Zahlen nach Pilot) |
| **N3** | Pilot-Kunde-Namen in Docs | ✅ **anonym, strikt** | — | erledigt |
| **M2** | `nomos-core` PyPI-Publish | 🟡 EMPFOHLEN | v0.6.0, WSK-Modell-2 | **diese Woche** |
| **N5** | WSK-Integration: Modell 2+3 | 🟡 EMPFOHLEN | Hash-Chain-Format-Contract | **diese Woche** |
| **N6** | WSK-Pilot-0 = Pilot-Kandidat? | 🟡 teil-offen | Pilot-Planung-Klarheit | WSK-Seite prüfen |
| **N4** | Atlas customer-shippable? | 🔴 OFFEN | v0.7 Scope, WSK-Onboarding | Juni |
| **N2** | Trademark-Anwalt — wann? | 🔴 OFFEN | OSS-Release | vor OSS-Release |
| **M9** | Funding: AWS-first / EU-parallel | ⚠️→Reframe | nichts (Lottogewinn) | Q3 |
| **M10** | Wann Customer-Acquisition | ⚠️→Reframe | Pre-Sale-Framing | jetzt |
| **N7** | Quadrupel-Center in META-VISION | 🟡 EMPFOHLEN | META-VISION-Update | Juni |
| **N8** | Hermes als NomOS-Backend | 🟡 EMPFOHLEN | nichts (defer) | — |
| **M1** | Atlas als NomOS-Pilot-Customer #0 | 🟡 EMPFOHLEN | v0.7 Dogfood-Demo | Juni |
| **M19** | Asqav adoptieren oder eigene Chain | 🟡 EMPFOHLEN | nichts (Chain bleibt) | v0.5.0 |
| **M13** | Customer-Hardware-SKU | 🟡 EMPFOHLEN | v1.0-Marketing | v1.0.0 |
| **M15** | DPIA — wer (externer DSB) | 🟡 EMPFOHLEN | v0.9.0 | Juni-Kontakt |
| **M16** | Pentest — Firma, Budget, Timing | 🟡 EMPFOHLEN | v1.0.0 | Juni-Buchung |
| **M7** | Sigstore Rekor public anchoring | 🟡 EMPFOHLEN | v1.1+ | v1.1+ |
| **M5** | NemoClaw-Activation als Backend | 🟡 EMPFOHLEN | nichts (defer) | v1.1+ |
| **M3** | Multi-Tenant DB-Isolation | 🟢 CLAUDE | v0.9.0 | v0.9.0 |
| **M4** | OpenAPI-driven Plugin-Contract | 🟢 CLAUDE | v0.7.0 | v0.7.0 |
| **M6** | Vault-TLS-Migration | 🟢 CLAUDE | v0.6.0 | v0.6.0 |
| **M8** | Customer-Migration-Path | 🟢 CLAUDE | v1.0.0 | v1.0.0 |
| **M12** | `/full-sync` Timing | 🟢 CLAUDE | nichts | v0.5.0-Tag |
| **M14** | Atlas-Phase-4 ‖ v0.7 | 🟢 CLAUDE | nichts | jetzt |
| **M11** | Pilot-Customer #1 | ✅ ENTSCHIEDEN | — | Pilot-Kandidat |
| **M17** | Pricing — €499 Flat | ⚠️ → ersetzt durch N9 | — | obsolet |
| **M18** | Lineage Engine — deferred | ✅ ENTSCHIEDEN | — | confirmed |

**Joe muss noch aktiv:** N2 + N4 (Juni), N6-WSK-Seite prüfen,
"weitere Pilot-Kunden?" — plus 3 Juni-Aktionen aus §6 (PyPI-Account,
DSB, Pentest-Buchung). Alles andere ist entschieden oder vorbereitet.

---

## 3. Der kritische Pfad — was JETZT (nach Joe-Runde 1) dran ist

N1 ist entschieden → der Pfad ist frei bis PyPI:

```
N1 Lizenz ✅ ────► M2 PyPI-Publish ────► N5 WSK-Modell-2
AGPL-3.0+TM        (braucht nur noch     (importiert nomos-core
                    Joe's PyPI-Account)   als Library)
```

**Einzige verbleibende Joe-Aktion auf dem kritischen Pfad:**
einen PyPI-Account/Token bereitstellen (M2). Danach ist v0.6.0 +
WSK-Library-Integration ohne weitere Entscheidung ausführbar.

---

## 4. Die NEUEN Entscheidungen (nicht in MASTER-PLAN §7)

### N1 — Lizenz ✅ ENTSCHIEDEN: AGPL-3.0 + Trademark

**Joe 2026-05-21: AGPL-3.0 + Trademark.**

Das beantwortet direkt **Joe's Frage #16** (*"baut es mir wer nach
und macht Geld damit?"*): Ja, die Gefahr ist real — Microsoft + Asqav
nutzen MIT und sind genau deshalb schließbar. AGPL macht jeden Fork
offen-pflichtig (auch bei SaaS-Nutzung), Trademark schützt den Namen.
Das ist zugleich ein Differenzierungs-Punkt (competitive-landscape.md
§4) und Bell-Labs-Logik: Code ist frei, Marke ist unsere.

**Folge-Aktionen:** N2 (Anwalt-Timing), LICENSE-Datei + Header in
v0.5.0, PyPI-Publish unter AGPL (M2).

### N9 — Pricing ✅ ENTSCHIEDEN: individuell pro Kunde

**Joe 2026-05-21: kein Einheitsmodell — Hybrid + Flat + individuell.**

Es gibt **keinen festen Preis**. FCL bleibt (3 Agents gratis). Darüber
ist die Vereinbarung pro Kunde individuell — aus drei Bausteinen:
- **Beitrag + Erfolg (Hybrid)** — Sockel-Beitrag deckt Infra, plus
  Mehrwert-Komponente
- **Flat-Tarif** — für Kunden die Planbarkeit wollen
- **bespoke** — individuell verhandelt

Das alte €499-Flat (M17) ist damit *nicht tot* — es ist **eine
Option unter mehreren**, nicht DAS Modell. Konkrete Zahlen erst
**nach dem Pilot** — man teilt Mehrwert erst wenn er gemessen ist
(Joe-Korrektur #15). Der Konflikt mit der Empowerment-Stance ist
damit aufgelöst: der Kunde wählt was passt, inkl. niedrig-Beitrag.

### N5 — WSK-Integration: Modell 2+3 gestaffelt? 🟡

**Frage:** Wie konsumiert das WSK-Projekt NomOS? (Detail-Analyse:
`2026-05-21-nomos-wsk-integration.md`.)

**Empfehlung: gestaffeltes Modell 2+3** — Phase 1 (v0.5):
WSK-Hash-Chain formatkompatibel machen. Phase 2 (v0.6): `nomos-core`
als PyPI-Library, WSK importiert sie. Phase 3 (v0.7): WSK-Events
fliessen als Audit-Events in NomOS. Phase 4 (v0.8): WSK-KMU-Kunden
bekommen automatisch Annex-IV-PDFs.

Kein Big-Bang, keine WSK-Release-Blockade. Hängt an M2 (PyPI).
**Joe muss:** Modell 2+3 bestätigen — oder anderes Modell nennen.

### N6 — WSK-Pilot-0 = Pilot-Kandidat? 🟡 teil-offen

**Joe 2026-05-21:** noch nicht eindeutig — WSK-seitig zu prüfen.
Bekannt ist: der Pilot-Kandidat ist ein **Bestandskunde**, für den
AIE Webshop-Tools + Odoo gebaut hat und den Betrieb verwaltet. Ziel
ist, dass NomOS dessen Betrieb später auditiert/governt. Ob das
dieselbe Firma wie WSK-"Pilot-0" ist, muss Joe WSK-seitig abgleichen.

**Joe muss:** WSK-CHANGELOG-"Pilot-0" gegen den Bestandskunden
abgleichen — identisch oder zwei verschiedene.

### N3 — Pilot-Kunde-Namen in Docs ✅ ENTSCHIEDEN: anonym, strikt

**Joe 2026-05-21: anonym halten, in allen Docs.**

Der Pilot-Kunde wird in **keinem Dokument** namentlich genannt — aus
Diskretionsgründen gegenüber dem Kunden. In allen Strategy-Docs steht
**"Pilot-Kandidat"** bzw. **"Bestandskunde"**. Ebenfalls anonym: die
für ihn gebauten Beta-Tools.

**Regel für künftige Docs:** Kunden-Interna (insb. Compliance-Stand
eines Kunden) gehören **nie** in ein versioniertes Repo. Nur das
abstrakte Muster ("ein KMU mit Optimierungs-Bedarf") ist
dokumentierbar — nie firmen-zuordenbare Details. Diese Diskretion ist
nicht verhandelbar: eine Pilot-Beziehung darf der Firma nie schaden.

### N4 — Atlas customer-shippable oder internal-only? 🔴

**Frage:** Atlas (phantom-control) ist heute Joe's interne Konsole.
WSK-ADR-0031 will Atlas fürs Kunden-Onboarding nutzen. Soll Atlas
nach RCE-Fix + IP-Bereinigung auch an Kunden ausgeliefert werden?

**Empfehlung: internal-only für jetzt, customer-shippable als
v1.1+-Option.** Bis 2026-08-02 ist keine Zeit, Atlas customer-ready
zu härten (RCE-Fix + IP-Scrub + UI-Rework + eigener Pentest). NomOS
allein trägt die Deadline. **Joe muss:** bestätigen + sagen ob
customer-shipping je gewünscht ist.

### N7 — Quadrupel-Center in META-VISION übernehmen? 🟡

**Empfehlung: ja** — die Topologie ist Quadrupel-Center
(Zeroth + NomOS + Atlas + WSK). Sobald Joe bestätigt, aktualisiere
ich `2026-05-20-META-VISION.md` (reiner Doc-Task).

### N8 — Hermes als NomOS-Backend? 🟡

**Empfehlung: deferred lassen.** Kein Deadline-Bezug, kein
Customer-Pull. Re-evaluieren in v1.1+.

### N2 — Trademark-Anwalt — wann buchen? 🔴

**Frage:** N1 ist "AGPL + Trademark" — wann wird der Anwalt für die
Markenanmeldung ("NomOS", evtl. "A.T.L.A.S. CEO") beauftragt?

**Empfehlung: vor dem OSS-Release (v0.6 Zeitfenster).** Trademark
sollte angemeldet sein bevor der Code öffentlich ist — sonst kann
jemand den Namen vor uns registrieren. **Joe muss:** Anwalt-Kontakt +
Timing.

---

## 5. Konflikte — Auflösungs-Status

| Konflikt | Alt | Joe-Korrektur | Auflösung |
|---|---|---|---|
| **N9 / M17** | €499 Flat-Pricing | #10 #15 #17 | ✅ aufgelöst — N9: individuell pro Kunde, Flat nur eine Option |
| **M9** | "AWS-Funding first" | #1 — kein Founding-Focus | Reframe: Funding opportunistisch, kein Roadmap-Treiber, keine Phase hängt daran |
| **M10** | "Pre-Sale ab v0.8" | #10 — Networking statt Sales | Reframe: "Pre-Sale" → "Pilot-Gespräche / Networking" |

M9 + M10 sind reine Formulierungs-Reframes — fliessen in
MASTER-PLAN v2 ein, brauchen keine Joe-Aktion.

---

## 6. §7-Entscheidungen mit Claude-Empfehlung — Ratify-Liste

Volle Optionen + Begründung in `2026-05-20-MASTER-PLAN.md` §7.
Default: gelten als angenommen wenn Joe nicht widerspricht.

| ID | Kurz | Empfehlung |
|---|---|---|
| M1 | Atlas als Pilot-#0 | ja — Dogfood |
| M2 | PyPI-Publish | ja — *kritischer Pfad, braucht Joe's PyPI-Account* |
| M5 | NemoClaw-Activation | nein — defer auf v1.1+ |
| M7 | Sigstore Rekor | opt-in, off by default |
| M13 | Hardware-SKU | x86-Baseline + Intel-NUC-Edge-SKU |
| M15 | DPIA | externer DSB (~€500-1500) — *Joe kontaktiert* |
| M16 | Pentest | DE-Mittelständler-Firma, €5-15k — *Joe bucht im Juni* |
| M19 | Asqav | eigene Chain behalten + Interop dokumentieren |

🟢 **Rein technisch — Claude entscheidet ohne Joe** (Transparenz):
M3 (DB-Isolation: RLS für v1.0), M4 (OpenAPI-codegen: ja),
M6 (Vault-TLS: opt-in env), M8 (Migration: CLI + Guide),
M12 (/full-sync: bei v0.5.0-Tag), M14 (Atlas-P4 ‖ v0.7: parallel).

**Joe-Aktionen hier:** 3 — PyPI-Account bereitstellen (M2), DSB
kontaktieren (M15), Pentest-Firma buchen (M16). Alles im Juni.

---

## 7. Bereits entschieden — Record

| ID | Entscheidung |
|---|---|
| N1 | Lizenz = AGPL-3.0 + Trademark (Joe 2026-05-21) |
| N3 | Pilot-Kunde in allen Docs anonym (Joe 2026-05-21) |
| N9 | Pricing individuell pro Kunde, Zahlen nach Pilot (Joe 2026-05-21) |
| M11 | Pilot-Customer #1 = der Pilot-Kandidat (Joe-Bestandskunde) |
| M18 | Lineage Engine bleibt deferred — NomOS hat es absorbiert |
| DEC-001 | Zeroth Core = Veto-Layer, nicht Hub |
| DEC-002 | Engineering-Spec strikt getrennt von Vision-Material |
| DEC-003 | TT-SI als kanonischer M08-Algorithmus (conditional) |
| DEC-004 | Memetik nur in research-directions |
| DEC-005 | Action-Plan v2.0 — 4-Lane 60/20/5/15 |
| — | Audit-Trail v2 (Ed25519 + RFC-6962 Merkle) — shipped v0.4.0 |
| — | OpenClaw gepinnt auf 2026.5.18 |

---

## 8. Das Goal — jetzt fast vollständig scharf

Das Goal selbst stand immer klar in MASTER-PLAN §1 (bis 2026-08-02
kann ein DACH-KMU `docker compose up`, Agent hiren, Annex-IV-PDF,
Regulator-Verifikation mit Public-Key). Offen waren die Gabelungen.
**Nach Joe-Runde 1 ist das Goal:**

> **NomOS wird als AGPL-3.0-Open-Source-Projekt mit Trademark-Schutz
> veröffentlicht (✅ N1), als `nomos-core` auf PyPI publiziert (M2),
> und bildet mit WSK über ein gestaffeltes Library+Audit-Sink-Modell
> (N5) ein Compliance-Backbone das WSK's Kunden (AIE/ZW/KMU)
> automatisch Annex-IV-konform macht. Der erste reale Beweis ist ein
> Bestandskunde (Pilot-Kandidat, anonym — ✅ N3). Geld ist individuell
> pro Kunde (✅ N9) — Beitrag/Erfolg/Flat als Bausteine, FCL bleibt
> gratis, Zahlen erst nach Pilot. Funding ist Lottogewinn (M9), nicht
> Plan. Atlas bleibt vorerst Joe's internes Cockpit (N4, Empfehlung).
> Die Bewegung heißt Empowerment, nicht Verkauf.**

**Verbleibende Gabelungen:** nur noch N2 (Anwalt-Timing), N4
(Atlas-Shipping ja/nein) und N6-WSK-Abgleich. Keine davon blockiert
v0.5.0/v0.6.0. Sobald sie beantwortet sind, schreibe ich
**MASTER-PLAN v2** — fork-frei.

---

## 9. Nächster konkreter Schritt

1. **Joe:** PyPI-Account/Token bereitstellen (M2 — einzige
   kritisch-Pfad-Aktion). N2/N4/N6 können bis Juni warten.
2. **Claude parallel (blockiert nicht):** v0.5.0 W-Phase-Code —
   CI-Sichtung, 5 Sicherheitslücken, Live-Eval. Hash-Chain-Format
   einfrieren (WSK-Task #1). LICENSE-Datei (AGPL-3.0) + File-Header
   anlegen (N1-Folge).
3. **Nach Joe's restlichen Antworten:** MASTER-PLAN v2 +
   META-VISION-Update (N7).

---

## 10. Begleitdokumente

- `2026-05-20-MASTER-PLAN.md` §7 — volle Optionen der M-Entscheidungen
- `2026-05-20-META-VISION.md` §12 — die 6 Vision-Fragen (hier überführt)
- `2026-05-21-nomos-wsk-integration.md` §9 — WSK-Fragen-Detail
- `2026-05-21-competitive-landscape.md` — warum AGPL (N1) strukturell zählt
- `2026-05-20-v0.5.0-roadmap.md` — die 5 Roadmap-pending-Items
