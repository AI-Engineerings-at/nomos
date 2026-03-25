"""NomOS Compliance Gate — generate required compliance documents.

Generates EU AI Act + DSGVO compliance documents from an agent's
manifest. These documents are REQUIRED before deployment — without them,
the compliance engine returns BLOCKED.

Gate v2 generates up to 14 documents based on risk class:
- minimal: 5 base docs
- limited: 9 docs (base + AVV, Risk Mgmt, Betroffenenrechte, AI Literacy)
- high: 14 docs (all, including TIA if LLM location is US)

Documents:
 1. DPIA (Art. 35 DSGVO)
 2. Verarbeitungsverzeichnis (Art. 30 DSGVO)
 3. Art. 50 Transparency Declaration (EU AI Act)
 4. Art. 14 Human Oversight / Kill Switch Policy (EU AI Act)
 5. Art. 12 Record-Keeping / Logging Policy (EU AI Act)
 6. AVV (Auftragsverarbeitungsvertrag) — Art. 28 DSGVO
 7. Risk Management Report — Art. 9 EU AI Act
 8. Betroffenenrechte-Prozess — Art. 15, 17 DSGVO
 9. AI Literacy Checklist — Art. 4 EU AI Act
10. Transfer Impact Assessment (TIA) — Schrems II (only if US location)
11. Art. 22 Policy — Automatisierte Entscheidungen
12. Incident Response Plan — Art. 33/34 DSGVO
13. TOM-Dokumentation — Art. 32 DSGVO
14. Barrierefreiheitserklaerung — BFSG
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from nomos.core.manifest import AgentManifest


_DISCLAIMER = (
    "Automatisch generiert von NomOS. "
    "Dieses Dokument ersetzt keine individuelle Rechtsberatung."
)


@dataclass
class ComplianceDoc:
    """A generated compliance document."""

    name: str
    title: str
    path: Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Base documents (1-5) — generated for ALL risk classes
# ---------------------------------------------------------------------------


def _generate_dpia(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Data Protection Impact Assessment (Art. 35 DSGVO)."""
    content = f"""# Datenschutz-Folgenabschaetzung (DPIA)

**Agent:** {manifest.agent.name}
**Rolle:** {manifest.agent.role}
**Unternehmen:** {manifest.identity.company}
**Risikoeinstufung:** {manifest.agent.risk_class.value}
**Erstellt:** {_now_iso()}

---

## 1. Verarbeitungszweck

Der AI-Agent "{manifest.agent.name}" wird eingesetzt als {manifest.agent.role}
fuer {manifest.identity.company}.

## 2. Beschreibung der Verarbeitung

- **Art der Daten:** Geschaeftskommunikation, Aufgabenverwaltung
- **Betroffene:** Mitarbeiter, Kunden, Geschaeftspartner
- **Speicherdauer:** {manifest.memory.retention.session_messages_days} Tage (Sessions), {manifest.memory.retention.audit_logs_days} Tage (Audit)
- **PII-Filter:** {"Aktiviert (Honcho)" if manifest.memory.backend.value == "honcho" and manifest.memory.pii_filter.enabled else "Nicht aktiv — lokales Backend ohne PII-Filterung" if manifest.memory.pii_filter.enabled else "Deaktiviert"}

## 3. Risikobewertung

| Risiko | Einstufung | Massnahme |
|--------|-----------|-----------|
| Datenverlust | Mittel | Verschluesselte Speicherung, Backup-Policy |
| Unbefugter Zugriff | Niedrig | NemoClaw Sandbox, Credential Guard |
| PII-Exposition | {"Niedrig" if manifest.memory.backend.value == "honcho" and manifest.memory.pii_filter.enabled else "Mittel — PII-Filter nicht aktiv (lokales Backend)" if manifest.memory.pii_filter.enabled else "Hoch"} | PII-Filter {"aktiv (Honcho)" if manifest.memory.backend.value == "honcho" and manifest.memory.pii_filter.enabled else "nicht aktiv — Honcho-Backend fuer PII-Filterung erforderlich" if manifest.memory.pii_filter.enabled else "NICHT aktiv — Massnahmen erforderlich"} |
| Unkontrollierte Aktionen | Niedrig | Safety Gate + Kill Switch |

## 4. Technische und organisatorische Massnahmen

- NemoClaw Sandbox (Netzwerk-Isolation: {manifest.nemoclaw.network_policy})
- Governance Hooks: {", ".join(manifest.governance.hooks_enabled)}
- Kill Switch Authority: {", ".join(manifest.governance.kill_switch_authority) or "NICHT KONFIGURIERT"}
- Audit Trail: Hash-Chain mit {manifest.governance.audit_retention_days} Tagen Aufbewahrung
- PII-Maskierung: Emails={"Ja" if manifest.memory.pii_filter.mask_emails else "Nein"}, Telefon={"Ja" if manifest.memory.pii_filter.mask_phones else "Nein"}

## 5. Ergebnis

Die Verarbeitung ist unter den beschriebenen Massnahmen **zulaessig**.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "dpia.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="dpia", title="Datenschutz-Folgenabschaetzung", path=path)


def _generate_verarbeitungsverzeichnis(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Processing Register (Art. 30 DSGVO)."""
    content = f"""# Verarbeitungsverzeichnis (Art. 30 DSGVO)

**Agent:** {manifest.agent.name}
**ID:** {manifest.agent.id}
**Verantwortlicher:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

| Feld | Wert |
|------|------|
| Bezeichnung der Verarbeitung | AI-Agent: {manifest.agent.name} ({manifest.agent.role}) |
| Verantwortlicher | {manifest.identity.company} |
| Kontakt | {manifest.identity.email} |
| Zweck | {manifest.agent.role} |
| Kategorien betroffener Personen | Mitarbeiter, Kunden, Geschaeftspartner |
| Kategorien personenbezogener Daten | Kommunikationsdaten, Aufgabendaten |
| Empfaenger | Intern: Geschaeftsfuehrung. Extern: Keine |
| Drittlandtransfer | {"Nein (EU-Hosting)" if manifest.nemoclaw.enabled else "Zu pruefen"} |
| Loeschfristen | Sessions: {manifest.memory.retention.session_messages_days}d, Audit: {manifest.memory.retention.audit_logs_days}d |
| Technische Massnahmen | NemoClaw Sandbox, PII-Filter, Audit Chain, Kill Switch |

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "verarbeitungsverzeichnis.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="verarbeitungsverzeichnis", title="Verarbeitungsverzeichnis", path=path)


def _generate_art50(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Art. 50 Transparency Declaration (EU AI Act)."""
    content = f"""# Transparenzerklaerung (Art. 50 EU AI Act)

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## KI-Kennzeichnung

{manifest.identity.ai_disclosure}

## Details

| Feld | Wert |
|------|------|
| Name des KI-Systems | {manifest.agent.name} |
| Anbieter | {manifest.identity.company} |
| Einsatzzweck | {manifest.agent.role} |
| Risikoeinstufung | {manifest.agent.risk_class.value} (EU AI Act Art. 6) |
| Kontakt | {manifest.identity.email} |

## Erklaerung

Dieses System ist ein KI-gestuetzter Agent der fuer {manifest.agent.role}
eingesetzt wird. Alle Ausgaben dieses Systems werden mit folgendem Hinweis
gekennzeichnet:

> {manifest.identity.ai_disclosure}

Die Kennzeichnung erfolgt automatisch durch den Art. 50 Labeler Hook.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "art50_transparency.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="art50_transparency", title="Art. 50 Transparenzerklaerung", path=path)


def _generate_art14(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Art. 14 Human Oversight / Kill Switch Policy (EU AI Act)."""
    authorities = ", ".join(manifest.governance.kill_switch_authority) or "NICHT KONFIGURIERT"
    content = f"""# Human Oversight Policy (Art. 14 EU AI Act)

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## Kill Switch Konfiguration

| Feld | Wert |
|------|------|
| Kill Switch aktiv | Ja |
| Berechtigte Personen | {authorities} |
| Eskalationsschwelle | {manifest.governance.escalation_threshold} Korrekturen |
| Reaktionszeit | Sofort (synchron) |

## Funktionsweise

Der Kill Switch ermoeglicht autorisierten Personen ({authorities}) den
sofortigen Halt aller Agent-Aktivitaeten. Der Switch wirkt auf Gateway-Ebene
und unterbricht:

1. Alle laufenden Operationen
2. Alle ausstehenden Nachrichten
3. Alle geplanten Aufgaben

## Eskalationspfad

1. **Automatisch:** Nach {manifest.governance.escalation_threshold} Korrekturen wird ein Warnhinweis generiert
2. **Manuell:** Autorisierte Person kann jederzeit "STOP" oder "NOTAUS" ausfuehren
3. **Audit:** Jede Kill-Switch-Aktivierung wird im Audit Trail protokolliert

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "art14_killswitch.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="art14_killswitch", title="Human Oversight Policy", path=path)


def _generate_art12(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Art. 12 Record-Keeping / Logging Policy (EU AI Act)."""
    content = f"""# Record-Keeping Policy (Art. 12 EU AI Act)

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## Audit Trail

| Feld | Wert |
|------|------|
| Format | JSONL (JSON Lines) |
| Integritaet | SHA-256 Hash Chain (tamper-evident) |
| Aufbewahrung | {manifest.governance.audit_retention_days} Tage |
| Verifizierung | `nomos audit --verify` oder API GET /api/audit/verify/{{id}} |

## Was wird protokolliert

- Jede Agent-Erstellung (agent.created)
- Jedes Deployment (agent.deployed)
- Jeder Compliance-Check (compliance.check.passed/failed)
- Jede Governance-Hook-Aktivierung (governance.hook.triggered/blocked)
- Jede Kill-Switch-Aktivierung (governance.kill_switch)
- Jede Eskalation (governance.escalation)

## Hash Chain

Jeder Eintrag enthaelt einen SHA-256 Hash der ueber folgende Felder berechnet wird:
- Sequenznummer
- Zeitstempel (UTC ISO 8601)
- Event-Typ
- Agent-ID
- Ereignisdaten
- Hash des vorherigen Eintrags

Manipulation eines Eintrags invalidiert alle nachfolgenden Hashes.

## Export

Der Audit Trail kann fuer Regulatoren exportiert werden:
- `nomos audit --agent-dir <path>` (vollstaendiger Trail)
- `nomos audit --agent-dir <path> --verify` (Integritaetspruefung)
- API: GET /api/agents/{{id}}/audit (JSON)
- API: GET /api/audit/verify/{{id}} (kryptographische Verifikation)

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "art12_logging.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="art12_logging", title="Record-Keeping Policy", path=path)


# ---------------------------------------------------------------------------
# Extended documents (6-9) — generated for limited + high risk
# ---------------------------------------------------------------------------


def _generate_avv(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Auftragsverarbeitungsvertrag (Art. 28 DSGVO)."""
    content = f"""# Auftragsverarbeitungsvertrag (AVV) — Art. 28 DSGVO

**Agent:** {manifest.agent.name}
**Verantwortlicher:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Gegenstand und Dauer der Verarbeitung

Der Auftragsverarbeiter (AI-Agent "{manifest.agent.name}") verarbeitet
personenbezogene Daten im Auftrag von {manifest.identity.company} fuer den
Zweck: {manifest.agent.role}.

Die Verarbeitung erfolgt fuer die Dauer des Einsatzes des AI-Agenten.

## 2. Art und Zweck der Verarbeitung

| Feld | Wert |
|------|------|
| Art der Verarbeitung | Automatisierte Datenverarbeitung durch AI-Agent |
| Zweck | {manifest.agent.role} |
| Art der Daten | Geschaeftskommunikation, Aufgabendaten |
| Kategorien Betroffener | Mitarbeiter, Kunden, Geschaeftspartner |

## 3. Pflichten des Auftragsverarbeiters

- Verarbeitung nur auf dokumentierte Weisung des Verantwortlichen
- Vertraulichkeitsverpflichtung aller Personen mit Zugang
- Technische und organisatorische Massnahmen gemaess Art. 32 DSGVO
- Keine Unterauftragsverarbeiter ohne vorherige Genehmigung
- Unterstuetzung bei Betroffenenrechten (Art. 15-22 DSGVO)
- Loeschung aller Daten nach Beendigung (Retention: {manifest.memory.retention.session_messages_days} Tage)

## 4. Technische und organisatorische Massnahmen

- NemoClaw Sandbox-Isolation
- PII-Filter: {"Aktiv" if manifest.memory.pii_filter.enabled else "Nicht aktiv"}
- Audit Trail mit Hash-Chain-Integritaet
- Kill Switch fuer sofortigen Halt

## 5. Kontakt

Verantwortlicher: {manifest.identity.company} ({manifest.identity.email})

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "avv.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="avv", title="Auftragsverarbeitungsvertrag", path=path)


def _generate_risk_management(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Risk Management Report (Art. 9 EU AI Act)."""
    content = f"""# Risk Management Report — Art. 9 EU AI Act

**Agent:** {manifest.agent.name}
**Risikoeinstufung:** {manifest.agent.risk_class.value}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Risikomanagement-System

Fuer den AI-Agent "{manifest.agent.name}" (Risikoeinstufung: {manifest.agent.risk_class.value})
wurde ein Risikomanagement-System gemaess Art. 9 EU AI Act eingerichtet.

## 2. Identifizierte Risiken

| Risiko | Wahrscheinlichkeit | Auswirkung | Massnahme |
|--------|-------------------|------------|-----------|
| Fehlentscheidung | Mittel | Hoch | Human Oversight (Art. 14), Eskalation nach {manifest.governance.escalation_threshold} Korrekturen |
| Datenverlust | Niedrig | Hoch | Verschluesselung, Backup, Audit Trail |
| PII-Exposition | Mittel | Hoch | PII-Filter, Datensparsamkeit |
| Manipulation | Niedrig | Kritisch | Hash-Chain-Integritaet, NemoClaw Sandbox |
| Unkontrolliertes Handeln | Niedrig | Kritisch | Kill Switch, Safety Gate |

## 3. Risikominderungsmassnahmen

- **Governance Hooks:** {", ".join(manifest.governance.hooks_enabled)}
- **Kill Switch Authority:** {", ".join(manifest.governance.kill_switch_authority) or "NICHT KONFIGURIERT"}
- **Audit Trail:** {manifest.governance.audit_retention_days} Tage Aufbewahrung
- **Sandbox:** NemoClaw mit Profil {manifest.nemoclaw.sandbox_profile.value}

## 4. Ueberwachung und Review

Das Risikomanagement wird laufend ueberprueft. Jede Aenderung am Agent-Manifest
loest eine Neubewertung aus.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "risk_management.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="risk_management", title="Risk Management Report", path=path)


def _generate_betroffenenrechte(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Betroffenenrechte-Prozess (Art. 15, 17 DSGVO)."""
    content = f"""# Betroffenenrechte-Prozess — Art. 15, 17 DSGVO

**Agent:** {manifest.agent.name}
**Verantwortlicher:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Recht auf Auskunft (Art. 15 DSGVO)

Betroffene Personen koennen Auskunft ueber die von "{manifest.agent.name}"
verarbeiteten personenbezogenen Daten anfordern.

**Kontakt:** {manifest.identity.email}
**Frist:** 30 Tage ab Eingang der Anfrage

## 2. Recht auf Loeschung (Art. 17 DSGVO)

Betroffene koennen die Loeschung ihrer Daten verlangen. Der Agent loescht:
- Session-Nachrichten (Retention: {manifest.memory.retention.session_messages_days} Tage)
- Abgeleitete Daten (Retention: {manifest.memory.retention.representations_days} Tage)

Audit-Logs werden gemaess gesetzlicher Aufbewahrungspflicht
{manifest.memory.retention.audit_logs_days} Tage aufbewahrt.

## 3. Recht auf Berichtigung (Art. 16 DSGVO)

Unrichtige Daten werden unverzueglich berichtigt.

## 4. Recht auf Einschraenkung (Art. 18 DSGVO)

Die Verarbeitung kann eingeschraenkt werden. Bei Einschraenkung wird der
Agent-Status auf "paused" gesetzt.

## 5. Recht auf Datenportabilitaet (Art. 20 DSGVO)

Export der Daten im maschinenlesbaren Format (JSON/JSONL) ueber:
- CLI: `nomos audit --agent-dir <path>`
- API: GET /api/agents/{{id}}/audit/export

## 6. Prozess

1. Anfrage per Email an {manifest.identity.email}
2. Identitaetspruefung des Betroffenen
3. Bearbeitung innerhalb von 30 Tagen
4. Dokumentation im Audit Trail

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "betroffenenrechte.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="betroffenenrechte", title="Betroffenenrechte-Prozess", path=path)


def _generate_ai_literacy(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate AI Literacy Checklist (Art. 4 EU AI Act)."""
    content = f"""# AI Literacy Checklist — Art. 4 EU AI Act

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Gemaess Art. 4 EU AI Act muessen Anbieter und Betreiber sicherstellen, dass
Personen die mit KI-Systemen arbeiten ueber ausreichende KI-Kompetenz verfuegen.

## 2. Schulungsinhalte fuer "{manifest.agent.name}"

| Thema | Inhalt | Status |
|-------|--------|--------|
| Grundlagen | Was ist ein AI-Agent? Wie funktioniert "{manifest.agent.name}"? | Offen |
| Einschraenkungen | Grenzen der KI, moegliche Fehler, Halluzinationen | Offen |
| Risikoeinstufung | Bedeutung von "{manifest.agent.risk_class.value}" gemaess EU AI Act | Offen |
| Kill Switch | Wie und wann wird der Kill Switch eingesetzt? | Offen |
| Datenschutz | Welche Daten verarbeitet der Agent? PII-Filter erklaeren | Offen |
| Eskalation | Wann muss an einen Menschen eskaliert werden? | Offen |
| Audit | Wie pruefe ich den Audit Trail? | Offen |

## 3. Zielgruppen

- Geschaeftsfuehrung / Management
- Mitarbeiter die mit dem Agent interagieren
- IT-Administration
- Datenschutzbeauftragter

## 4. Nachweispflicht

Schulungen muessen dokumentiert und nachweisbar sein. NomOS protokolliert
Agent-Interaktionen im Audit Trail.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "ai_literacy.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="ai_literacy", title="AI Literacy Checklist", path=path)


# ---------------------------------------------------------------------------
# High-risk documents (10-14) — generated only for high risk
# ---------------------------------------------------------------------------


def _generate_tia(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Transfer Impact Assessment (TIA) — Schrems II.

    Only generated when LLM location is outside the EU (e.g., US).
    """
    content = f"""# Transfer Impact Assessment (TIA) — Schrems II

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Diese Bewertung prueft die Zulaessigkeit der Datenuebermittlung in Drittlaender
im Zusammenhang mit dem AI-Agent "{manifest.agent.name}" gemaess den
Anforderungen des EuGH-Urteils "Schrems II" (C-311/18).

## 2. Uebermittelte Daten

| Feld | Wert |
|------|------|
| Agent | {manifest.agent.name} |
| Verarbeitungszweck | {manifest.agent.role} |
| Art der Daten | Geschaeftskommunikation, Aufgabendaten |
| Zielland | USA (LLM-Provider) |
| Rechtsgrundlage | Standardvertragsklauseln (SCC) + ergaenzende Massnahmen |

## 3. Risikobewertung Drittland

| Risiko | Bewertung | Massnahme |
|--------|-----------|-----------|
| Zugriff durch Behoerden (FISA 702) | Hoch | Verschluesselung, Datensparsamkeit |
| Fehlender Rechtsschutz | Mittel | SCC + ergaenzende Garantien |
| Datenverlust bei Transfer | Niedrig | TLS-Verschluesselung |

## 4. Ergaenzende Massnahmen

- PII-Filter vor Uebermittlung: {"Aktiv" if manifest.memory.pii_filter.enabled else "Nicht aktiv — ERFORDERLICH"}
- Verschluesselung im Transit (TLS 1.3)
- Minimale Datenuebermittlung (nur notwendige Prompts)
- Audit Trail fuer alle Transfers
- NemoClaw Sandbox-Isolation

## 5. Ergebnis

Die Datenuebermittlung ist unter den beschriebenen ergaenzenden Massnahmen
zulaessig. Eine regelmaessige Neubewertung ist erforderlich.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "tia.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="tia", title="Transfer Impact Assessment", path=path)


def _generate_art22(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Art. 22 Policy — Automatisierte Entscheidungen."""
    content = f"""# Art. 22 Policy — Automatisierte Einzelentscheidungen

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Diese Richtlinie regelt den Umgang mit automatisierten Einzelentscheidungen
gemaess Art. 22 DSGVO im Zusammenhang mit dem AI-Agent "{manifest.agent.name}".

## 2. Grundsatz

Betroffene Personen haben das Recht, nicht einer ausschliesslich auf
automatisierter Verarbeitung beruhenden Entscheidung unterworfen zu werden,
die ihnen gegenueber rechtliche Wirkung entfaltet oder sie in aehnlicher
Weise erheblich beeintraechtigt.

## 3. Massnahmen fuer "{manifest.agent.name}"

| Massnahme | Implementation |
|-----------|---------------|
| Human Oversight | Kill Switch Authority: {", ".join(manifest.governance.kill_switch_authority) or "NICHT KONFIGURIERT"} |
| Eskalationspfad | Nach {manifest.governance.escalation_threshold} Korrekturen |
| Transparenz | Art. 50 Labeler aktiv |
| Widerspruchsrecht | Kontakt: {manifest.identity.email} |

## 4. Prozess bei automatisierter Entscheidung

1. Agent trifft Entscheidung
2. Betroffener wird informiert (Art. 50 Labeler)
3. Betroffener kann Widerspruch einlegen
4. Menschliche Pruefung innerhalb von 48h
5. Dokumentation im Audit Trail

## 5. Ausnahmen

Automatisierte Entscheidungen sind zulaessig wenn:
- Ausdrueckliche Einwilligung vorliegt
- Fuer Vertragserfuellung erforderlich
- Durch Rechtsvorschrift zugelassen

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "art22_policy.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="art22_policy", title="Art. 22 Policy", path=path)


def _generate_incident_response(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Incident Response Plan (Art. 33/34 DSGVO)."""
    content = f"""# Incident Response Plan — Art. 33/34 DSGVO

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Dieser Plan regelt das Vorgehen bei Datenschutzverletzungen im Zusammenhang
mit dem AI-Agent "{manifest.agent.name}" gemaess Art. 33 und Art. 34 DSGVO.

## 2. Meldepflicht (Art. 33 DSGVO)

| Feld | Wert |
|------|------|
| Meldefrist an Aufsichtsbehoerde | 72 Stunden nach Bekanntwerden |
| Meldefrist an Betroffene (Art. 34) | Unverzueglich bei hohem Risiko |
| Verantwortlich | {manifest.identity.company} ({manifest.identity.email}) |

## 3. Erkennungsmechanismen

- **PII-in-Log-Detection:** Automatische Erkennung von PII in Logs
- **Endpoint-Monitoring:** Ueberwachung auf unautorisierte Endpunkte
- **Hash-Chain-Verifikation:** Erkennung von Manipulation
- **Kill Switch:** Sofortiger Halt bei kritischen Vorfaellen

## 4. Reaktionsprozess

1. **Erkennung** (automatisch durch NomOS Incident Detection)
2. **Eindaemmung** (Kill Switch falls erforderlich)
3. **Bewertung** (Schweregrad: critical/high/medium/low)
4. **Meldung** (innerhalb 72h an Aufsichtsbehoerde)
5. **Benachrichtigung** (Betroffene bei hohem Risiko)
6. **Dokumentation** (Audit Trail + Incident Report)
7. **Nachbereitung** (Root Cause Analyse, Massnahmen)

## 5. Eskalationsstufen

| Schweregrad | Massnahme | Frist |
|-------------|-----------|-------|
| Critical | Kill Switch + sofortige Meldung | Sofort |
| High | Meldung an Verantwortlichen | 4h |
| Medium | Dokumentation + Bewertung | 24h |
| Low | Dokumentation | 72h |

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "incident_response.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="incident_response", title="Incident Response Plan", path=path)


def _generate_tom(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate TOM-Dokumentation (Art. 32 DSGVO)."""
    content = f"""# Technische und Organisatorische Massnahmen (TOM) — Art. 32 DSGVO

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Dokumentation der technischen und organisatorischen Massnahmen zum Schutz
personenbezogener Daten bei Einsatz des AI-Agents "{manifest.agent.name}"
gemaess Art. 32 DSGVO.

## 2. Vertraulichkeit

| Massnahme | Implementation |
|-----------|---------------|
| Zugriffskontrolle | NemoClaw Sandbox (Profil: {manifest.nemoclaw.sandbox_profile.value}) |
| Credential Guard | {"Aktiv" if manifest.nemoclaw.credential_guard else "Nicht aktiv"} |
| PII-Filter | {"Aktiv" if manifest.memory.pii_filter.enabled else "Nicht aktiv"} |
| Datenisolation | {manifest.memory.isolation_level.value} |

## 3. Integritaet

| Massnahme | Implementation |
|-----------|---------------|
| Hash Chain | SHA-256, tamper-evident Audit Trail |
| Manifest-Integritaet | SHA-256 Hash-Verifikation |
| Netzwerk-Policy | {manifest.nemoclaw.network_policy} |

## 4. Verfuegbarkeit

| Massnahme | Implementation |
|-----------|---------------|
| Kill Switch | Authority: {", ".join(manifest.governance.kill_switch_authority) or "NICHT KONFIGURIERT"} |
| Audit Retention | {manifest.governance.audit_retention_days} Tage |
| Session Retention | {manifest.memory.retention.session_messages_days} Tage |

## 5. Belastbarkeit

| Massnahme | Implementation |
|-----------|---------------|
| Sandbox-Isolation | NemoClaw mit Netzwerk-Restriction |
| Safety Gate | {"Aktiv" if "safety-gate" in manifest.governance.hooks_enabled else "Nicht aktiv"} |
| Eskalation | Nach {manifest.governance.escalation_threshold} Korrekturen |

## 6. Regeln zur Bewertung

Die Wirksamkeit der Massnahmen wird laufend ueberprueft. Jede Aenderung
am Agent-Manifest oder an der Infrastruktur erfordert eine Neubewertung.

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "tom.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="tom", title="TOM-Dokumentation", path=path)


def _generate_accessibility(manifest: AgentManifest, docs_dir: Path) -> ComplianceDoc:
    """Generate Barrierefreiheitserklaerung (BFSG)."""
    content = f"""# Barrierefreiheitserklaerung — BFSG

