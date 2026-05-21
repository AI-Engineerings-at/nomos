# NomOS ↔ Wertschöpfungskette (WSK) — Integration-Klärung

> Die Zusammenarbeit zwischen NomOS und dem WSK-Projekt
> (`~/wertschoepfungskette/`) ist WSK-seitig in zwei ADRs angelegt,
> aber nomos-seitig nie beantwortet. Dieses Dokument klärt sie.
>
> Begleitdokument zu `2026-05-20-nomos-atlas-integration.md` und
> `2026-05-20-META-VISION.md`.
>
> **Stand:** 2026-05-21. Quelle: 4 WSK-Files (CHANGELOG, ARCHITECTURE,
> CLAUDE, README) von Joe übergeben.

---

## 1. Was WSK ist

**Wertschöpfungskette** = Enterprise Automation Pipeline. Eigenes
Repo (`~/wertschoepfungskette/`), eigene 57 ADRs, eigene KB-Struktur.
Owner @joe — gleicher Owner wie nomos, aber **eigenständiges Projekt.**

**Ein System, drei Anwendungen, neun Blöcke:**

```
CONTENT ENGINE  →  DISTRIBUTION   →  LEAD CAPTURE
     ↓                  ↓                  ↓
LEAD NURTURING  →  SALES AUTOMATION → DELIVERY
     ↓                  ↓                  ↓
SUPPORT/UPSELL  →  FEEDBACK LOOP   →  CONTINUOUS IMPROVEMENT
```

Drei Anwendungen aus einem System:
- **AIE** (AI Engineering selbst)
- **ZugangsWeg** (Lena's Inklusions-Brand)
- **KMU-White-Label** (für Kunden)

**Tech-Stack:** n8n self-hosted (Docker Swarm .82), ERPNext + Frappe
LMS, Mattermost (HITL), Listmonk, Qdrant + bge-m3 (RAG), Ollama-lokal
+ Claude/Codex via OAuth. Eigene Audit-Hash-Chain. OpenBadges 3.0
Cert-Service.

**Status:** Phase A-D durchlaufen, **Pilot-0 heute (2026-05-21)
implementiert** — Lint-Gates, Counter-Stack, 62 pytest-Tests,
Vier-Säulen-Wirkungs-Report, Goodhart-Schutz.

---

## 2. Die zwei bestehenden Verbindungs-ADRs

WSK hat die Zusammenarbeit **WSK-seitig bereits in zwei
Architektur-Entscheidungen festgeschrieben** (aus dem WSK-CHANGELOG,
Phase B4):

| ADR | Titel | Bedeutung für nomos |
|---|---|---|
| **ADR-0030** | `nomos-audit-chain-Library` | WSK will nomos's Hash-Chain-Code als **Library** konsumieren |
| **ADR-0031** | `phantom-control-Onboarding` | WSK will Atlas (phantom-control) für **Onboarding** nutzen |

Plus aus dem WSK-CHANGELOG, Sektion "Fixed":
> "nomos '48 Commits unpushed' Risiko aufgelöst (PR #5 gemerged
> 2026-05-20 via D4)"

→ WSK's Recherche-Subagenten haben sogar **nomos's Repo-Hygiene
mitbeobachtet**. WSK ist sich nomos sehr bewusst.

**ABER:** Beide ADRs sind WSK-seitige Absichten. Es gibt
nomos-seitig **keine Antwort, keinen Contract, keine "wie WSK uns
konsumiert"-Spec.** Genau das ist die ungeklärte Lücke die Joe meint.

---

## 3. Die Richtungs-Frage — Code-Dependency vs Daten-Quelle

Hier ist eine wichtige Doppeldeutigkeit aufzulösen:

- **ADR-0030 sagt:** WSK konsumiert nomos (nomos-Code → WSK).
  Richtung: nomos ist **Upstream-Library**.
- **Joe sagt heute:** "WSK ist ein Datenpunkt/Datenquelle für nomos"
  (WSK-Daten → nomos). Richtung: WSK ist **Daten-Quelle**.

**Beide stimmen — es sind zwei verschiedene Kopplungen:**

