# NomOS — Decision Log: alle offenen Fragen an einem Ort

> **Zweck:** Joe's Constraint #1 ist *Übersicht*. Dieses Dokument ist
> die EINE Stelle an der jede offene Entscheidung steht — konsolidiert
> aus 4 Strategy-Docs (MASTER-PLAN §7, META-VISION §12,
> WSK-Integration §9, v0.5.0-Roadmap). Wenn die hier markierten
> Entscheidungen getroffen sind, hat der Pfad zum Goal **keine
> Gabelungen mehr** — Ausführung wird mechanisch.
>
> **Stand:** 2026-05-21. Kanonischer Decision-Register —
> ersetzt die verstreute Frage-Haltung in §7/§12/§9.

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
| **N1** | Lizenz final: AGPL-3.0 + Trademark? | 🔴 OFFEN | PyPI-Publish, Open-Source-Release | **diese Woche** |
| **N9** | Pricing-Philosophie: Beitrag/Erfolg/Hybrid? | ⚠️ KONFLIKT | v0.8 Pre-Sale, ersetzt M17 | **diese Woche** |
| **M2** | `nomos-core` PyPI-Publish? | 🟡 EMPFOHLEN | v0.6.0, WSK-Modell-2 | **diese Woche** |
| **N5** | WSK-Integration: Modell 2+3 gestaffelt? | 🟡 EMPFOHLEN | Hash-Chain-Format-Contract | **diese Woche** |
| **N6** | WSK-Pilot-0 = RUF-Pilot (identisch)? | 🔴 OFFEN | Pilot-Planung-Klarheit | diese Woche |
| **N3** | RUF + taktical-apps Namen in Docs nennen? | 🔴 OFFEN | Doc-Präzision | diese Woche |
| **N4** | Atlas customer-shippable oder internal-only? | 🔴 OFFEN | v0.7 Scope, WSK-Onboarding | Juni |
| **M9** | Funding: AWS-first / EU-parallel? | ⚠️ KONFLIKT | nichts (Lottogewinn-Reframe) | Q3 |
| **M10** | Wann Customer-Acquisition beginnt? | ⚠️ KONFLIKT | Pre-Sale-Framing | jetzt |
| **N7** | Quadrupel-Center in META-VISION übernehmen? | 🟡 EMPFOHLEN | META-VISION-Update | Juni |
| **N8** | Hermes als NomOS-Backend? | 🟡 EMPFOHLEN | nichts (defer) | — |
| **N2** | Trademark-Anwalt — wann buchen? | 🔴 OFFEN | hängt an N1 | nach N1 |
| **M1** | Atlas als NomOS-Pilot-Customer #0? | 🟡 EMPFOHLEN | v0.7 Dogfood-Demo | Juni |
| **M19** | Asqav adoptieren oder eigene Chain? | 🟡 EMPFOHLEN | nichts (Chain bleibt) | v0.5.0 |
| **M13** | Customer-Hardware-SKU? | 🟡 EMPFOHLEN | v1.0-Marketing | v1.0.0 |
| **M15** | DPIA — wer macht das (externer DSB)? | 🟡 EMPFOHLEN | v0.9.0 | Juni-Kontakt |
| **M16** | Pentest — Firma, Budget, Timing? | 🟡 EMPFOHLEN | v1.0.0 | Juni-Buchung |
| **M7** | Sigstore Rekor public anchoring? | 🟡 EMPFOHLEN | v1.1+ | v1.1+ |
| **M5** | NemoClaw-Activation als Backend? | 🟡 EMPFOHLEN | nichts (defer) | v1.1+ |
| **M3** | Multi-Tenant DB-Isolation-Strategie? | 🟢 CLAUDE | v0.9.0 | v0.9.0 |
| **M4** | OpenAPI-driven Plugin-Contract? | 🟢 CLAUDE | v0.7.0 | v0.7.0 |
| **M6** | Vault-TLS-Migration-Strategie? | 🟢 CLAUDE | v0.6.0 | v0.6.0 |
| **M8** | Customer-Migration-Path v0.2→v1.0? | 🟢 CLAUDE | v1.0.0 | v1.0.0 |
| **M12** | `/full-sync` heute oder bei v0.5.0-Tag? | 🟢 CLAUDE | nichts | v0.5.0-Tag |
| **M14** | Atlas-Phase-4 vs v0.7 — parallel? | 🟢 CLAUDE | nichts | jetzt |
| **M11** | Wer ist Pilot-Customer #1? | ✅ ENTSCHIEDEN | — | RUF (Joe) |
| **M17** | Pricing — €499 Flat? | ⚠️ → N9 | — | ersetzt durch N9 |
| **M18** | Lineage Engine — deferred? | ✅ ENTSCHIEDEN | — | confirmed |

