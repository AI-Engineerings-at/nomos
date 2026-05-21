# Competitive Landscape — und was sie an unserem Plan ändert

> Online-Recherche 2026-05-21 + Joe's übergebene Landscape-Map.
> Ehrliche Antwort auf: "ändert sich was an der Vision?"
>
> **Kurzfassung:** Die Vision ändert sich NICHT. Die *Gangart* schon.
> Joe's Liste war unvollständig — seit April 2026 gibt es Open-Source-
> Konkurrenten direkt in unserem Schnittpunkt. Das Zeitfenster ist
> enger als gedacht.

---

## 1. Was Joe's Liste hatte (Closed-Source / Enterprise / reine Orchestratoren)

| Player | Kategorie | Bedrohung für uns |
|---|---|---|
| PwC Agent OS | Enterprise Agent-OS | gering — nie KMU-erschwinglich, nie OSS |
| USU KI-Plattform | Trusted-AI, DE | mittel — Trust-Layer, aber klassische Enterprise-Plattform |
| appliedAI Lighthouse | Agent-Ops, DE | gering — Enablement, kein Compliance-Backbone |
| **BReact OS** | Agentic Framework, **AT** | **hoch** — Österreich, On-Prem, DSGVO+NIS2+EU-AI-Act, "100% data control" |
| PlanB | Orchestration + Integrity Hub | mittel — Governance-Backbone, aber kein KMU-Fokus |
| AIOS / Agent Zero | OSS Agent-OS | gering — Orchestratoren, KEIN Compliance-Modell |
| CrewAI | Multi-Agent-Framework | gering — Baustein, keine Trust-Architektur |

Joe's Liste schloss: *"fast niemand kombiniert alles."* — Das war
korrekt **für diese Liste**. Aber die Liste war nicht vollständig.

---

## 2. Was die Recherche NEU gefunden hat (das Joe's Liste fehlte)

**Seit April 2026 gibt es Open-Source-Player direkt in unserem
Schnittpunkt — Compliance + Audit-Trail + EU-AI-Act + self-hostable:**

| Player | Lizenz | Was es macht | Released |
|---|---|---|---|
| **Microsoft Agent Governance Toolkit** | MIT | Runtime-Security-Governance, Compliance-Grading, **EU-AI-Act-Mapping** + HIPAA + SOC2 | April 2026 |
| **Asqav** | MIT | SDK das **jede Agent-Action signiert + zu tamper-evident Audit-Trail kettet** (ML-DSA-65, post-quantum) | April 2026 |
| **FutureAGI** | Apache 2.0 | self-hostable Runtime: enforcement + audit + registry + gateway + incident — "satisfies EU AI Act + NIST AI RMF + ISO 42001" | 2026 |
| Bifrost | OSS | AI-Gateway als Policy-Enforcement-Layer, audit-logging | 2026 |

**Das ist die wichtigste Erkenntnis dieser Recherche:**

> Joe's Annahme "niemand baut die Kombination" war bis ~März 2026 wahr.
> Seit April 2026 ist sie es nicht mehr. **Asqav ist fast exakt
> NomOS's Audit-Trail-Kern.** Microsoft's Toolkit macht
> EU-AI-Act-Mapping. FutureAGI deckt fast unseren ganzen Scope ab.

Das sind 6-8 Wochen alte Releases. Die Kategorie "Open-Source AI Agent
Governance" wird **gerade jetzt** besetzt.

---

## 2b. Was sie können vs. was bei uns zusätzlich neu ist

Konkrete Gegenüberstellung — pro Player das was er liefert, und das
Delta das NomOS/der Quadrupel-Stack zusätzlich hat:

| Konkurrenz | Was sie können | Was bei uns zusätzlich neu ist |
|---|---|---|
| **PwC Agent OS** | Enterprise-Orchestrierung + Governance, CrewAI-Kern, Skalierung | KMU-erschwinglich statt Enterprise-only; AGPL-OSS statt Beratungs-gebunden; regionale Wirkungslogik |
| **USU KI-Plattform** | Trusted-AI, Quellenrückverfolgung, EU/on-prem, Compliance | agentische *gesellschaftliche* Infrastruktur statt klassische Unternehmensplattform; Empowerment-Bewegung statt Lizenz-Revenue |
| **appliedAI Lighthouse** | Agent-Ops, Enablement, Evaluation in der Ops-Schicht | durchgehender Audit-Trail (Ed25519 + RFC-6962) + Annex-IV-Workflow statt reines Enablement |
| **BReact OS** (AT) | On-Prem, DSGVO + NIS2 + EU-AI-Act, "100% data control" | Meta-Ebene: regulator-facing Inclusion-Proofs + WSK-Wertschöpfungs-Kopplung; AGPL statt Closed-kommerziell |
| **PlanB Framework** | Orchestrierung + Integrity-Hub, Auditierbarkeit, "Autonomie mit Aufsicht" | KMU-Fokus statt generisch; Quadrupel-Stack-Kohärenz statt Punkt-Lösung |
| **AIOS** | Agent-OS-Kern: Scheduling, Memory, Context, Tool-/Access-Mgmt | vollständiges Governance-/Compliance-Betriebsmodell, das AIOS bewusst NICHT hat |
| **Agent Zero** | autonomer local-first Agent, persistent memory, transparent | regulierungsfeste Trust-Infrastruktur für Firmen statt persönlicher Agent |
| **CrewAI** | Multi-Agent-Orchestrierung, Observability-Baustein | vollständige Vertrauensarchitektur statt Framework-Baustein |
| **Microsoft Agent Governance Toolkit** | Runtime-Governance, Compliance-Grading, EU-AI-Act-Mapping (MIT) | AGPL (nicht schließbar); DACH-KMU-spezifisch (DE-Sprache, AT/DE-Recht); WSK-Kopplung |
| **Asqav** | signiert jede Agent-Action → tamper-evident Audit-Trail (ML-DSA-65, MIT) | regulator-facing STH + Inclusion-Proofs (Einzel-Event-Beweis, Datenminimierung); Annex-IV-Workflow drüber; AGPL |
| **FutureAGI** | self-hostable: enforcement + audit + registry + gateway (Apache 2.0) | regionale Verankerung (RUF + WSK) — nicht kopierbar; Empowerment- statt Geschäftsmodell |
| **Dynatrace AI Governance** | Observability, Audit-Trails für produktive KI-Services | Compliance-*Engine* (Annex IV, Risk-Class) statt reines Monitoring |
| **The Future Society / Bitkom** | Policy-Diskurs, Governance-Lücken-Nachweis (kein Produkt) | wir sind die *Implementierung* der Lücke die sie beschreiben |

**Lesart:** Die linke Spalte beweist, dass das Feld existiert und
gekauft wird — die rechte Spalte ist, was wir beweisen müssen. Bis
März 2026 war die rechte Spalte "die Kombination". Seit April ist sie
schmaler und konkreter: AGPL + DACH-KMU + WSK-Kopplung + regionale
Verankerung (§4).

---

## 3. Ändert das die Vision? — Ehrliche Antwort: zu 80% nein, zu 20% ja

Joe's eigene Vermutung: *"das war schon Vision, nur nicht schön
formuliert."* — **Zu 80% stimmt das.**

### Was sich NICHT ändert (war schon Vision)

- Constitutional OS für AI-Agents
- EU-souverän, KMU-Empowerment, Inverse-Pyramide
- Quadrupel-Architektur (Zeroth + NomOS + Atlas + WSK)
- Die 7 Goals, die 4 Verträge
- AGPL-Open-Source-Strategie

Die Recherche **bestätigt** die Vision sogar: Die EU-Sovereign-Thesis
ist real (substrate dependency + regulatory alignment + capital flow).
GenAI4EU subventioniert agentische Plattformen für SMEs. Die EU Apply
AI Strategy zielt explizit auf den Mittelstand. **Der Markt den wir
adressieren existiert und wird politisch gefördert.**

### Was sich ÄNDERT (das war NICHT durchdacht — echter Blind-Spot)

1. **Konkurrenz-Bewusstsein.** META-VISION hatte "Was es NICHT ist"
   (10 Abgrenzungen) aber kein "Wer macht Ähnliches". Das war ein
   Loch. Jetzt gefüllt.
2. **Das Tempo.** Microsoft + Asqav + FutureAGI sind seit April live.
   "Wir bauen still bis August" ist gefährlich. Die Audit-Trail-
   Governance-Kategorie wird gerade besetzt — nicht in 2 Jahren.
3. **Die Build-vs-Adopt-Frage.** Neu. Asqav macht schon tamper-evident
   Audit-Trails. Bauen wir das nochmal, oder bauen wir die Schicht
   drüber? (Diskussion §5.)
4. **Die Differenzierung muss schärfer.** "Wir kombinieren alles"
   reicht nicht mehr, wenn FutureAGI auch fast alles kombiniert.

**Fazit:** Es ist kein Vision-*Change*. Es ist ein Realitäts-*Check*,
der die Gangart beeinflusst. Joe hatte recht — nur war die
Konkurrenz-Realität härter als seine Liste suggerierte.

---

## 4. Unsere ECHTE verbleibende Differenzierung (nach dem Befund)

