# NomOS Compliance-Leitfaden

## Uebersicht

NomOS setzt eine Teilmenge der Anforderungen des EU AI Act und der DSGVO durch Software-Kontrollen um. Dieses Dokument ist ehrlich darueber, was NomOS abdeckt, was teilweise abgedeckt ist und was nicht abgedeckt ist.

---

## EU AI Act Abdeckung

### Art. 4 — KI-Kompetenz

| Status | **Teilweise abgedeckt** |
|--------|------------------------|
| Was NomOS tut | Generiert Compliance-Dokumentation (DPIA, Transparenzerklaerung, Logging-Policy) die als Schulungsmaterial dienen kann. Das `ai_disclosure`-Feld in jedem Manifest stellt einen Standard-KI-Hinweis bereit. |
| Was NomOS NICHT tut | Bietet keine Schulungsprogramme, E-Learning oder Kompetenz-Assessments. Dokumentengenerierung ist nicht dasselbe wie organisatorische KI-Kompetenz. |
| Was man noch braucht | Ein organisatorisches KI-Kompetenzprogramm. NomOS-Dokumente koennen Inputs dafuer sein. |

### Art. 6 — Risikoklassifizierung

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Jedes Agent-Manifest enthaelt ein `risk_class`-Feld (`minimal`, `limited`, `high`). Die Risikoklasse bestimmt Governance-Anforderungen — Hochrisiko-Agents brauchen eine Kill Switch Authority. Die Compliance Engine erzwingt risikoklassenspezifische Regeln am Gate. |
| Einschraenkung | NomOS akzeptiert die zugewiesene Risikoklasse. Es bewertet nicht autonom ob die Klassifizierung korrekt ist. |

### Art. 9 — Risikomanagementsystem

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Das blockierende Compliance Gate verhindert Agent-Deployment bis alle Pflichtdokumente existieren. Die Governance Hooks (safety-gate, kill-switch, escalation-tracker) bilden eine Laufzeit-Risikomanagement-Schicht. |
| Einschraenkung | Governance Hooks sind im Manifest definiert, aber ihre Laufzeit-Durchsetzung haengt von der Gateway-Integration (OpenClaw Plugin) ab. |

### Art. 11 — Technische Dokumentation

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | `nomos verify` fuehrt eine vollstaendige technische Dokumentationspruefung durch: Manifest-Schema-Validierung, Geschaeftsregel-Validierung, Compliance-Dokument-Existenz, Manifest-Hash-Integritaet und Audit-Chain-Integritaet. |

### Art. 12 — Aufzeichnungspflicht

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | SHA-256 Hash-Chain Audit Trail. Jedes Agent-Lifecycle-Event wird in einer manipulationssicheren JSONL-Chain aufgezeichnet. `nomos audit --verify` und der API-Endpoint `GET /api/audit/verify/{id}` fuehren kryptographische Chain-Verifikation durch. Das generierte Art. 12 Logging-Policy-Dokument beschreibt was protokolliert wird und wie. |
| Was protokolliert wird | Agent-Erstellung, Deployment, Compliance-Checks, Governance-Hook-Aktivierungen, Kill-Switch-Events, Eskalationen. |

### Art. 13 — Transparenz

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Die Fleet API bietet transparenten Zugang zu Agent-Status, Compliance-Status und Audit Trails. Das Dashboard bietet visuelle Uebersicht ueber alle Agents. |

### Art. 14 — Menschliche Aufsicht

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Kill Switch Konfiguration in jedem Manifest. Das `kill_switch_authority`-Feld definiert wer einen Agent stoppen kann. Das generierte Art. 14 Policy-Dokument beschreibt den Kill-Switch-Mechanismus, Eskalationspfad und autorisierte Personen. Hochrisiko-Agents werden blockiert wenn keine Kill Switch Authority konfiguriert ist. |
| Einschraenkung | Kill-Switch-Durchsetzung haengt von der Gateway-Integration ab. NomOS generiert die Policy und erzwingt die Konfigurationsanforderung, aber der tatsaechliche "Stop"-Mechanismus wird vom OpenClaw Plugin implementiert. |

### Art. 26 — Betreiberpflichten

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | `nomos hire` erstellt Agents mit allen erforderlichen Metadaten. Das Compliance Gate erzwingt Dokumentengenerierung vor dem Deployment. Der Audit Trail liefert den Nachweis der Compliance-Prozesse. |

### Art. 50 — Transparenzpflichten

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Jedes Manifest enthaelt ein `ai_disclosure`-Feld (Standard: "Diese Nachricht wurde mit KI-Unterstuetzung erstellt."). Die Art. 50 Transparenzerklaerung wird vom Compliance Gate generiert. Der `art50-labeler` Governance Hook kennzeichnet (bei Integration ueber Gateway) KI-generierte Ausgaben. |

---

## DSGVO-Abdeckung

### Art. 28 — Auftragsverarbeitung (AVV)

| Status | **Nicht abgedeckt** |
|--------|---------------------|
| Was NomOS tut | Nichts. NomOS generiert keine AVV-Vorlagen. |
| Was man noch braucht | Einen Auftragsverarbeitungsvertrag zwischen dem KI-Agent-Betreiber und jedem Auftragsverarbeiter. Dies ist ein Rechtsdokument das juristische Beratung erfordert. |

