# Integration Test Pflicht — Browser vor "fertig"

> Gelernt aus Session 01-05.04.2026: 3 Audits fanden weniger Bugs als 1 Browser-Test.

## Pflicht BEVOR etwas als "fertig" gilt

1. `docker compose build` — Baut ohne Fehler?
2. `docker compose up -d` — Alle Services healthy?
3. Browser oeffnen → Login → Hire → Agent erstellen → Chat
4. F12 oeffnen → Null Errors in Console?
5. Jeden geaenderten Endpoint mit `curl` gegen die laufende API testen

## Was NICHT als Test zaehlt

- TypeScript `tsc --noEmit` → prueft nur Typen, nicht Realitaet
- `vitest run` → prueft Mocks, nicht Docker
- `pytest` → prueft Isolation, nicht Integration
- Schema-Vergleich → prueft Definitionen, nicht Responses
- Sub-Agent Audit → prueft Code, nicht Erlebnis

## Die einzige Frage die zaehlt

> "Kann ein Kunde docker compose up machen, sich einloggen,
> einen Agent einstellen, und mit ihm chatten?"

Wenn die Antwort nicht "ja, getestet" ist, ist nichts fertig.
