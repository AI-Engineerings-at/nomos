"""NomOS Compliance Gate — generate required compliance documents.

Generates the 5 EU AI Act + DSGVO compliance documents from an agent's
manifest. These documents are REQUIRED before deployment — without them,
the compliance engine returns BLOCKED.

Documents:
1. DPIA (Art. 35 DSGVO)
2. Verarbeitungsverzeichnis (Art. 30 DSGVO)
3. Art. 50 Transparency Declaration (EU AI Act)
4. Art. 14 Human Oversight / Kill Switch Policy (EU AI Act)
5. Art. 12 Record-Keeping / Logging Policy (EU AI Act)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from nomos.core.manifest import AgentManifest


@dataclass
class ComplianceDoc:
    """A generated compliance document."""

    name: str
    title: str
    path: Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


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

*Dieses Dokument wurde automatisch von NomOS generiert und muss vom Verantwortlichen geprueft und freigegeben werden.*
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

*Automatisch generiert von NomOS. Pruefung durch Verantwortlichen erforderlich.*
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

*Automatisch generiert von NomOS. Pruefung durch Verantwortlichen erforderlich.*
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

*Automatisch generiert von NomOS. Pruefung durch Verantwortlichen erforderlich.*
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

*Automatisch generiert von NomOS. Pruefung durch Verantwortlichen erforderlich.*
"""
    path = docs_dir / "art12_logging.md"
    path.write_text(content, encoding="utf-8")
    return ComplianceDoc(name="art12_logging", title="Record-Keeping Policy", path=path)


# Document generator registry
_GENERATORS = {
    "dpia": _generate_dpia,
    "verarbeitungsverzeichnis": _generate_verarbeitungsverzeichnis,
    "art50_transparency": _generate_art50,
    "art14_killswitch": _generate_art14,
    "art12_logging": _generate_art12,
}


def generate_compliance_docs(manifest: AgentManifest, docs_dir: Path) -> list[ComplianceDoc]:
    """Generate all required compliance documents for an agent.

    Creates markdown files in docs_dir for each document listed in
    manifest.compliance.documents_required.
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    results: list[ComplianceDoc] = []

    for doc_name in manifest.compliance.documents_required:
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

    required = manifest.compliance.documents_required if manifest else []
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
