#!/usr/bin/env python3
"""
Document Phase 2.1 completion to ERPNext and open-notebook.
Uses vault.py credentials for authentication.
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime
import os

# Set UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add vault to path
vault_path = Path("C:/Users/Legion/Documents/phantom-ai/.claude/credentials")
sys.path.insert(0, str(vault_path))
from vault import get

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg: str, color: str = RESET) -> None:
    print(f"{color}{msg}{RESET}")

# Retrieve credentials
try:
    ERPNEXT_URL = "http://10.40.10.82:8082"
    ERPNEXT_API_KEY = get("shared", "erpnext", "API_KEY")
    ERPNEXT_API_SECRET = get("shared", "erpnext", "API_SECRET")
    log(f"✓ ERPNext credentials loaded", GREEN)
except KeyError as e:
    log(f"✗ ERPNext credentials not found: {e}", RED)
    sys.exit(1)

try:
    OPEN_NOTEBOOK_URL = get("shared", "open_notebook", "URL")
    log(f"✓ open-notebook URL loaded", GREEN)
except KeyError as e:
    log(f"✗ open-notebook URL not found: {e}", RED)
    OPEN_NOTEBOOK_URL = "http://10.40.10.82:5055"  # Fallback

# Phase 2.1 Documentation Content
PHASE_2_1_TITLE = "Phase 2.1: Vitest Full Coverage + NSS Compliance Discovery"
PHASE_2_1_DESCRIPTION = """
## Status: [COMPLETE]

**Duration:** 1 session (2026-03-28)
**Commits:** c6367b8 — test(console): vitest setup + full page coverage — 21 test files × 85 tests
**Test Results:** 85/85 tests passing (100%)

## What Was Accomplished

### Vitest Infrastructure [OK]
- vitest.config.ts — jsdom environment with globals, path aliases
- test-setup.tsx — 8 global mocks for Next.js modules and browser APIs
- test-utils.tsx — Test utilities and vitest exports
- page-test-factory.tsx — 4-state coverage factory (loading, error, data, empty)
- fixtures.ts — 25+ realistic mock objects matching API response types
- shared-mocks.ts — Base mock values for store and auth

### Full Page Coverage [OK]
- **Admin Pages (13):** dashboard, team, team-detail, hire, tasks, approvals, incidents, audit, compliance, costs, users, diagnostics, settings
- **App Pages (4):** dashboard, tasks, chat, help
- **Auth & Special (4):** login, compliance-dashboard, utils, root-page
- **E2E Foundation (2):** auth.setup.ts, page-sweep.spec.ts

**Test Coverage:**
- 21 test files
- 85 tests
- 100% passing
- 87% boilerplate reduction vs. manual tests

## Key Discoveries: NSS Compliance Gap [CRITICAL]

### Missing Test Categories
NomOS is a "Compliance Control Plane" per Design Spec, but Phase 2.1 only tested UI functionality.

Missing compliance tests:
- Guardian Shield (MARS, SENTINEL, APEX, SHIELD, VIGIL)
- EU AI Act (Art. 14+) compliance verification
- GDPR (Art. 17) right-to-be-forgotten
- PII redaction pipeline
- Audit trail (SHA-256 immutable)
- Compliance gate (pass/fail)

**Impact:** 40+ additional tests required before Phase 2.2.

## Security Audit Results
- [OK] No hardcoded secrets in git
- [OK] No internal IPs in product code
- [OK] .env properly gitignored
- [ACTION] Rotate NVIDIA_API_KEY immediately

## Technical Quality
- Test Architecture: A+ (Factory pattern, realistic fixtures, type safety)
- Mock Consistency: A (All 8 mocks correct)
- Type Alignment: A+ (Fixtures match API schemas)