### Art. 30 — Verarbeitungsverzeichnis

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Das Compliance Gate generiert ein Verarbeitungsverzeichnis-Dokument mit: Verarbeitungszweck, Verantwortlicher, Kontakt, Datenkategorien, betroffene Personen, Empfaenger, Drittlandtransfers, Loeschfristen und technische Massnahmen. |
| Einschraenkung | Das generierte Dokument verwendet Daten aus dem Manifest. Wenn die Manifest-Daten unvollstaendig oder ungenau sind, ist es das Verarbeitungsverzeichnis auch. Pruefung und Freigabe durch den Verantwortlichen ist erforderlich. |

### Art. 35 — Datenschutz-Folgenabschaetzung (DPIA)

| Status | **Abgedeckt** |
|--------|--------------|
| Was NomOS tut | Das Compliance Gate generiert ein DPIA-Dokument mit: Verarbeitungszweck, Datenbeschreibung, Risikobewertung, technische und organisatorische Massnahmen und ein Ergebnis. Die Risikobewertung beruecksichtigt PII-Filter-Status und Memory-Backend-Konfiguration. |
| Einschraenkung | Dies ist eine generierte Vorlage basierend auf Manifest-Daten. Eine echte DPIA kann zusaetzliche Analyse fuer den spezifischen Anwendungsfall erfordern. Das generierte Dokument muss vom Datenschutzbeauftragten geprueft und unterschrieben werden. |

### Art. 15 — Auskunftsrecht

| Status | **Nicht abgedeckt** |
|--------|---------------------|
| Was NomOS tut | Nichts. NomOS bietet keine Mechanismen fuer Betroffene um Auskunft ueber ihre Daten zu erhalten. |
| Was man noch braucht | Einen Prozess fuer die Bearbeitung von Auskunftsersuchen. Bei Verwendung des Honcho Memory Backends wuerde dies die Abfrage von Honchos User Data Store beinhalten. |

### Art. 17 — Recht auf Loeschung

| Status | **Nicht abgedeckt** |
|--------|---------------------|
| Was NomOS tut | Nichts. NomOS bietet keine Loeschmechanismen fuer einzelne Betroffenendatensaetze. |
| Was man noch braucht | Einen Prozess fuer die Bearbeitung von Loeschanfragen. Bei Verwendung des Honcho Memory Backends wuerde dies das Loeschen von Benutzerdaten aus Honchos Store beinhalten. |

---

## Generierte Compliance-Dokumente

Das Compliance Gate (`nomos gate` / `POST /api/agents/{id}/gate`) generiert diese 5 Dokumente:

| # | Dokument | Dateiname | Rechtsgrundlage |
|---|----------|----------|-----------------|
| 1 | Datenschutz-Folgenabschaetzung (DPIA) | `dpia.md` | Art. 35 DSGVO |
| 2 | Verarbeitungsverzeichnis | `verarbeitungsverzeichnis.md` | Art. 30 DSGVO |
| 3 | Transparenzerklaerung | `art50_transparency.md` | Art. 50 EU AI Act |
| 4 | Human Oversight Policy | `art14_killswitch.md` | Art. 14 EU AI Act |
| 5 | Record-Keeping Policy | `art12_logging.md` | Art. 12 EU AI Act |

Alle Dokumente werden auf Deutsch generiert (wie fuer DACH-Region erforderlich). Sie enthalten Daten aus dem Agent-Manifest und muessen vom Verantwortlichen geprueft und freigegeben werden.

---

## Compliance-Status-Werte

| Status | Bedeutung |
|--------|-----------|
| `passed` | Alle Pflichtdokumente existieren, alle Pruefungen bestanden |
| `warning` | Dokumente fehlen aber Blocking-Modus deaktiviert |
| `blocked` | Dokumente fehlen oder kritische Fehler — Agent kann nicht deployt werden |

Der Blocking-Modus ist standardmaessig aktiviert (`compliance.blocking: true` im Manifest). Das bedeutet ein Agent kann nicht deployt werden bis alle 5 Dokumente generiert und vorhanden sind.

---

## Was NomOS NICHT abdeckt

Um die Grenzen klar zu benennen:

1. **Rechtsberatung** — NomOS generiert Dokumente, keine Rechtsgutachten. Alle generierten Dokumente muessen von qualifiziertem Personal geprueft werden.
2. **AVV (Art. 28 DSGVO)** — Keine Auftragsverarbeitungsvertrag-Vorlagen.
3. **Betroffenenrechte (Art. 15/17 DSGVO)** — Keine Auskunfts- oder Loeschmechanismen fuer einzelne Betroffene.
4. **KI-Kompetenz-Schulung (Art. 4)** — Nur Dokumentation, keine Schulungsprogramme.
5. **Autonome Risikoklassifizierung** — NomOS erzwingt die zugewiesene Risikoklasse, bewertet aber nicht ob sie korrekt ist.
6. **Laufzeit-PII-Filterung** — PII-Filter-Konfiguration ist im Manifest, aber tatsaechliche Filterung erfordert das Honcho Memory Backend. Das lokale Backend filtert kein PII.
7. **Konformitaetsbewertung** — NomOS fuehrt keine Konformitaetsbewertung durch und ersetzt diese nicht, wie sie fuer Hochrisiko-KI-Systeme unter Art. 43 EU AI Act erforderlich ist.
