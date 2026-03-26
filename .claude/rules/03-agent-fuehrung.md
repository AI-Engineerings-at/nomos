# Agent-Fuehrung — Plan lesen, nicht raten

> Gilt fuer jeden Agent der einen Sub-Plan ausfuehrt (Worktree oder Subagent).

## So arbeitest du als Agent

1. **Kompletten Plan lesen** — Nicht nur deine Tasks, den GANZEN Plan.
2. **Endpoint-Liste abgleichen** — Welche Endpoints ruft das Plugin auf? Stimmen deine Pfade?
3. **Types abgleichen** — Welche Response gibt die API? Stimmen deine Frontend-Types?
4. **Self-Check am Ende** — "Geplant vs. Gebaut" Report erstellen.
5. **GAPs melden** — Fehlende Endpoints/Tests explizit als GAP melden, nicht stillschweigend ueberspringen.

## Prompt-Checkliste fuer Agent-Dispatcher

Wenn du einen Agent losschickst, stelle sicher dass der Prompt enthaelt:
- Welche Endpoints das Plugin/Frontend aufruft
- Welche Response-Formate erwartet werden
- Wie der Agent sein Ergebnis verifizieren soll
- "Pruefe ob deine API Response zu den Frontend Types passt"
