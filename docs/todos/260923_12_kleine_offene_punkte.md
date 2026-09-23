---
id: 1015aa0c-1961-40fa-a726-046aab11f446
status: offen
aufwand: S
angelegt: 2026-09-02
ziele:
  jira: ISSE-31
punkte:
  56ab937c-042c-47fe-8cf3-a1331cbe6106:
    jira: ISSE-33
  73639e06-aeb5-422c-b195-df5d7cd210e5:
    jira: ISSE-32
  fa42ff31-8b90-4a1b-b80b-b342ce94e916:
    jira: ISSE-34
---
# T12 — Kleine offene Punkte (Bündel)

**Status: offen** · angelegt 02.09.2026 · Aufwand S

Drei kleine, voneinander unabhängige Reste aus sonst erledigten oder fast erledigten
Abschnitten.

- [ ] **`/api/collections` liefert `{}`:** Die Route antwortet sauber mit 200 und `{}`, <!-- aufgabe:73639e06-aeb5-422c-b195-df5d7cd210e5 -->
      weil `llm_collections.json` fehlt — geprüft, kein Fehler. Ob die Datei je existieren
      soll (und was sie enthalten müsste), ist weiterhin offen.
- [ ] **Altbestand in NTFS-Datenströmen retten:** Läufe vor dem 03.09.2026 haben ihre <!-- aufgabe:56ab937c-042c-47fe-8cf3-a1331cbe6106 -->
      Rohantworten noch in NTFS-Alternative-Data-Streams stehen (Ursache war ein
      Doppelpunkt in `combination_id`, seither behoben). Sie sind mit PowerShell auslesbar
      (`Get-Item <datei> -Stream *`), gehen aber bei jeder Kopie verloren. Falls die alten
      Läufe erhalten bleiben sollen, wäre eine einmalige Rettungsschleife nötig — bisher
      nicht gemacht; Entscheidung steht aus, ob sich der Aufwand überhaupt lohnt.
- [ ] **`scripts/dev-server.sh` schreibt in die Repo-Wurzel:** `dev-server.log` und <!-- aufgabe:fa42ff31-8b90-4a1b-b80b-b342ce94e916 -->
      `.dev-server.pid` landen im Repo-Root. Beide sind gitignoriert, lösen aber den
      baumweiten Wurzel-Wächter aus. Entweder in die `$erwartet`-Liste des Wächters oder
      in einen Unterordner verlegen.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitte 2.1 (Detailtext), 2.8
(Altbestand-Absatz) und „Kleinkram" (erster Punkt).