**Agent:** {manifest.agent.name}
**Unternehmen:** {manifest.identity.company}
**Erstellt:** {_now_iso()}

---

## 1. Zweck

Diese Erklaerung beschreibt den Stand der Barrierefreiheit des AI-Agents
"{manifest.agent.name}" gemaess Barrierefreiheitsstaerkungsgesetz (BFSG).

## 2. Geltungsbereich

| Feld | Wert |
|------|------|
| Produkt | AI-Agent "{manifest.agent.name}" |
| Anbieter | {manifest.identity.company} |
| Schnittstellen | CLI, API, Console (Web) |

## 3. Stand der Barrierefreiheit

| Anforderung | Status | Anmerkung |
|-------------|--------|-----------|
| Textbasierte Interaktion | Erfuellt | Agent kommuniziert textbasiert |
| Screenreader-Kompatibilitaet | Teilweise | Console-Oberflaeche in Entwicklung |
| Tastaturbedienbarkeit | Erfuellt | CLI vollstaendig per Tastatur bedienbar |
| Farbkontraste | Teilweise | Console-Design in Entwicklung |
| Einfache Sprache | Offen | KI-Ausgaben koennen komplex sein |
| Alternativtexte | Nicht anwendbar | Keine Bilder in Agent-Ausgaben |