```
   Code-Ebene (ADR-0030):
   ─────────────────────
   nomos.core.hash_chain  ──Library──►  WSK counter.py
   (eine Hash-Chain-Implementation, geteilt)

   Daten-Ebene (Joe's "Datenquelle"):
   ──────────────────────────────────
   WSK Workflow-Runs / HITL-Events  ──Audit-Sink──►  nomos Audit-Trail
   (WSK-Compliance-Events landen in nomos)
```

Das ist **strukturell identisch zur Atlas-Bridge** (siehe
`2026-05-20-nomos-atlas-integration.md`): Atlas ist ein
nomos-Consumer auf Code- UND Daten-Ebene. WSK genauso.

---

## 4. WSK in der Meta-Vision-Topologie

In `META-VISION.md` hatte ich die Topologie als Tri-Center
(Zeroth + NomOS + Atlas) + 3 Peripherie-Schalen.

**WSK passt NICHT in eine Peripherie-Schale.** Dafür ist es zu
substantiell (57 ADRs, eigenes Multi-Tenant-System, Enterprise-Grade,
3 produktive Anwendungen). WSK ist eine **eigene Säule**.

Die korrigierte Topologie:

```
                  ZEROTH (Verfassung — governs all)
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    ATLAS             NOMOS               WSK
   (Operator)        (Compliance)      (Wertschöpfung)
   ──────────        ───────────       ──────────────
   "wer steuert"     "ist es legal"    "was wird erzeugt"
   Electron HQ       Docker Engine     n8n Pipeline
   Joe-intern        Customer-Produkt  AIE+ZW+KMU
       │                 │                 │
       └────────►  Contract A/B  ◄──────────┘
                  (audit-sink +
                   verdict-check)
```

**Die drei Verben:**
- **Atlas** beantwortet *"wer steuert die Agenten?"*
- **NomOS** beantwortet *"ist diese Agent-Action legal/auditierbar?"*
- **WSK** beantwortet *"was erzeugt der Agent — Content, Leads, Umsatz?"*

NomOS sitzt in der Mitte. Atlas und WSK sind beide nomos-Consumer.
**WSK ist sogar der wichtigere Consumer** — denn WSK ist
customer-facing (AIE+ZW+KMU-White-Label), Atlas ist nur Joe-intern.

**Implikation für die META-VISION:** das Tri-Center wird zum
**Quadrupel-Center: Zeroth + NomOS + Atlas + WSK.** Die META-VISION
sollte entsprechend ergänzt werden.

---

## 5. Warum WSK strategisch der wichtigste Daten-Lieferant ist

WSK's neun Blöcke produzieren genau die Event-Arten die nomos's
Audit-Trail + Annex-IV-Generator braucht:

| WSK-Block | Event-Typ | nomos-Relevanz |
|---|---|---|
| Content Engine | Content-Veröffentlichung (HITL) | Art. 50 Transparenz — KI-generierter Content muss markiert sein |
| Lead Capture | PII-Erfassung (Double-Opt-In) | DSGVO Art. 6 + 30 — Verarbeitungsverzeichnis |
| Sales Automation | Hot-Lead-Kontakt (HITL) | Art. 14 menschliche Aufsicht |
| Delivery | Zertifikat-Hash | Art. 12 Record-Keeping |
| Feedback Loop | Wirkungs-Report | Annex IV §2(d) — Eval-Daten |
| Continuous Improvement | Agent-Selbst-Anpassung | Art. 12 substantielle Modifikation |

WSK's eigene Architektur (ARCHITECTURE.md §7) sagt schon:
> "Append-only Event-Log je Workflow-Run, hash-verkettet (ähnlich
> Cert-Hash-Chain)"

Das ist **dasselbe Pattern wie nomos's Hash-Chain.** WSK hat es
parallel erfunden. ADR-0030 erkennt: statt zwei Implementationen →
eine geteilte nomos-Library.

---

## 6. Drei Integrations-Modelle

### Modell 1 — Pattern-Referenz (loseste Kopplung)

WSK behält seine eigene Hash-Chain (`counter.py`). nomos ist nur
Vorbild. ADR-0030 wird "informational" statt "binding".

- **Pro:** keine Kopplung, WSK released unabhängig, kein PyPI nötig
- **Contra:** zwei Hash-Chain-Implementationen, zwei Audit-Formate,
  zweimal Pflege, Drift-Risiko (LEARNINGS L042-Klasse)

