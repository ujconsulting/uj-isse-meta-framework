---
id: 6296277d-4058-476e-abb5-f0d376c7c4fe
status: offen
aufwand: S-M
angelegt: 2026-09-02
ziele:
  jira: ISSE-3
punkte:
  329afa0a-fcef-484c-916a-f3e0ee44f1b6:
    jira: ISSE-4
  ee3bc489-5e2f-47fa-837f-139f388e6b2d:
    jira: ISSE-5
  f543972c-7a81-4193-bcaf-1ff29c78ccf5:
    jira: ISSE-6
---
# T02 — Übersetzung unvollständig

**Status: offen** · angelegt 02.09.2026 · Aufwand S-M

## Lage

Übersetzt ist die Hauptoberfläche (~110 Zeichenketten) samt dynamisch nachgeladener
Teile. **Nicht übersetzt:** Cognitive Diversity Explorer, `/docs`, `/about`, und alle
Meldungen, die das Backend erzeugt (Fortschritt, Fehler, Zusammenfassungen).

## Schritte

- [ ] Cognitive-Diversity-Explorer-Seiten in die Übersetzungsschicht aufnehmen <!-- aufgabe:329afa0a-fcef-484c-916a-f3e0ee44f1b6 -->
- [ ] `/docs` und `/about` übersetzen <!-- aufgabe:ee3bc489-5e2f-47fa-837f-139f388e6b2d -->
- [ ] Backend-Meldungen (Fortschritt, Fehler, Zusammenfassungen) über dieselbe Schicht <!-- aufgabe:f543972c-7a81-4193-bcaf-1ff29c78ccf5 -->
      statt als hartcodierte Strings ausgeben

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 2.2.
