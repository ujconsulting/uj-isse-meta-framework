---
id: 0a209904-b089-4fc5-861d-3ccec32acc55
status: offen
aufwand: L
angelegt: 2026-09-02
ziele:
  jira: ISSE-2
---
# T01 — Oberfläche zeitgemäß gestalten

**Status: offen** · angelegt 02.09.2026 · Aufwand L

## Wunsch

Nicht nur aufräumen, sondern „schön" und zeitgemäß — etwas, das ein Mensch gern ansieht.

## Lage

Die Hürde ist strukturell, nicht stilistisch: `isee-ui.html` ist eine Datei mit ~5.000
Zeilen, in der Markup, Styling und Verhalten ineinanderliegen. Ernsthafte
Gestaltungsarbeit setzt voraus, sie vorher zu zerlegen — sonst gefährdet jede visuelle
Änderung die Ausführungsüberwachung.

## Was die Gestaltung tragen muss (soll sie treiben, nicht ein Trend)

1. die Live-Ansicht der 66 Aufrufe — wird minutenlang angesehen
2. Kostenschätzung **vor** dem Start
3. 66 Ergebnisse zeigen, ohne den Leser zu ertränken
4. minutenlange Läufe mit Teilergebnissen und Einzelfehlern

## Offene Frage

Der Cognitive Diversity Explorer ist eine zweite, separat gestaltete Oberfläche. Ein
Redesign sollte entscheiden, ob das eine Oberfläche wird oder zwei — heute sind es zwei,
die so tun, als wären sie eine.

Ein Teil des toten UI-Gewichts (5.1 #5, Modell-Padding) ist bereits entfernt (`9545da3`,
219 Zeilen); der Rest der Liste geht in dieses Redesign auf.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 1.2.