### Modell 2 — nomos als Code-Library (ADR-0030 binding)

nomos wird als `nomos-core` auf PyPI publiziert. WSK importiert
`nomos.core.hash_chain` + `nomos.core.merkle`. WSK's `counter.py`
nutzt die nomos-Implementation.

- **Pro:** EINE Hash-Chain-Implementation für nomos + Atlas + WSK.
  Eine Wahrheit. Audit-Format überall identisch.
- **Contra:** nomos.core muss API-stabil sein; WSK hängt an
  nomos-Releases; **PyPI-Publish nötig** (= Master-Plan §7 Frage #2,
  Empfehlung war ohnehin "JA")

### Modell 3 — WSK als nomos-Compliance-Tenant (Daten-Integration)

WSK's Workflow-Runs + HITL-Events fliessen als Audit-Events in eine
nomos-Instanz. WSK wird ein nomos-Tenant. Genau wie die Atlas-Bridge
Contract A.

- **Pro:** nomos validiert WSK live → echte Compliance-Story für
  AIE+ZW+KMU. Self-Application-Dogfood. Annex-IV-PDF für WSK-Kunden
  fällt automatisch ab.
- **Contra:** WSK muss eine nomos-Instanz betreiben; Betriebskomplexität;
  WSK-n8n-Workflows brauchen einen `nomos-audit-sink`-Node

### Empfehlung: Modell 2 + 3 kombiniert (gestaffelt)

```
Phase 1 (v0.5.x)  — Modell 1 bleibt aktiv (WSK eigenes counter.py),
                    ABER WSK's Hash-Chain-Format wird API-kompatibel
                    zu nomos gemacht (gleiche Feld-Namen, gleiche
                    canonical-JSON-Regeln). Migration wird trivial.

Phase 2 (v0.6.0)  — nomos PyPI-Publish (Master-Plan #2). WSK's
                    counter.py importiert nomos.core.hash_chain.
                    ADR-0030 wird binding. → Modell 2 live.

Phase 3 (v0.7.0)  — gemeinsam mit der Atlas-Bridge: WSK bekommt
                    denselben Audit-Sink-Contract. WSK-Events → nomos
                    Audit-Trail. → Modell 3 live.

Phase 4 (v0.8.0)  — WSK-Kunden (KMU-White-Label) bekommen über nomos
                    automatisch Annex-IV-PDFs. WSK + nomos sind ein
                    Compliance-Produkt aus Kundensicht.
```

So wird WSK schrittweise von "kennt nomos" zu "läuft auf nomos" —
ohne Big-Bang, ohne WSK-Release-Blockade.

---

## 7. Verbindung zur externen Analyse — "Regionaler Wirkungsflow"

In der letzten Session habe ich Joe gefragt was "Regionaler
Wirkungsflow" ist. **Die WSK-Files beantworten das:**

WSK-CHANGELOG "Welle 6 — Regionaler Wirkungsflow + Goodhart-Schutz"
(2026-05-20):
- **ADR-0055 Goodhart-Schutz-Doktrin** — Vier-Säulen-Wirkungsprofil
  (Counter + Resonanz-Stimme + Stichproben-Audit + Kontrafaktisch-Frage),
  6 Wirkungs-Dimensionen **ohne Score-Aggregation**
- **ADR-0056 Plattform-Kooperativen-Anker** — CoopCycle, Fairbnb.coop,
  AMIBA Local Multiplier, CLES Preston als Theorie-Referenz
- **ADR-0057 LEADER/CLLD-Reserve** — EU-regionale Entwicklungs-Förderung

Das ist die **konkrete Umsetzung dessen, was die externe Analyse
"lokale Kontextkenntnis als neuer Knappheitsfaktor" nannte.** WSK
misst Wirkung bewusst NICHT als aggregierten Score (Anti-Goodhart) —
weil sobald eine Metrik zum Ziel wird, taugt sie nicht mehr als
Metrik.

**Die Arbeitsteilung wird damit glasklar:**

- Die **externe Analyse** sagte: der Knappheitsfaktor ist *Vertrauen,
  Governance, lokale Kontextkenntnis*.
- **NomOS** liefert *Vertrauen + Governance* — kryptographisch
  portabel, verifizierbar ohne zentrale Autorität.