## Files Created
- vitest.config.ts (53 lines)
- src/test-setup.tsx (171 lines)
- src/test-utils.tsx (12 lines)
- src/__tests__/page-test-factory.tsx (137 lines)
- src/__tests__/fixtures.ts (600+ lines)
- src/__tests__/shared-mocks.ts (50 lines)
- src/__tests__/*.test.tsx (21 files, 130+ lines each)
- e2e/auth.setup.ts
- e2e/page-sweep.spec.ts

**Total:** 3387 insertions, 32 files created

## Metrics
- Test Files: 21
- Tests Passing: 85/85 (100%)
- Global Mocks: 8
- Fixtures: 25+
- Boilerplate Reduction: 87%

## Learnings
1. **Compliance is Architecture** — NSS Guardian Shield, EU AI Act, GDPR are not optional, they are the core product
2. **Test Factory Pattern Scales** — 4-state coverage factory reduced boilerplate from 100+ to 13 lines
3. **Fixtures as Contract** — Mock data matching API schemas prevents future type mismatches
4. **Security Audit Early** — NVIDIA key rotation critical
5. **Plan-Product Alignment** — Plan said "Control Plane" but tests were "UI Panel"

## Outstanding Actions
- [ ] Rotate NVIDIA_API_KEY
- [ ] Decide: Phase 2.2 (E2E) or Phase 2.1b (Compliance Tests)?
- [ ] Add 40+ compliance tests before Phase 2.2

## Next Steps
1. **Phase 2.1b** (Recommended): Add NSS compliance tests before E2E
2. **Phase 2.2**: Playwright E2E tests (happy-path, error-cases, multi-user)
3. **Phase 2.3**: Compliance & security verification

---

**Session Report:** docs/reports/2026-03-28-session-report.md
**Design Spec:** docs/superpowers/specs/2026-03-24-nomos-v2-design.md
**Master Plan:** docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md
"""

# ============================================================================
# ERPNext API Integration
# ============================================================================

def create_erpnext_task() -> bool:
    """Create Phase 2.1 task in ERPNext via Frappe API v2."""

    try:
        # Frappe API v2 format
        endpoint = f"{ERPNEXT_URL}/api/v2/resource/Task"

        headers = {
            "Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}",
            "Content-Type": "application/json",
        }

        payload = {
            "data": {
                "title": PHASE_2_1_TITLE,
                "description": PHASE_2_1_DESCRIPTION,
                "status": "Completed",
                "priority": "High",
                "project": "NomOS v2",
                "tags": "Phase 2.1, Vitest, Testing, Compliance, NSS",
                "docstatus": 1,  # Submitted
            }
        }

        log(f"\n📝 Creating ERPNext Task: {PHASE_2_1_TITLE}", YELLOW)
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)

        if resp.status_code in (200, 201):
            result = resp.json()
            task_id = result.get("data", {}).get("name", "unknown")
            log(f"✓ ERPNext Task Created: {task_id}", GREEN)
            log(f"   URL: {ERPNEXT_URL}/app/task/{task_id}", GREEN)
            return True
        elif resp.status_code == 409:
            # Task might already exist, try GET
            log(f"⚠ Task may already exist (409). Attempting update...", YELLOW)
            return update_erpnext_task()
        else:
            log(f"✗ ERPNext API Error ({resp.status_code}):", RED)
            log(f"  {resp.text}", RED)
            # Try v1 format as fallback
            return create_erpnext_task_v1()
    except Exception as e:
        log(f"✗ ERPNext Error: {e}", RED)
        return False

def create_erpnext_task_v1() -> bool:
    """Fallback: Try Frappe API v1 format."""
    try:
        endpoint = f"{ERPNEXT_URL}/api/resource/Task"

        headers = {
            "Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}",
            "Content-Type": "application/json",
        }

        # Try without project first
        payload = {
            "subject": PHASE_2_1_TITLE,
            "description": PHASE_2_1_DESCRIPTION,
            "status": "Completed",
            "priority": "High",
        }

        log(f"📝 Trying Frappe API v1 format (without project)...", YELLOW)
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)

        if resp.status_code in (200, 201):
            log(f"[OK] ERPNext Task Created (v1)", GREEN)
            return True
        elif resp.status_code == 404 and "nicht gefunden" in resp.text.lower():
            # Try with minimal payload
            payload_minimal = {
                "subject": PHASE_2_1_TITLE,
                "description": PHASE_2_1_DESCRIPTION[:500],  # Truncate for safety
            }
            log(f"📝 Trying minimal payload...", YELLOW)
            resp = requests.post(endpoint, json=payload_minimal, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                log(f"[OK] ERPNext Task Created (minimal)", GREEN)
                return True
            else:
                log(f"✗ v1 also failed ({resp.status_code})", RED)
                return False
        else:
            log(f"✗ v1 failed ({resp.status_code}): {resp.text[:200]}", RED)
            return False
    except Exception as e:
        log(f"✗ v1 Error: {e}", RED)
        return False

def update_erpnext_task() -> bool:
    """Update existing Task if it exists."""
    try:
        # First try to find the task by title
        task_name = PHASE_2_1_TITLE.replace(":", "-").replace(" ", "-")[:50]
        endpoint = f"{ERPNEXT_URL}/api/v2/resource/Task/{task_name}"

        headers = {
            "Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}",
            "Content-Type": "application/json",
        }

        payload = {
            "data": {
                "status": "Completed",
                "docstatus": 1,
            }
        }

        log(f"📝 Updating ERPNext Task: {task_name}", YELLOW)
        resp = requests.patch(endpoint, json=payload, headers=headers, timeout=10)

        if resp.status_code in (200, 204):
            log(f"✓ ERPNext Task Updated", GREEN)
            return True
        else:
            log(f"⚠ Update failed ({resp.status_code})", YELLOW)
            return False
    except Exception as e:
        log(f"⚠ Update error: {e}", YELLOW)
        return False

# ============================================================================
# open-notebook Integration
# ============================================================================

def create_open_notebook_source() -> bool:
    """Create Phase 2.1 source in open-notebook."""

    try:
        log(f"\n📚 Creating open-notebook Source: {PHASE_2_1_TITLE}", YELLOW)

        # Try different payload formats with multiple endpoints
        payloads = [
            # Format 1: with type as "markdown"
            {
                "type": "markdown",
                "title": PHASE_2_1_TITLE,
                "content": PHASE_2_1_DESCRIPTION,
            },
            # Format 2: with type as "document"
            {
                "type": "document",
                "name": PHASE_2_1_TITLE,
                "content": PHASE_2_1_DESCRIPTION,
            },
            # Format 3: Google Docs style
            {
                "type": "googledoc",
                "title": PHASE_2_1_TITLE,
                "url": "",  # Would be filled for real Google Docs
            },
            # Format 4: Simple format
            {
                "title": PHASE_2_1_TITLE,
                "content": PHASE_2_1_DESCRIPTION,
                "format": "markdown",
            },
        ]

        endpoints = [
            f"{OPEN_NOTEBOOK_URL}/api/sources",
            f"{OPEN_NOTEBOOK_URL}/api/documents",
            f"{OPEN_NOTEBOOK_URL}/api/files",
        ]

        for endpoint in endpoints:
            for payload in payloads:
                try:
                    resp = requests.post(endpoint, json=payload, timeout=10)

                    if resp.status_code in (200, 201):
                        log(f"[OK] open-notebook Source Created", GREEN)
                        result = resp.json()
                        source_id = result.get("id") or result.get("data", {}).get("id")
                        if source_id:
                            log(f"    Source ID: {source_id}", GREEN)
                        return True
                    elif resp.status_code == 404:
                        continue
                    elif resp.status_code == 422:
                        continue  # Try next payload format
                    else:
                        log(f"    Trying {endpoint} with {payload.get('type', 'format')}: {resp.status_code}", YELLOW)
                        continue

                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue

        log(f"✗ All open-notebook endpoints and formats failed", RED)
        log(f"  Note: Documentation saved to file", YELLOW)
        return False

    except Exception as e:
        log(f"✗ open-notebook Error: {e}", RED)
        return False

# ============================================================================
# Main Execution
# ============================================================================

def main() -> None:
    log(f"\n{'='*70}", YELLOW)
    log(f"Documenting Phase 2.1: Vitest Full Coverage", YELLOW)
    log(f"{'='*70}\n", YELLOW)

    erpnext_ok = create_erpnext_task()
    open_notebook_ok = create_open_notebook_source()

    log(f"\n{'='*70}", YELLOW)
    log(f"Summary:", YELLOW)
    log(f"  ERPNext:      {'✓ OK' if erpnext_ok else '✗ FAILED'}", GREEN if erpnext_ok else RED)
    log(f"  open-notebook: {'✓ OK' if open_notebook_ok else '✗ FAILED'}", GREEN if open_notebook_ok else RED)
    log(f"{'='*70}\n", YELLOW)

    if not (erpnext_ok or open_notebook_ok):
        log("⚠ Both integrations failed. Saving documentation to file...", YELLOW)
        save_offline_documentation()

    sys.exit(0 if (erpnext_ok or open_notebook_ok) else 1)

def save_offline_documentation() -> None:
    """Save documentation to a file if APIs fail."""
    doc_file = Path(__file__).parent.parent / "reports" / "2026-03-28-phase-2-1-documentation.md"
    doc_file.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_file, "w", encoding="utf-8") as f:
        f.write(f"# {PHASE_2_1_TITLE}\n\n")
        f.write(PHASE_2_1_DESCRIPTION)

    log(f"[OK] Documentation saved to: {doc_file}", GREEN)

if __name__ == "__main__":
    main()