**Joe muss aktiv durchgehen: 8 Stück** — die 🔴 (N1, N6, N3, N4, N2)
und die ⚠️ (N9, M9, M10). Alles andere ist vorbereitet.

---

## 3. Der kritische Pfad — was JETZT entschieden werden muss

Diese 6 blockieren die nächsten 2-3 Wochen. Alles andere kann bis zu
seiner Phase warten.

```
N1 Lizenz ──────────► M2 PyPI-Publish ──────────► N5 WSK-Modell-2
(AGPL final)          (braucht Lizenz +            (importiert nomos-core
                       Joe's PyPI-Account)          als Library)

N9 Pricing-Philosophie ──► v0.8 Pre-Sale-Framing
(Beitrag statt €499)

N6 WSK-Pilot-0=RUF? ──┐
N3 RUF-Namen in Docs? ─┴──► Pilot- + Doc-Präzision (klein, aber blockt Klarheit)
```

**Reihenfolge der Dependency:** N1 zuerst (man publiziert unter einer
Lizenz) → dann M2 → dann N5. N9 ist unabhängig, aber genauso dringend
weil es das ganze Geschäfts-Framing bestimmt.

---

## 4. Die NEUEN Entscheidungen (nicht in MASTER-PLAN §7)

### N1 — Lizenz final: AGPL-3.0 + Trademark? 🔴

**Frage:** Unter welcher Lizenz geht NomOS Open Source — und schützen
wir den Namen per Trademark?

Das beantwortet direkt **Joe's Frage #16** aus den Korrekturen:
*"besteht die Gefahr dass es mir einfach wer nachbaut und Geld damit
macht?"* — **Ja, diese Gefahr ist real** (Microsoft + Asqav nutzen MIT,
genau deshalb sind sie schließbar). Die Lizenz IST die Antwort.

| Option | Effekt |
|---|---|
| **A: AGPL-3.0 + Trademark** | Jeder Fork muss offen bleiben (auch SaaS-Nutzung). Name geschützt → niemand verkauft "NomOS" als Closed-Produkt. Empfohlen. |
| B: Apache-2.0 / MIT | Maximale Adoption — aber jeder kann es schließen und kommerziell weiterverkaufen. Genau Joe's befürchtetes Szenario. |
| C: AGPL ohne Trademark | Code geschützt, Name nicht — Nachbau unter gleichem Namen möglich |

**Empfehlung: A.** AGPL ist exakt der strukturelle Schutz gegen
"jemand baut es nach und verdient daran". Es ist auch ein
Differenzierungs-Punkt gegenüber Microsoft/Asqav (siehe
competitive-landscape.md §4). Trademark trennt "Code ist frei" von
"Marke ist unsere" — Bell-Labs-Logik.

**Joe muss:** A/B/C bestätigen. Blockt M2 (PyPI-Publish).

---

### N9 — Pricing-Philosophie ⚠️ (ersetzt M17)

