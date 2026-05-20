# Phase 5a: CLI v2 + Console Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI mit allen neuen Commands + Next.js 15 Console mit Design System, Layout, Auth und Login.

**Architecture:** CLI ruft NomOS API auf (HTTP). Console ist Next.js 15 App Router mit PixiJS fuer Office-Visualisierung, Pixelact UI / shadcn fuer Komponenten, Zustand fuer State, i18n fuer DE/EN.

**Tech Stack:**
- CLI: Python 3.12, Click, httpx
- Console: Next.js 15, TypeScript strict, Tailwind CSS, Zustand, @pixi/react, pixelarticons

---

## Teil 1: CLI v2

### Dateien

```
Erweitern:
  nomos-cli/nomos/cli.py          # +10 neue Commands
  nomos-cli/nomos/core/api.py     # NEU — HTTP Client fuer NomOS API

Tests:
  nomos-cli/tests/test_cli_v2.py  # Tests fuer neue Commands
```

### Neue Commands

```python
# Alle Commands rufen die API auf, kein direkter DB-Zugriff

nomos pause <agent>                      # POST /api/agents/{id}/pause
nomos resume <agent>                     # POST /api/agents/{id}/resume
nomos retire <agent>                     # POST /api/agents/{id}/retire
nomos forget <email>                     # POST /api/dsgvo/forget
nomos assign <agent> --task "desc"       # POST /api/tasks
nomos costs                              # GET /api/costs
nomos costs <agent>                      # GET /api/costs/{agent_id}
nomos incidents                          # GET /api/incidents
nomos workspace mount --agent --coll     # POST /api/workspace/mount
nomos workspace unmount --agent --coll   # POST /api/workspace/unmount
```

### Erfolgs-Kriterien CLI

- [ ] Alle 10 Commands implementiert
- [ ] Jeder Command hat min. 2 Tests (happy path + error)
- [ ] Hilfe-Texte bilingual (--help zeigt DE, --help --lang en zeigt EN)
- [ ] Error Messages menschlich ("Agent nicht gefunden" nicht "404")
- [ ] API Client mit Retry + Timeout

---

## Teil 2: Console Foundation

### Dateien

```
nomos-console/
├── package.json                    # Next.js 15 + deps
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root Layout (Providers, Theme, i18n)
│   │   ├── login/
│   │   │   └── page.tsx            # Login Page (Email + PW + 2FA)
│   │   ├── admin/
│   │   │   └── layout.tsx          # Admin Layout (Sidebar + Header)
│   │   ├── app/
│   │   │   └── layout.tsx          # User Layout (simplified)
│   │   └── compliance/
│   │       └── layout.tsx          # Officer Layout (read-only)
│   ├── components/
│   │   ├── ui/                     # Design System
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── table.tsx
│   │   │   ├── skeleton.tsx        # Loading State
│   │   │   ├── empty-state.tsx     # Empty State mit CTA
│   │   │   └── error-boundary.tsx  # Error Boundary
│   │   ├── layout/
│   │   │   ├── sidebar.tsx         # Sidebar Navigation
│   │   │   ├── header.tsx          # Header (Logo, Theme, Lang, User)
│   │   │   ├── theme-toggle.tsx    # Light/Dark Switch
│   │   │   └── lang-toggle.tsx     # DE/EN Switch
│   │   └── auth/
│   │       ├── login-form.tsx      # Login Form
│   │       └── totp-input.tsx      # 2FA Code Input
│   ├── lib/
│   │   ├── api.ts                  # Typed API Client (fetch + error handling)
│   │   ├── auth.ts                 # Auth Context (JWT, Role, User)
│   │   ├── store.ts                # Zustand Store
│   │   └── i18n/
│   │       ├── index.ts            # i18n Setup
│   │       ├── de.ts               # Deutsche Texte
│   │       └── en.ts               # Englische Texte
│   └── styles/
│       ├── globals.css             # Tailwind + Custom Properties
│       └── design-tokens.css       # Farben, Fonts, Spacing
├── public/
│   ├── logo-new.png                # Eagle Logo (kopiert von Playbook01)
│   ├── logo-new-white.png          # Eagle Logo weiss (fuer Dark Mode)
│   └── sprites/                    # Pixel-Art Sprites (spaeter)
└── e2e/
    └── login.spec.ts               # Playwright: Login Flow
```

### Design Tokens (CSS Custom Properties)

```css
/* design-tokens.css */
:root {
  /* NomOS Brand */
  --color-primary: #4262FF;
  --color-primary-hover: #3451DB;
  --color-accent: #31F1A8;
  --color-accent-hover: #28D494;

  /* Semantic */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  /* Light Mode */
  --color-bg: #FAFAFA;
  --color-card: #FFFFFF;
  --color-text: #1A1A2E;
  --color-muted: #6B7280;
  --color-border: #E5E7EB;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.08);

  /* Typography */
  --font-headline: 'Montserrat', sans-serif;
  --font-body: 'Geist Sans', sans-serif;
  --font-mono: 'Geist Mono', monospace;

  /* Spacing */
  --radius: 8px;
  --transition: 150ms ease;
}

[data-theme="dark"] {
  --color-bg: #0B0C0F;
  --color-card: #1a1919;
  --color-text: #F1F1F1;
  --color-muted: #9CA3AF;
  --color-border: #2D2D2D;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
}
```

### Erfolgs-Kriterien Console Foundation

- [ ] Next.js 15 laeuft auf Port 3040
- [ ] Design System: min. 10 UI-Komponenten
- [ ] Login funktioniert (Email + PW → JWT Cookie)
- [ ] 2FA Input (optional, wenn User 2FA aktiviert hat)
- [ ] Rollenbasiertes Layout (Admin Sidebar ≠ User Sidebar ≠ Officer)
- [ ] Light + Dark Mode toggle (localStorage + OS-Preference)
- [ ] DE + EN switch (localStorage)
- [ ] Eagle Logo (logo-new.png) in Sidebar
- [ ] Error Boundary um jeden Route-Bereich
- [ ] Skeleton Loading States
- [ ] Empty States mit CTA
- [ ] axe-core: 0 critical/serious auf Login
- [ ] Keyboard: Tab durch Login komplett
- [ ] TypeScript strict: 0 Errors
- [ ] Kein generisches Look — Montserrat + Geist, NomOS-Blau + Neon-Green Akzent
