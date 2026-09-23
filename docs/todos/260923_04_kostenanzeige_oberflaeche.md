---
id: 3cda48e4-69ed-441a-8a48-d32b791f9d28
status: offen
aufwand: S
angelegt: 2026-09-03
ziele:
  jira: ISSE-10
---
# T04 — Kostenbericht in der Oberfläche anzeigen

**Status: offen** · angelegt 03.09.2026 · Aufwand S

## Lage

Die Lesehälfte ist erledigt (`a3c0f6d`): jeder Lauf legt `cost_report.txt` und
`cost_report.json` in sein Verzeichnis, `run_cost_report.py` liest beide Formen und lädt
`.env`, damit die Guthabenzeile auch beim Einzelaufruf erscheint.

**Weiterhin offen:** die Zahl in der Oberfläche selbst zeigen.

## Bewusst zurückgestellt

Bis nach Route A #4 (Subprozess-Muster entfernen, siehe T08) — heute käme die Zahl nur aus
der stdout-Ausgabe des Unterprozesses, und genau diese Schicht entfällt dort.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 2.6.
