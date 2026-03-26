# PDCA Post-Phase Zyklus — Inhaltlich, nicht formal

> Nach JEDER Phase den kompletten Zyklus durchlaufen.

## So pruefst du eine Phase

1. **Pruefung** — IST/SOLL Vergleich gegen den Plan.
   - Nicht: "Wie viele Endpoints haben wir?"
   - Sondern: "Kann ein Kunde docker compose up machen, sich einloggen, einen Agent einstellen?"
2. **Tests ausfuehren** — Alle Tests auf main (CLI + API + Plugin).
3. **Korrektur** — Luecken identifizieren und schliessen.
4. **Rescope** — Restlichen Plan anpassen.
   - Sind Annahmen fuer spaetere Phasen noch gueltig?
   - Muessen Abhaengigkeiten neu bewertet werden?
5. **Plan ausrichten** — Master Plan aktualisieren mit tatsaechlichem Stand.

## Kein Phasen-Uebergang ohne abgeschlossenen Zyklus.

## Die richtige Audit-Frage

```
"Kann ein Kunde docker compose up machen, sich einloggen,
einen Agent einstellen, und mit ihm chatten?"
```

Nicht: "Wie viele Endpoints/Tests/Zeilen haben wir?"
