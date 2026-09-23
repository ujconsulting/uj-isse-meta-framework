---
id: 9a87b1c4-9a90-4405-98f5-0cbd11d5fa9a
status: offen
aufwand: L
angelegt: 2026-09-02
ziele:
  jira: ISSE-23
punkte:
  79521496-14d4-4a5a-944c-bcdce4f3d21d:
    jira: ISSE-24
---
# T09 — Route B: Redesign auf heutigem Stand (strategische Entscheidung)

**Status: offen** · angelegt 02.09.2026 · Aufwand L

## Lage

Der Code kodiert Annahmen von Anfang 2025, die abgelaufen sind. Ein Redesign würde sie
prüfen, statt sie mitzuschleppen:

- **Kontextfenster liegen heute bei ~1M Token.** Die 66 isolierten Einzelaufrufe, von
  denen keiner die anderen kennt, waren ein Workaround für kleine Fenster. Mit 1M kann
  eine Synthese alle Perspektiven auf einmal lesen, statt sie zu clustern und
  zusammenzufassen — stärkster Einzelpunkt für Route B.
- **Batch-Preise existieren.** OpenRouter führt `:batch`-Varianten der meisten Modelle zu
  etwa halbem Preis. 66 unabhängige Aufrufe sind der Lehrbuchfall dafür — der Code weiß
  nichts davon.
- **Reasoning-Modelle sind der Normalfall**, mehrere lehnen die fest verdrahteten
  Sampling-Parameter ab. Die Parameterschicht gehört neu gedacht, nicht geflickt.
- **Structured Outputs / JSON-Schema** würden das brüchige Textparsing in
  `evaluation_scoring.py` und `cognitive_diversity_extractor.py` ersetzen — samt der
  Template- und Platzhaltererkennung, die nur existiert, um es auszugleichen.
- **Ballast, der abgeworfen statt portiert werden sollte:** die ~200 Zeilen ungelesene
  `cognitive_diversity`-Taxonomie, der `ollama_models`-Block,
  `openrouter_rankings_service.py`, die ~25 verstreuten Markdown-Dateien in der
  Repo-Wurzel.

## Abwägung gegen Route A (T08)

Route A ist inkrementell, prüfbar und jeder Schritt für sich wertvoll — bricht man ab, ist
das Repo trotzdem besser dran. Route B trifft den Umstand, dass die Prämisse der
Architektur nicht mehr gilt, ist aber ein Neubau: kein Teilwert, und ein funktionierendes
System wird gegen ein erhofftes getauscht.

## Entscheidung

- [ ] Auftraggeber entscheidet: Route A weiterführen, Route B ansetzen, oder beides <!-- aufgabe:79521496-14d4-4a5a-944c-bcdce4f3d21d -->
      zeitlich staffeln (A zuerst, B als späteres Neubauvorhaben)

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 5.2.
