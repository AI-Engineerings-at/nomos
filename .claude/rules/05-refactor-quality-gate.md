# Refactor Quality Gate — Kein unvollstaendiges Refactoring

> Gelernt aus Session 01.04.2026: Variable umbenannt, Referenz vergessen = Runtime Crash.

## Nach JEDER Code-Aenderung

1. **Rename:** `grep -r "alterName"` im gesamten Projekt. Null Treffer = OK.
2. **Type-Aenderung:** `grep -r "TypeName"` → alle Fixtures, Mocks, Tests aktualisieren.
3. **Endpoint-Aenderung:** Frontend + Plugin + Tests pruefen. Alle drei.
4. **Test Run:** SOFORT nach jedem Fix. Nicht batchen. Jeder Fix einzeln verifizieren.

## Checkliste vor Commit

- [ ] Grep nach umbenannten Variablen/Funktionen: null Treffer?
- [ ] Alle Fixtures/Mocks aktualisiert die geaenderte Types nutzen?
- [ ] TypeScript: `tsc --noEmit` sauber?
- [ ] Vitest: Alle Tests gruen?
- [ ] pytest: Alle Tests gruen?
- [ ] Keine `newStatus`-artigen Leichen im Code?

## Was NICHT erlaubt ist

- Variable umbenennen und nur die Definition aendern, nicht die Verwendungen
- Type erweitern und Fixtures/Mocks nicht anpassen
- Fix committen ohne vorher Tests zu laufen
- Mehrere Fixes batchen und erst am Ende testen
