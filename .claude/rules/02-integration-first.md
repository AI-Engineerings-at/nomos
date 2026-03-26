# Integration-First — Stack zuerst, Code danach

> Gelernt aus Session 25.03.2026: 18.575 Zeilen Code, 0 funktionierende Flows.
> Postmortem: `docs/reports/2026-03-25-session-postmortem.md`

## So gehst du vor

1. **Docker Stack starten** — ALLE Services muessen healthy sein BEVOR Code geschrieben wird.
2. **Gegen echte Services testen** — Kein in-memory Dict als Ersatz fuer einen Docker Service.
3. **Types von API ableiten** — API starten, Response inspizieren, Types daraus generieren. Nicht erfinden.
4. **Doku lesen** — OpenClaw/NemoClaw Referenz: `docs/references/openclaw-nemoclaw-reference.md`
5. **Browser oeffnen** — Jede Seite testen mit F12 offen. "tsc --noEmit" ist kein Funktionstest.

## Was NICHT erlaubt ist

- Mock API Server als Ersatz fuer fehlende Docker Services
- Python Dict als "functional store" (S9 Verstoss)
- Frontend Types erfinden die nicht zur echten API passen
- Gateway Config raten statt Doku zu lesen (R1 Verstoss)
- 18 Panels bauen und am Ende schauen ob sie funktionieren

## Verifizierung

Ein Feature ist FERTIG wenn:
1. Der Docker Service healthy ist
2. Der API-Call ein korrektes Ergebnis liefert
3. Das Frontend die Daten korrekt anzeigt
4. F12 zeigt null Fehler
