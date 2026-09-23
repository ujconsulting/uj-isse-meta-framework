---
id: 8505f8b4-cd79-47af-8452-ae1db8f1f706
status: offen
aufwand: M
angelegt: 2026-09-05
ziele:
  jira: ISSE-11
---
# T05 — Zwei Ausgabelayouts nebeneinander vereinheitlichen

**Status: offen** · angelegt 05.09.2026 · Aufwand M

## Befund

`app.py` legt `data/output/run_TIMESTAMP` an, `main.py` im Konstruktor
`data/output/YYYY-MM/weekN/run_TIMESTAMP`. Ein Lauf aus dem Browser landet flach, einer
von der Kommandozeile verschachtelt. Das ist kein Rest, beide Pfade laufen parallel.

Bisher dreimal darüber gestolpert, jedes Mal in Code, der eine vollständige Liste zu
liefern vorgab: das Laufarchiv zeigte 7 von 9 Läufen, `latest.txt` zeigte auf ein nicht
existierendes Verzeichnis, und die selbstkorrigierende Kostenschätzung sah ausschließlich
Web-Läufe. Alle drei Leser handhaben jetzt beide Layouts als Übergangslösung.

## Die eigentliche Reparatur

Ein einheitliches Ausgabelayout (vermutlich das flache `data/output/run_TIMESTAMP`, da
Läufe faktisch bereits überwiegend dort landen) — das ist laut `CLAUDE.md` **review-
pflichtig** (Änderung am Run-Ausgabelayout), deshalb hier nicht nebenbei gemacht.

## Solange sie aussteht

Der Cognitive Diversity Explorer kann verschachtelte Läufe gar nicht öffnen: seine Route
und die zwei APIs seiner Seite nehmen eine Lauf-Kennung ohne Schrägstrich, geprüft gegen
`run_YYYYMMDD_HHMMSS`. Das Archiv sagt das inzwischen sichtbar an, statt die Lücke zu
lassen.

## Betroffene Leser (müssen bei der Vereinheitlichung mitziehen)

`reporting.py`, `cognitive_diversity_extractor.py`, `extract_raw_responses.py`,
`organize_runs.py`, `launch_cognitive_explorer.py`, Ergebnisrouten in `app.py`.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 2.10 und 5.1 (Route A,
Zeile „Flaches Ausgabelayout").