- **WSK** liefert *lokale Kontextkenntnis* — Regionaler Wirkungsflow,
  Goodhart-geschützte Wirkungsmessung, Plattform-Kooperativen-Logik.
- **Atlas** ist das Cockpit das beides für Joe bedienbar macht.

NomOS und WSK sind **nicht Konkurrenten um dieselbe Rolle — sie sind
die zwei Hälften der Antwort.** NomOS = "ist es vertrauenswürdig und
legal", WSK = "schafft es echten lokalen Mehrwert".

---

## 8. Was nomos-seitig konkret zu tun ist

Damit die WSK-Integration aus nomos-Sicht real wird:

| # | Task | nomos-Version | Hängt an |
|---|---|---|---|
| 1 | **Hash-Chain-Format einfrieren + dokumentieren** als stabiler Contract (`docs/contracts/hash-chain-format.md`) | v0.5.0 | — |
| 2 | **`nomos-core` PyPI-Publish** (Master-Plan #2) | v0.6.0 | Wheel-Build ready |
| 3 | **`POST /api/audit/entries` Batch-Endpoint** (gemeinsam mit Atlas-Bridge) | v0.7.0 | Atlas-Bridge-Arbeit |
| 4 | **WSK-Tenant-Onboarding-Doku** — wie ein n8n-Workflow den nomos-audit-sink anspricht | v0.7.0 | #3 |
| 5 | **Annex-IV-Generator akzeptiert WSK-Event-Quellen** | v0.8.0 | Annex-IV-Auto-Gen |

WSK-seitig (für Joe / WSK-Session, nicht nomos):
- ADR-0030 von "Proposed" auf "Accepted" mit konkretem Modell (2+3)
- ADR-0031 prüfen — was genau braucht WSK von Atlas?
- WSK `counter.py` Hash-Chain-Felder gegen nomos-Format angleichen

---

## 9. Offene Fragen an Joe

1. **Ist WSK-Pilot-0 = der RUF-Pilot?** WSK-CHANGELOG erwähnt
   "Pilot-0-Frontend (Betriebs-Profile, HilfeCounter, Danke-Wall)".
   In der letzten Session sagtest du Pilot-Firma = RUF mit
   "taktical apps" in Beta. Sind das dieselben, oder zwei
   verschiedene Piloten?

2. **Modell 2+3 bestätigt?** Gestaffelte Integration (Pattern-kompat
   → PyPI-Library → Audit-Sink → Annex-IV) — oder anderes Modell?

3. **PyPI-Publish jetzt bestätigen** — Modell 2 hängt daran.
   Master-Plan §7 Frage #2 Empfehlung war "JA". WSK gibt jetzt einen
   zweiten Grund: nicht nur Customer-Friction, sondern WSK braucht es
   als echte Dependency.

4. **Wird das Quadrupel-Center (Zeroth+NomOS+Atlas+WSK) in die
   META-VISION übernommen?** Dann aktualisiere ich
   `2026-05-20-META-VISION.md` entsprechend.

5. **WSK + Atlas Beziehung** — ADR-0031 sagt WSK nutzt Atlas fürs
   Onboarding. Aber Atlas ist Joe-intern. Soll Atlas (nach
   RCE-Fix + IP-Bereinigung) auch WSK-Kunden-shippable werden? Das
   verstärkt die Master-Plan-Frage "Atlas customer-shippable?".

---

## 10. Zusammenfassung in drei Sätzen

WSK ist ein eigenständiges Enterprise-Automation-Projekt (9 Blöcke,
3 Anwendungen, 57 ADRs) das die **Wertschöpfungs-Säule** neben NomOS
(Compliance) und Atlas (Operator) bildet — gemeinsam ein
Quadrupel-Center unter Zeroth. WSK hat die Kopplung WSK-seitig bereits
in ADR-0030 (nomos-Library) + ADR-0031 (Atlas-Onboarding) angelegt,
aber nomos-seitig fehlt der Contract — den dieses Dokument als
gestaffeltes Modell 2+3 vorschlägt. Strategisch ist WSK nomos's
**wichtigster Daten-Lieferant**, weil WSK customer-facing ist
(AIE + ZugangsWeg + KMU-White-Label) und damit die echten
EU-AI-Act-relevanten Events erzeugt die nomos auditiert und in
Annex-IV-PDFs verwandelt.