## 4. Bekannte Einschraenkungen

- KI-generierte Texte koennen komplex formuliert sein
- Console-Oberflaeche befindet sich in Entwicklung
- Sprachausgabe (TTS) ist optional verfuegbar

## 5. Feedback und Kontakt

Bei Fragen zur Barrierefreiheit wenden Sie sich an:
{manifest.identity.company} ({manifest.identity.email})

---

*{_DISCLAIMER}*
"""
    path = docs_dir / "accessibility.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="accessibility", title="Barrierefreiheitserklaerung", path=path)


# ---------------------------------------------------------------------------
# Document generator registry and risk-class mapping
# ---------------------------------------------------------------------------

_GENERATORS = {
    "dpia": _generate_dpia,
    "verarbeitungsverzeichnis": _generate_verarbeitungsverzeichnis,
    "art50_transparency": _generate_art50,
    "art14_killswitch": _generate_art14,
    "art12_logging": _generate_art12,
    "avv": _generate_avv,
    "risk_management": _generate_risk_management,
    "betroffenenrechte": _generate_betroffenenrechte,
    "ai_literacy": _generate_ai_literacy,
    "tia": _generate_tia,
    "art22_policy": _generate_art22,
    "incident_response": _generate_incident_response,
    "tom": _generate_tom,
    "accessibility": _generate_accessibility,
}

# All 14 document types available in Gate v2
REQUIRED_DOCS_V2: list[str] = list(_GENERATORS.keys())

# Base docs for all risk classes (minimal)
_DOCS_MINIMAL: list[str] = [
    "dpia",
    "verarbeitungsverzeichnis",
    "art50_transparency",
    "art14_killswitch",
    "art12_logging",
]

# Additional docs for limited risk (9 total)
_DOCS_LIMITED: list[str] = _DOCS_MINIMAL + [
    "avv",
    "risk_management",
    "betroffenenrechte",
    "ai_literacy",
]

# All docs for high risk (14 total, TIA conditionally)
_DOCS_HIGH_RISK_BASE: list[str] = _DOCS_LIMITED + [
    "art22_policy",
    "incident_response",
    "tom",
    "accessibility",
]

_DOCS_FOR_RISK: dict[str, list[str]] = {
    "minimal": _DOCS_MINIMAL,
    "limited": _DOCS_LIMITED,
    "high": _DOCS_HIGH_RISK_BASE,
}


def _get_docs_for_risk(risk_class: str, llm_location: str) -> list[str]:
    """Determine which documents to generate based on risk class and LLM location."""
    docs = list(_DOCS_FOR_RISK.get(risk_class, _DOCS_MINIMAL))
    if risk_class == "high" and llm_location == "us":
        docs.append("tia")
    return docs


def generate_compliance_docs(
    manifest: AgentManifest,
    docs_dir: Path,
    llm_location: str = "eu",
) -> list[ComplianceDoc]:
    """Generate all required compliance documents for an agent.

    Creates markdown files in docs_dir based on the agent's risk class.
    Minimal risk: 5 docs, limited risk: 9 docs, high risk: 13-14 docs.
    TIA is only generated when llm_location is "us" (Schrems II).

    Args:
        manifest: The agent's manifest.
        docs_dir: Output directory for compliance documents.
        llm_location: Location of the LLM provider ("eu" or "us").
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    results: list[ComplianceDoc] = []

    doc_names = _get_docs_for_risk(manifest.agent.risk_class.value, llm_location)

    for doc_name in doc_names:
        generator = _GENERATORS.get(doc_name)
        if generator is None:
            continue
        doc = generator(manifest, docs_dir)
        results.append(doc)

    return results


def load_compliance_status(agent_dir: Path) -> dict:
    """Load compliance status for an agent directory.

    Returns dict with: complete (bool), total (int), generated (int),
    missing (list[str]).
    """
    manifest = None
    manifest_file = agent_dir / "manifest.yaml"
    if manifest_file.exists():
        from nomos.core.manifest_validator import load_manifest

        manifest = load_manifest(manifest_file)

    if manifest is None:
        return {
            "complete": False,
            "total": 0,
            "generated": 0,
            "missing": [],
        }

    required = _get_docs_for_risk(manifest.agent.risk_class.value, "eu")
    docs_dir = agent_dir / "compliance"

    generated = 0
    missing = []
    for doc_name in required:
        found = False
        for ext in (".md", ".pdf", ".txt", ".docx", ".html"):
            if (docs_dir / f"{doc_name}{ext}").exists():
                found = True
                break
        if found:
            generated += 1
        else:
            missing.append(doc_name)

    return {
        "complete": generated == len(required) and len(required) > 0,
        "total": len(required),
        "generated": generated,
        "missing": missing,
    }
