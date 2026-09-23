---
id: 1a5e43de-27cd-4cf3-a151-277925d30bd1
status: offen
aufwand: S-M
angelegt: 2026-09-02
ziele:
  jira: ISSE-12
punkte:
  8353a955-32c8-42c8-89d5-d63c06716fda:
    jira: ISSE-13
  f527d7d7-7660-484f-b900-34563b9a3ad9:
    jira: ISSE-14
---
# T06 — Verbrauchsdaten werden nicht persistiert

**Status: offen** · angelegt 02.09.2026 · Aufwand S-M

## Lage

Die Zahlen liegen inzwischen je Lauf in `cost_report.json`, und die Kostenschätzung liest
sie von dort (`516cf51`). **`performance_tracking.db` hat weiterhin keine Spalten
dafür** — dieser Punkt ist also nicht erledigt, nur umgangen.

## Warum es zählt

Ohne Spalten in `performance_tracking.db` lässt sich kein laufender Mittelwert über alle
Läufe bilden — und genau der würde `TYPICAL_RESPONSE_TOKENS = 2500` von einer
Einzelmessung zu einer belastbaren Zahl machen.

## Schritte

- [ ] Spalten für abgerechnete Token je Antwort in `performance_tracking.db` ergänzen <!-- aufgabe:8353a955-32c8-42c8-89d5-d63c06716fda -->
      (Migration, bestehende Zeilen bleiben ohne Wert)
- [ ] laufenden Mittelwert daraus bilden und `TYPICAL_RESPONSE_TOKENS` darauf umstellen <!-- aufgabe:f527d7d7-7660-484f-b900-34563b9a3ad9 -->

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 3.3.