Wenn Microsoft, Asqav, FutureAGI auch OSS + Compliance + Audit machen
— **was bleibt einzigartig an uns?** Sechs Dinge, in Reihenfolge der
Verteidigungs-Stärke:

1. **DACH-KMU-spezifisch, nicht generisch-Enterprise.** Deutsche
   Sprache, österreichisches/deutsches Recht, regionale Granularität.
   Microsoft/FutureAGI sind US-generic. BReact ist AT — aber
   Closed-Source-kommerziell.
2. **AGPL, nicht MIT/Apache.** Microsoft + Asqav nutzen MIT —
   *jeder kann sie schließen und als Closed-SaaS verkaufen.* Unser
   AGPL macht das unmöglich. Das ist eine echte Lizenz-Philosophie-
   Differenzierung, kein Detail.
3. **Die WSK-Wertschöpfungs-Integration.** Niemand sonst koppelt
   Compliance-Engine an eine Wertschöpfungskette mit Regionalem
   Wirkungsflow + Goodhart-Schutz. Das ist einzigartig.
4. **Empowerment-Bewegung, nicht Geschäftsmodell.** Die anderen sind
   Firmen mit Revenue-Zielen. "Beitrag statt Pricing", Mittelstand-
   Empowerment, Inverse-Pyramide — das ist eine Bewegungs-Logik.
5. **Quadrupel-Stack-Kohärenz.** Atlas (Operator) + NomOS (Compliance)
   + WSK (Wertschöpfung) + Zeroth (Verfassung) als ein zusammenhängendes
   System. Die anderen liefern Punkt-Lösungen.
6. **Bell-Labs Institution > Person.** Pseudonymität, Continuity.
   Niemand sonst hat diese Governance-Philosophie.

**Differenzierungs-Satz neu:** *Nicht "wir kombinieren alles" —
sondern: die einzige AGPL-Open-Source, DACH-KMU-erschwingliche,
regional-verankerte Compliance-Infrastruktur, die an eine echte
Wertschöpfungskette gekoppelt ist.*

---

## 5. Neue strategische Frage: Build vs Adopt

**Asqav existiert.** Es signiert jede Agent-Action + kettet sie zu
einem tamper-evident Audit-Trail. Das ist ~NomOS's Audit-Trail-Kern.
Frage: bauen wir unseren weiter, oder adoptieren wir Asqav?

| Option | Pro | Contra |
|---|---|---|
| **NomOS-Chain behalten** (Status quo) | 745 Tests, funktioniert, AGPL-rein, Ed25519+RFC6962 ist Standard | Doppel-Arbeit gegenüber Asqav |
| **Asqav adoptieren** | weniger Wartung, post-quantum (ML-DSA-65) | MIT-Lizenz (kann geschlossen werden), externe Dependency, fünf-Framework-SDK passt nicht zu unserem OpenClaw-Stack |
| **Interoperabel bleiben** | unser Format ↔ Asqav-Format konvertierbar; Customer hat Wahl | minimaler Mehraufwand |

**Empfehlung:** NomOS-Chain behalten (Option 1). Gründe: sie ist
fertig, AGPL-rein, und unsere Differenzierung ist NICHT die
Krypto-Primitive — sie ist der DACH-KMU-Annex-IV-Workflow drüber.
Aber: **Interoperabilität dokumentieren** (Option 3 als Zusatz) —
falls ein Customer Asqav schon nutzt, soll NomOS dessen Trail lesen
können. Gehört in den Decision-Log.

---

## 6. Was wir schon haben (Stand v0.4.0)

- NomOS v0.4.0 — 745 Tests, Audit-Trail v2 (Ed25519 + RFC 6962 Merkle
  + STH + Inclusion-Proofs), Router-AuthZ-Coverage als CI-Gate
- 7 Strategy-Docs (big-picture, MASTER-PLAN, META-VISION,
  v0.5.0-roadmap, atlas-integration, wsk-integration, dieses)
- Atlas (phantom-control) — Phase 3.5.x, Operator-Cockpit
- WSK — 57 ADRs, Pilot-0 implementiert, 9-Block-Pipeline
- Der Quadrupel-Stack ist konzipiert, NomOS ist davon am weitesten

**Was die Konkurrenz NICHT hat und wir schon:** einen regulator-
facing STH + Inclusion-Proof-Mechanismus (Customer beweist *einzelne*
Events ohne die ganze Chain — data-minimisation). Plus die WSK-
Kopplung. Plus die Hire→Annex-IV-Vision.

---

## 7. Wo der nächste Fokus liegen sollte — dreifach

