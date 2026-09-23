---
id: 58173815-08fd-4e8b-b39a-7b356b4a7440
status: offen
aufwand: M
angelegt: 2026-09-02
ziele:
  jira: ISSE-7
punkte:
  c58d5eba-1b44-4a7a-bae5-1ef56770dbe4:
    jira: ISSE-9
  e8d1e49b-b5be-4461-8107-82e3765c9292:
    jira: ISSE-8
---
# T03 — `--provider` steuert die Ausführung nicht

**Status: offen** · angelegt 02.09.2026 · Aufwand M

## Befund

Bestätigt: `main.py` erzeugt Clients aus dem `provider`-Feld **jedes Config-Eintrags**,
nicht aus dem CLI-Argument. Ein Lauf mit `--provider globant` gegen ein
OpenRouter-Portfolio ruft trotzdem OpenRouter.

## Aktueller Stand

Eingedämmt (`B5`): `globant` und `hybrid` brechen ohne echte Zugangsdaten mit Exit 2 ab.
Die eigentliche Reparatur — Ausführung über `ProviderManager` routen — ist ein
Refactoring und gehört inhaltlich zu Route A #2 (Provider-Konsolidierung, siehe T08).

## Entscheidung/Schritte

- [ ] Klären, ob dieses Ticket in T08 (Route A) aufgeht oder eigenständig umgesetzt wird <!-- aufgabe:e8d1e49b-b5be-4461-8107-82e3765c9292 -->
- [ ] Ausführung über `ProviderManager` routen, statt Clients direkt aus dem <!-- aufgabe:c58d5eba-1b44-4a7a-bae5-1ef56770dbe4 -->
      Config-Eintrag zu erzeugen

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 2.4 und 5.1 (Route A, #2).
