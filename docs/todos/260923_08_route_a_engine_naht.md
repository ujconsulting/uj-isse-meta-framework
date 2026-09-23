---
id: 1b2f4727-d0b1-4d82-ae82-ee0ac22f8226
status: offen
aufwand: L
angelegt: 2026-09-02
ziele:
  jira: ISSE-19
punkte:
  40243083-b5de-49f8-8e68-a40b194942c4:
    jira: ISSE-21
  73fab3db-8019-412a-a89e-6274768afd3e:
    jira: ISSE-22
  c2afda7b-bb24-42e4-af70-69d0825647c2:
    jira: ISSE-20
---
# T08 — Route A: Engine-Naht, Subprozess-Muster entfernen, Execution Matrix

**Status: offen** · angelegt 02.09.2026 · Aufwand L

## Zusammenhang

Route A zieht die Upstream-Optimierungen aus dem Branch `upstream-refactor-codebase-plan`
(15 Commits, 3.–6.12.2025) einzeln nach: für die eigene Providerlage umgeschrieben,
geprüft und eigenständig committet — kein Merge, sondern Neuumsetzung mit dem Original
als Referenz. Reihenfolge laut Plan: 1 → 3 → 4 → 2 → 5. Punkt 1 ist erledigt (`837c01f`),
Punkt 2 ist eigenständig unter T03 geführt, Punkt 5 geht in T01 (Oberfläche) auf.

Verbleibend, hier gebündelt, weil #4 an #3 hängt:

- [ ] **#3 `isee_engine.py` extrahieren** — Kernlogik aus `main.py` in ein importierbares <!-- aufgabe:c2afda7b-bb24-42e4-af70-69d0825647c2 -->
      Modul, Voraussetzung für #4. Plan liegt vor
      ([`docs/plans/2026-09-03-engine-naht.md`](../plans/2026-09-03-engine-naht.md)), nach
      fünf Codex-Runden auf `VERDICT: REVISE` stehengeblieben, kein `APPROVED`. Nur die vom
      Plan selbst als unabhängig markierten Vorbereitungsschritte 0a–0d sind erledigt
      (`4b2e84e`, 05.09.2026): `matplotlib.use("Agg")` vor jedem `pyplot`-Import,
      `run_cost_report` wirft keine `SystemExit` mehr, alle 12 SQLite-Verbindungsstellen
      tragen einen `busy_timeout`. Die eigentliche Extraktion (Schritte 1+) hat nicht
      begonnen — Review-Log: [`docs/plans/2026-09-03-engine-naht-review-log.md`](../plans/2026-09-03-engine-naht-review-log.md).
- [ ] **#4 Subprozess-Muster entfernen** — `app.py` importiert die Engine direkt, statt <!-- aufgabe:40243083-b5de-49f8-8e68-a40b194942c4 -->
      `main.py` zu starten und stdout zu parsen. Entfernt die
      Parameter-Übersetzungsschicht (Ausgabeformat, Unicode über die Pipe, verschluckte
      Fortschrittsblöcke), an der mehrere Sitzungen bereits hingen. Größter Einzelgewinn
      der ganzen Route. Schritt 0e (`--workers 1` in `nixpacks.toml`) ist gesetzt; die dort
      ebenfalls geplante Betriebssperre beim Prozessstart (zweiter Prozess lehnt
      `/api/execute` und `/api/status` mit 503 ab) fehlt noch — kein Code dafür in `app.py`.
- [ ] **#6 Execution Matrix** — Upstream-Phase 6 ist selbst mitten in Arbeit („response <!-- aufgabe:73fab3db-8019-412a-a89e-6274768afd3e -->
      loading TBD") und hat `isee-ui.html` um 24 % vergrößert. Entscheiden: selbst zu Ende
      bringen oder auslassen.

## Warnung aus der Korrektur zu Punkt 1

Upstreams Beschreibungen sind Hinweise, keine Befunde — die ursprüngliche Beschreibung von
Punkt 1 stammte ungeprüft aus dem Refactoring-Plan des Originals und war falsch (das
eigentliche Problem war ein komplett toter Live-Fortschritt, nicht nur eine kleine
Ungenauigkeit). Vor jedem weiteren Punkt am eigenen Baum nachmessen, nicht dem
Originalplan glauben. Der Refactoring-Plan des Originals überzeichnet zudem sein Ergebnis
(behauptet −48 %, gemessen ist der Kern 104 Zeilen größer) — beim Nachziehen selbst messen.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 5.1 (Route A, Zeilen
3, 4, 6) inkl. Korrektur zu Punkt 1.