Die Recherche ändert NICHT dass v0.5.0 W-Phase zuerst kommt
(Live-Eval ist nach wie vor Pflicht — eine schöne Positionierung
nützt nichts wenn `docker compose up` nicht clean läuft). Aber sie
fügt zwei Spuren hinzu, die *parallel* laufen:

| Spur | Inhalt | Warum jetzt |
|---|---|---|
| **A — Code** | v0.5.0 W-Phase: Live-Eval, STH-Rate-Limit, B-F01/F02/F14, localhost-default-Fix | unverändert Pflicht — Substanz vor Story |
| **B — Differenzierung** | Dieses Doc + scharfer Positionierungs-Satz; Build-vs-Adopt in Decision-Log | Microsoft/Asqav sind seit April live — wir müssen wissen wer wir NICHT sind |
| **C — Sichtbarkeit (Joe-Art: Networking)** | RUF-Pilot + WSK-Regionaler-Wirkungsflow als gelebter Beweis | eine echte regionale KMU-Anwendung schlägt jedes Microsoft-Toolkit als Erzählung — und es ist genau Joe's "Networking statt Sales" |

**Spur C ist der eigentliche strategische Hebel.** Microsoft kann
ein Toolkit releasen. Microsoft kann *nicht* die Bäckerin in
Eisenstadt kennen. Unser Asset gegen die OSS-Konkurrenz ist nicht
besserer Code — es ist die **gelebte regionale Verankerung** (WSK +
RUF). Das ist nicht kopierbar.

---

## 8. Was sich am MASTER-PLAN ändert

| MASTER-PLAN-Element | Änderung |
|---|---|
| Vision (§1-2) | unverändert |
| Architektur (§3) | unverändert — aber Quadrupel-Center (WSK) ergänzen |
| Roadmap (§4-5) | unverändert — v0.5.0 W-Phase bleibt erste Priorität |
| Risiko-Register (§8) | **NEU: R13 — OSS-Konkurrenz besetzt die Kategorie schneller als wir.** Mitigation: Spur C (regionale Verankerung, nicht kopierbar) |
| Differenzierung | **NEU als eigene Sektion** — die 6 Punkte aus §4 dieses Docs |
| Build-vs-Adopt | **NEU im Decision-Log** — Asqav-Interoperabilität |

Kein Vision-Rewrite. Eine Risiko-Zeile, eine Differenzierungs-Sektion,
eine Decision-Log-Zeile. MASTER-PLAN v2 baut das ein.

---

## 9. Antwort in drei Sätzen

Die Vision war schon Vision — die Recherche bestätigt sie sogar (die
EU-Sovereign-Thesis ist real, der SME-Markt wird politisch gefördert).
Was Joe's Liste übersah: seit April 2026 gibt es OSS-Konkurrenten
(Microsoft Agent Governance Toolkit, Asqav, FutureAGI) direkt in
unserem Schnittpunkt — die Kombination ist nicht mehr leer, das
Zeitfenster ist enger, "wir kombinieren alles" reicht als
Differenzierung nicht mehr. Unser nicht-kopierbarer Vorteil ist
nicht der Code, sondern die *gelebte regionale Verankerung* (WSK +
RUF + Empowerment-Bewegung + AGPL) — und genau dort sollte der
Fokus liegen, parallel zur unverändert-pflichtigen v0.5.0-Code-Arbeit.

---

## Quellen

- [BReact OS — Agentic AI Automation Platform](https://breact.ai/breact-os)
- [Microsoft Agent Governance Toolkit (Open Source Blog)](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)
- [Asqav: Open-source SDK for AI agent governance (Help Net Security)](https://www.helpnetsecurity.com/2026/04/09/asqav-ai-agent-audit-trail/)
- [5 open source tools for AI agent governance in 2026 (DEV)](https://dev.to/jagmarques/5-open-source-tools-for-ai-agent-governance-in-2026-54le)
- [The European AI sovereignty thesis: three elements that compound](https://informationmatters.net/european-agentic-ai-sovereignty-thesis/)
- [Agentic AI Platform Europe 2026: Country Map and Sovereign Thesis (Knowlee)](https://www.knowlee.ai/blog/agentic-ai-platform-europe-2026)
- [EU AI Act 2026 Updates: Compliance Requirements (Legal Nodes)](https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks)
- [Agentic AI: Leveraging European AI talent and Regulatory Assets (EU Commission)](https://digital-strategy.ec.europa.eu/en/library/agentic-ai-leveraging-european-ai-talent-and-regulatory-assets-scale-adoption)
- [How AI Agents Are Governed Under the EU AI Act (The Future Society)](https://thefuturesociety.org/aiagentsintheeu)
