# Produkt-Standalone — NomOS laeuft beim Kunden

> NomOS ist ein Produkt. Keine interne Infrastruktur.

## So trennst du Produkt von Infra

1. Jede IP-Adresse im Code pruefen: Ist das `10.40.10.x`? → Darf nicht rein.
2. Jede URL pruefen: Zeigt sie auf `.80`, `.82`, `.90`, `.99`? → Darf nicht rein.
3. Stattdessen: Environment Variables oder Docker-interne Hostnamen verwenden.

## Checkliste vor Commit

- Kein `10.40.10.x` in Produkt-Code (nur in Dev-Scripts erlaubt)
- Kein Verweis auf `.80`, `.82`, `.83`, `.90`, `.91`, `.99`
- Alle externen URLs konfigurierbar via ENV
- `docker compose up -d` funktioniert auf einem fremden Server