**Konflikt:** MASTER-PLAN §7 #17 empfahl **€499/Monat Flat**. Das
widerspricht **drei Joe-Korrekturen**:
- #10 *"nicht so stark sales-getrieben"*
- #17 *"Empowerment des Mittelstands, Focus nicht Geld verrechnen"*
- #15 *"kann erst nach Wertschöpfung entschieden werden — Beteiligung
  an Mehrwert"*

Ein fixer SaaS-Preis ist das Gegenteil von Empowerment-Bewegung.

| Option | Effekt |
|---|---|
| A: €499 Flat (alt) | Klassisches SaaS — widerspricht der Bewegung. **Verworfen.** |
| **B: Beitrags-Modell** | FCL (3 Agents gratis) bleibt. Ab 4 Agents: Mitglieds-Beitrag nach Firmen-Größe gestaffelt, kein fixer Marktpreis |
| C: Erfolgs-Beteiligung | Anteil am messbaren Mehrwert (WSK liefert die Wirkungsmessung). Joe's #15-Idee. Komplex, aber philosophie-konform |
| D: Hybrid B+C | Kleiner Sockel-Beitrag (Infra-Deckung) + optionale Erfolgs-Komponente |

**Empfehlung: D (Hybrid).** Ein kleiner Beitrag deckt reale
Infra-Kosten (kein Verlustgeschäft), die Erfolgs-Komponente macht es
zur Beteiligung statt Verkauf. Konkrete Zahlen erst **nach** dem
RUF-Pilot — weil man Mehrwert erst messen muss bevor man ihn teilt
(genau Joe's #15). Bis dahin: NomOS bleibt schlicht gratis/FCL.

**Joe muss:** Richtung B/C/D bestätigen. M17 wird damit ungültig.

---

### N5 — WSK-Integration: Modell 2+3 gestaffelt? 🟡

**Frage:** Wie konsumiert das WSK-Projekt NomOS? (Detail-Analyse:
`2026-05-21-nomos-wsk-integration.md`.)

**Empfehlung: gestaffeltes Modell 2+3** — Phase 1 (v0.5): WSK-Hash-Chain
formatkompatibel machen. Phase 2 (v0.6): `nomos-core` als PyPI-Library,
WSK importiert sie. Phase 3 (v0.7): WSK-Events fliessen als
Audit-Events in NomOS (wie die Atlas-Bridge). Phase 4 (v0.8):
WSK-KMU-Kunden bekommen automatisch Annex-IV-PDFs.

Kein Big-Bang, keine WSK-Release-Blockade. Hängt an M2 (PyPI).

**Joe muss:** Modell 2+3 bestätigen — oder anderes Modell nennen.

---

### N6 — WSK-Pilot-0 = RUF-Pilot? 🔴

**Frage (rein faktisch — nur Joe weiß es):** Das WSK-CHANGELOG nennt
einen "Pilot-0" (Betriebs-Profile, HilfeCounter, Danke-Wall). Joe
nannte separat RUF als Pilot-Firma mit "taktical apps" in Beta. **Sind
das derselbe Pilot oder zwei verschiedene?**

Die Antwort bestimmt, ob die Pilot-Planung für NomOS, WSK und Atlas
auf *eine* reale Firma konvergiert oder auf zwei verteilt ist.

**Joe muss:** "identisch" oder "zwei verschiedene" + kurz was RUF ist.

---

### N3 — RUF + taktical-apps Namen in Docs nennen? 🔴

**Frage:** Dürfen die echten Namen (RUF, taktical-apps) in den
Strategy-Docs stehen, oder bleibt das anonym ("AT-KMU aus
Joe-Netzwerk")?

Joe's Pseudonymitäts-Constraint gilt für *Joe als Person* — nicht
unbedingt für Pilot-Kunden. Aber das ist Joe's Call.

**Empfehlung:** anonym halten bis der Pilot-Kunde selbst zustimmt
genannt zu werden. Interne Docs könnten den Namen führen, öffentliche
nicht. **Joe muss:** anonym / intern-ok / öffentlich-ok.

---

### N4 — Atlas customer-shippable oder internal-only? 🔴

**Frage:** Atlas (phantom-control) ist heute Joe's interne Konsole.
WSK-ADR-0031 will Atlas fürs Kunden-Onboarding nutzen. **Soll Atlas
nach RCE-Fix + IP-Bereinigung auch an Kunden ausgeliefert werden?**

| Option | Effekt |
|---|---|
| A: internal-only | Atlas bleibt Joe's Cockpit. Nur NomOS geht raus. Klare Trennung, weniger Härtungs-Aufwand. |
| B: customer-shippable | Atlas wird Teil des Produkts. Verstärkt das Quadrupel-Angebot, aber: RCE-Fix + voller IP-Scrub + UI-Rework + eigener Pentest nötig |

**Empfehlung: A für jetzt, B als v1.1+-Option.** Bis 2026-08-02 ist
keine Zeit Atlas customer-ready zu härten. NomOS allein muss die
Deadline tragen. Atlas-Shipping ist ein post-Deadline-Thema.

**Joe muss:** A/B + ob B überhaupt je gewünscht ist.

---

### N7 — Quadrupel-Center in META-VISION übernehmen? 🟡

**Frage:** Die WSK-Integration zeigte: die Topologie ist nicht
Tri-Center (Zeroth+NomOS+Atlas) sondern **Quadrupel-Center**
(+ WSK als Wertschöpfungs-Säule).

**Empfehlung: ja.** Sobald Joe bestätigt, aktualisiere ich
`2026-05-20-META-VISION.md` (reiner Doc-Task, kein Code).

---

### N8 — Hermes als NomOS-Backend? 🟡

**Frage (aus v0.5.0-Roadmap):** Top-Level-CLAUDE.md sagt "out of
scope", aber die Phantom-Neural-Cortex-Roadmap könnte das ändern.

**Empfehlung: deferred lassen.** Kein Bezug zur 2026-08-02-Deadline,
kein Customer-Pull. Re-evaluieren in v1.1+. **Joe muss:** nur
bestätigen dass das ok ist.

---

## 5. Konflikte — wo eine alte Empfehlung deinen Korrekturen widerspricht

Drei Stellen wo der MASTER-PLAN noch das alte "Founder/Sales"-Framing
trägt und reframed werden muss:

| Konflikt | Alt (MASTER-PLAN) | Joe-Korrektur | Auflösung |
|---|---|---|---|
| **N9 / M17** | €499/Monat Flat-Pricing | #10 #15 #17 — Empowerment, kein Geld-Focus | → N9: Beitrags-/Erfolgs-Hybrid, Zahlen erst nach Pilot |
| **M9** | "AWS-Funding first, Q3" | #1 — kein Founding-Focus, Lottogewinn nicht Muss | Funding bleibt im Plan, aber als *opportunistisch* — kein Roadmap-Treiber, keine Phase hängt daran |
| **M10** | "Pre-Sale ab v0.8 mit Annex-IV-Demo" | #10 — Networking statt Sales | "Pre-Sale" → *"Pilot-Gespräche / Networking"*. Kein Verkaufs-Funnel, sondern: mit RUF + Netzwerk teilen, Feedback holen |

Diese drei sind **keine neuen Entscheidungen** — sie sind
Formulierungs-Korrekturen die in MASTER-PLAN v2 einfliessen. Joe muss
nur N9 aktiv entscheiden; M9 + M10 sind reine Reframes.

---

## 6. §7-Entscheidungen mit Claude-Empfehlung — Ratify-Liste

Diese 12 haben eine klare Empfehlung im MASTER-PLAN §7. Default: sie
gelten als angenommen, wenn Joe nicht widerspricht. Volle Optionen +
Begründung stehen in `2026-05-20-MASTER-PLAN.md` §7.

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

**Joe-Aktionen hier:** nur 3 — PyPI-Account bereitstellen (M2), DSB
kontaktieren (M15), Pentest-Firma buchen (M16). Alles im Juni.

---

## 7. Bereits entschieden — Record

| ID | Entscheidung |
|---|---|
| M11 | Pilot-Customer #1 = RUF (Joe-Korrektur #11) |
| M18 | Lineage Engine bleibt deferred — NomOS hat es absorbiert |
| DEC-001 | Zeroth Core = Veto-Layer, nicht Hub |
| DEC-002 | Engineering-Spec strikt getrennt von Vision-Material |
| DEC-003 | TT-SI als kanonischer M08-Algorithmus (conditional) |
| DEC-004 | Memetik nur in research-directions |
| DEC-005 | Action-Plan v2.0 — 4-Lane 60/20/5/15 |
| — | Audit-Trail v2 (Ed25519 + RFC-6962 Merkle) — shipped v0.4.0 |
| — | OpenClaw gepinnt auf 2026.5.18 |

---

## 8. Das Goal — wenn alles beantwortet ist

Das Goal selbst ist **nicht offen** — es steht klar in MASTER-PLAN §1:

> Bis 2026-08-02 kann ein DACH-KMU `docker compose up -d` fahren,
> einen AI-Agent hiren, ein Annex-IV-PDF bekommen, und im Audit-Fall
> einem Regulator nur einen Public-Key + 3 URLs übergeben.

Was *offen* war, sind die **8 Gabelungen** auf dem Weg dorthin
(die 🔴 + ⚠️ aus §2). Sind die entschieden, ist das vollständige Goal:

> **NomOS wird als AGPL-3.0-Open-Source-Projekt veröffentlicht
> (N1), als `nomos-core` auf PyPI publiziert (M2), und bildet mit
> WSK über ein gestaffeltes Library+Audit-Sink-Modell (N5) ein
> Compliance-Backbone das WSK's Kunden (AIE/ZW/KMU) automatisch
> Annex-IV-konform macht. Der RUF-Pilot (M11/N6) ist der erste
> reale Beweis. Geld ist ein Beitrags-/Erfolgs-Hybrid (N9), kein
> SaaS-Preis. Funding ist Lottogewinn (M9), nicht Plan. Atlas
> bleibt vorerst Joe's internes Cockpit (N4). Die Bewegung heißt
> Empowerment, nicht Verkauf.**

Sobald N1, N3, N4, N6, N9 entschieden sind (5 echte Joe-Calls — der
Rest ist Ratify oder Reframe), schreibe ich **MASTER-PLAN v2**, der
alle 28 Entscheidungen eingebaut hat und keine Frage mehr offen lässt.

---

## 9. Nächster konkreter Schritt

1. **Joe:** die 5 🔴 entscheiden (N1, N3, N4, N6, N9) + N9-Richtung wählen.
2. **Claude parallel (blockiert nicht):** v0.5.0 W-Phase-Code starten —
   CI-Sichtung, 5 Sicherheitslücken, Live-Eval. Hash-Chain-Format
   einfrieren (WSK-Task #1, braucht keine Joe-Entscheidung).
3. **Nach Joe's Antworten:** MASTER-PLAN v2 + META-VISION-Update (N7).

---

## 10. Begleitdokumente

- `2026-05-20-MASTER-PLAN.md` §7 — volle Optionen der M-Entscheidungen
- `2026-05-20-META-VISION.md` §12 — die 6 Vision-Fragen (Teilmenge hier)
- `2026-05-21-nomos-wsk-integration.md` §9 — WSK-Fragen-Detail
- `2026-05-21-competitive-landscape.md` — warum AGPL (N1) strukturell zählt
- `2026-05-20-v0.5.0-roadmap.md` — die 5 Roadmap-pending-Items
