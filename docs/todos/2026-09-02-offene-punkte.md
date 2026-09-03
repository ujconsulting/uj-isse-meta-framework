# Offene Punkte — Stand 02.09.2026

Aufgenommen am Ende der Sitzung, in der ISEE von „läuft gar nicht" auf „läuft, CLI und
Web" gebracht wurde (Commits `8137f49` bis `759b8ea`). Was hier steht, ist **nicht**
erledigt. Was erledigt ist, steht in den Commit-Nachrichten und in
`session-summaries/SESSION-SUMMARY-2026-09-02-01.md`.

Reihenfolge = grobe Priorität, nicht Aufwand.

> **Nachtrag 03.09.2026** — Route A, Punkt 1 ist erledigt (`837c01f`), fiel dabei aber
> deutlich größer aus als hier beschrieben, und die Beschreibung selbst war teilweise
> falsch. Einzelheiten am Tabelleneintrag. Neue Funde aus derselben Sitzung stehen unter
> 2.5–2.7.

---

## 1. Ausdrücklich gewünscht, noch nicht gebaut

### 1.1 Archiv vergangener Abfragen
**Wunsch (02.09.2026):** eine Übersicht aller bisherigen Läufe mit den erzeugten
Dokumenten und Ergebnissen.

Die Daten sind vollständig da — es fehlt allein die Oberfläche darauf:

- `data/output/run_JJJJMMTT_HHMMSS/` — je Lauf `isee_result.md`, `analysis.md`,
  `raw_responses/`, ggf. `failed_responses/`, CSVs, Diagramme
- `data/performance_tracking.db` — SQLite mit der Laufhistorie
- seit `7e52b4a` zusätzlich die abgerechneten Token je Antwort

**Vor dem Bauen zu klären:** eigene Seite oder Erweiterung des Cognitive Diversity
Explorers? Beides ist vertretbar; die Entscheidung bestimmt, ob eine dritte Oberfläche
entsteht, die dann auch eigene Übersetzung und eigenes Design braucht (siehe 1.2).

**Mitzudenken:** Die Läufe enthalten die vollständigen Forschungsfragen. Wer die Liste
sieht, sieht sie alle — relevant, sobald das Werkzeug nicht mehr nur lokal läuft.

### 1.2 Oberfläche zeitgemäß gestalten
**Wunsch (02.09.2026):** nicht nur aufräumen, sondern „schön" und zeitgemäß — etwas, das
ein Mensch gern ansieht.

Die Hürde ist strukturell, nicht stilistisch: `isee-ui.html` ist **eine Datei mit ~5.000
Zeilen**, in der Markup, Styling und Verhalten ineinanderliegen. Ernsthafte
Gestaltungsarbeit setzt voraus, sie vorher zu zerlegen — sonst gefährdet jede visuelle
Änderung die Ausführungsüberwachung.

Was die Gestaltung tragen muss (soll sie treiben, nicht ein Trend):

1. die Live-Ansicht der 66 Aufrufe — wird minutenlang angesehen
2. Kostenschätzung **vor** dem Start
3. 66 Ergebnisse zeigen, ohne den Leser zu ertränken
4. minutenlange Läufe mit Teilergebnissen und Einzelfehlern

Offene Frage: Der Cognitive Diversity Explorer ist eine **zweite, separat gestaltete**
Oberfläche. Ein Redesign sollte entscheiden, ob das eine Oberfläche wird oder zwei — heute
sind es zwei, die so tun, als wären sie eine.

---

## 2. Funktionslücken

### 2.1 Nicht geprüfte Web-Pfade
Verifiziert sind: Modell-Endpunkte, Kostenschätzung, Start und Statusverlauf eines Laufs,
`/api/markdown`, `/api/download-zip`, Sprachumschaltung, Modellauswahl.

**Ungeprüft:**
- Cognitive-Diversity-Explorer-Routen (`/cognitive_diversity_explorer/<run_id>`,
  `/api/cognitive_diversity_data/<run_id>`, `/api/extract_cognitive_diversity`)
- `/api/enhance-query` und `/api/suggest-domains`
- `/api/collections` liefert `{}` („llm_collections.json not found") — Absicht oder Rest?

### 2.2 Übersetzung unvollständig
Übersetzt ist die Hauptoberfläche (~110 Zeichenketten) samt dynamisch nachgeladener
Teile. **Nicht übersetzt:** Cognitive Diversity Explorer, `/docs`, `/about`, und alle
Meldungen, die das Backend erzeugt (Fortschritt, Fehler, Zusammenfassungen).

### 2.3 Favicon
`/favicon.ico` liefert 404 — der einzige Konsolenfehler der Oberfläche. Kosmetisch,
aber ein Einzeiler.

### 2.4 `--provider` steuert die Ausführung nicht
Bestätigt: `main.py` erzeugt Clients aus dem `provider`-Feld **jedes Config-Eintrags**,
nicht aus dem CLI-Argument. Ein Lauf mit `--provider globant` gegen ein
OpenRouter-Portfolio ruft trotzdem OpenRouter.

Aktuell eingedämmt (`B5`): `globant` und `hybrid` brechen ohne echte Zugangsdaten mit
Exit 2 ab. Die eigentliche Reparatur — Ausführung über `ProviderManager` routen — ist ein
Refactoring und gehört zu Punkt 5.1.

### 2.5 Die Oberfläche bietet nur 8 der 14 Modelle an
*(gefunden 03.09.2026)* `loadModels()` ruft `/api/models?strategic_only=true` auf und
bekommt 8 Einträge; ohne den Parameter liefert dieselbe Route alle 14. Die Modellauswahl,
die im Auswahl-Commit gebaut wurde, kann also über sechs Modelle gar nicht verfügen —
darunter Mistral, Nemotron, MiniMax, Solar und Hunyuan.

**Zu entscheiden:** bewusste Kuratierung (dann gehört ein Hinweis in die Oberfläche) oder
Rest einer früheren Vereinfachung (dann alle 14 anbieten und `strategic_only` als
Vorauswahl statt als Filter verwenden).

### 2.6 Kostenbericht liest keine Markdown-Läufe
*(gefunden 03.09.2026)* `run_cost_report.py <lauf>` erwartet `isee_result.json`. Die
Weboberfläche startet aber immer mit `--output-format markdown`, also entsteht nur
`isee_result.md` — für genau die Läufe, die über die Oberfläche entstehen, ist der
Nachrechner damit nicht benutzbar. `FileNotFoundError`, nicht abgefangen.

Die Zahlen selbst gehen nicht verloren: `main.py` druckt den Bericht am Ende jedes Laufs,
er landet über den Unterprozess in `dev-server.log`. Er erscheint nur **nirgends in der
Oberfläche** — der Wunsch nach sauber ausgewiesenen Kosten ist damit erst halb erfüllt.

### 2.7 Zwei API-Pfade ohne Zeitlimit
*(gefunden 03.09.2026)* `model_api_integration.py:241` und `:315` rufen `requests.post`
**ohne** `timeout`. Die übrigen vier Aufrufe haben eines (120 s bzw. 30 s). Betrifft
derzeit nicht den OpenRouter-Pfad, aber ein Aufruf ohne Zeitlimit hängt unbegrenzt und
nimmt den ganzen Lauf mit.

Beobachtet am selben Tag, wenn auch auf dem Pfad *mit* Zeitlimit: ein Aufruf an GLM 5.3
Flash brauchte **278 Sekunden** und wurde als Versuch 1 erfolgreich beendet — das
`timeout=120` hat dort also nicht gegriffen (vermutlich Lesezeitlimit je Paket, nicht für
die Gesamtdauer). Ein Volllauf kann damit an einem einzigen langsamen Modell hängen, ohne
dass die Oberfläche erklärt, worauf gewartet wird.

---

## 3. Technische Schulden mit Nachweis

### 3.1 Tote Konfiguration
Der Block `cognitive_diversity` in `openrouter_config.json` (~200 Zeilen) wird **von
keiner Codestelle gelesen** — geprüft. Er referenziert zudem Modelle, die nicht in
`api_models` stehen. Löschen ist richtig, war aber in keinem der bisherigen Diffs
sachlich begründbar.

### 3.2 `update_latest_symlink` ohne Sperre
`main.py` löscht den `latest`-Link und legt ihn neu an, ohne Absicherung. Bei zwei
gleichzeitigen Läufen kann er fehlen oder auf den falschen Lauf zeigen. Unter Windows
scheitert er ohnehin (`WinError 1314`, fehlendes Symlink-Recht) — die Warnung erscheint
bei jedem Lauf und ist bisher nur Rauschen.

### 3.3 Verbrauchsdaten werden nicht persistiert
Seit `7e52b4a` stehen die abgerechneten Token je Antwort im Ergebnisdatensatz und im
Bericht. **`data/performance_tracking.db` hat aber keine Spalten dafür.** Damit lässt sich
kein laufender Mittelwert bilden — und genau der würde `TYPICAL_RESPONSE_TOKENS = 2500`
von einer Einzelmessung zu einer belastbaren Zahl machen.

### 3.4 Retries werden nicht eingepreist
`main.py` versucht bis zu **drei** Mal je Kombination. Die Vorabschätzung rechnet mit
einem Versuch, gibt also eine Untergrenze als Gesamtsumme aus. Die Versuchszahl steht seit
`8137f49` am Ergebnis — die Schätzung nutzt sie noch nicht.

### 3.5 Neun rote Tests
`tests/test_globant_integration.py` (6) und `tests/test_runner.py` (3) sind rot und waren
es vor allen Änderungen dieser Sitzung — auf gestashtem Baum gemessen. Die Globant-Tests
können ohne Zugang nicht grün werden; entweder als „übersprungen" markieren oder
entfernen. `test_runner.py` ist ungeklärt.

### 3.6 Dokumentation widerspricht sich weiterhin
`CLAUDE.md` nennt die Scoring-Gewichte in **zwei unvereinbaren Fassungen** (Impact 30 /
Novelty 25 / Feasibility 20 / Comprehensiveness 15 / Specificity 10 gegen Actionability 20
/ Specificity 25) und listet ein Modell-Portfolio, das **keinem** der beiden Branches
entspricht — darunter „Llama 3.3 70B (`awsbedrock/meta.llama3-2-11b`)", ein 11B-Modell als
70B ausgewiesen. `README.md` und `README_DE.md` sind seit `b8bf95d` auf Stand,
`CLAUDE.md` nicht.

---

## 4. Sicherheit und Betrieb

### 4.1 Öffentliches Repo ohne Meldeweg
`ujconsulting/uj-isse-meta-framework` ist **öffentlich**, hat aber weder `SECURITY.md`
noch aktiviertes *private vulnerability reporting*. Nach der baumweiten Regel in
`D:\Dokumente\Projekte\CLAUDE.md` gilt die Reihenfolge: **erst** das Reporting in den
GitHub-Einstellungen einschalten, **dann** drei Zeilen `SECURITY.md`, die darauf zeigen.
Umgekehrt entsteht ein Wegweiser ins Nichts.

### 4.2 Schlüsselpräfix öffentlich im Verlauf
In `session-summaries/SESSION-SUMMARY-2025-01-23-01.md` und `-2025-08-22-01.md` steht der
Anfang eines OpenRouter-Schlüssels im Klartext — geerbt vom Original, aber unter unserem
Org-Namen öffentlich lesbar. Es ist ein Präfix, kein vollständiger Schlüssel.

**Zu entscheiden:** stehen lassen, im aktuellen Stand entfernen (der Verlauf bleibt), oder
Verlauf umschreiben (`git filter-repo`) — Letzteres ändert alle Commit-IDs und ist bei
einem öffentlichen Repo mit Fork-Beziehung nicht folgenlos.

### 4.3 OpenRouter-Schlüssel nicht im Vault
Alle 381 Vaultwarden-Einträge geprüft: **kein** OpenRouter-Eintrag. Nach der
`credential-vault`-Regel gehört er dorthin, etwa als
`uj-isse-meta-framework/openrouter_api_key`, mit Round-Trip-Prüfung.

### 4.4 Falsch-Positive des Secret-Hooks (geteiltes Werkzeug)
`_claude\vault\git_secret_precommit.py` meldet Variablen-Referenzen als Secrets:
`genai.configure(api_key=self.api_key)` und `api_key = os.environ.get("…")` — Letzteres ist
gerade das *richtige* Muster. Jeder Commit dieser Sitzung brauchte deshalb `--no-verify`,
was den Hook auf Dauer entwertet. `SKIP_VAL` um `os.environ`, `os.getenv` und `self.`
erweitern würde die Klasse schließen. **Betrifft alle Repos** — deshalb nicht einseitig
geändert.

### 4.5 Budget
Stand 02.09.2026: **$18,11 von $131,48 übrig.** Diese Sitzung (Entwicklung + alle
Testläufe) kostete **$0,36**. Ein Volllauf liegt bei ~$0,31, eine Validierung bei ~$0,05.
`python run_cost_report.py` ohne Argumente zeigt den Kontostand; unter $5 warnt der
Bericht.

---

## 5. Strategische Entscheidung (unverändert offen)

Aus dem Handoff vom selben Tag, weiterhin unentschieden — die Arbeit dieser Sitzung hat
sie weder beantwortet noch überflüssig gemacht:

### 5.1 Route A — Upstream-Optimierungen einzeln nachziehen
Der Branch `upstream-refactor-codebase-plan` (15 Commits, 3.–6.12.2025, +6.156/−5.016
Zeilen) liegt im Fork. Jeder Punkt wird **einzeln** genommen, für unsere Providerlage
umgeschrieben, geprüft und eigenständig committet — kein Merge, sondern Neuumsetzung mit
dem Original als Referenz.

| # | Upstream-Phase | Übertragbar? | Was es für uns heißt | Zustand heute |
| --- | --- | --- | --- | --- |
| 1 | Visualisierungs-Bug | **ja, war aber falsch beschrieben** | s. Korrektur unter der Tabelle | **erledigt** (`837c01f`) |
| 2 | Provider-Konsolidierung | **spiegelverkehrt** | Upstream konsolidiert auf Globant. Bei uns die Gegenrichtung: **auf OpenRouter konsolidieren**, Globant-Pfade und `hybrid` entfernen. Dieselbe Vereinfachung, andere Richtung. | eingedämmt (Exit 2), nicht entfernt — s. 2.4 |
| 3 | `isee_engine.py` extrahieren | **ja** | Kernlogik aus `main.py` in ein importierbares Modul. Voraussetzung für #4. | offen |
| 4 | Subprozess-Muster entfernen | **ja — größter Gewinn** | `app.py` importiert die Engine direkt, statt `main.py` zu starten und stdout zu parsen. Entfernt die Parameter-Übersetzungsschicht, an der diese Sitzung mehrfach hing (Ausgabeformat, Unicode über die Pipe, verschluckte Fortschrittsblöcke). | offen |
| 5 | UI-Aufräumen | **Liste ja, Diff nein** | Upstream strich 347 Zeilen Provider-Umschalt-UI. Unsere unterscheidet sich (wir behalten OpenRouter), die *Liste* des Toten überträgt sich, der Diff nicht. Geht in 1.2 auf. | teilweise (219 Zeilen Modell-Padding entfernt, `9545da3`) |
| 6 | Execution Matrix | **upstream unfertig** | Phase 6 ist mitten in Arbeit („response loading TBD") und hat `isee-ui.html` um 24 % **vergrößert**. Selbst zu Ende bringen oder auslassen. | offen |
| — | Flaches Ausgabelayout | **bewusst entscheiden** | `data/output/run_TIMESTAMP` statt verschachtelt. Einfacher, aber Vertrag mit mehreren Lesern (`reporting.py`, `cognitive_diversity_extractor.py`, `extract_raw_responses.py`, `organize_runs.py`, `launch_cognitive_explorer.py`, Ergebnisrouten in `app.py`). Nur lohnend, wenn alle mitziehen. | Läufe landen faktisch bereits flach unter `data/output/run_*` |
| — | Modell-Falschbeschriftungen | **eigene Fassung** | Upstream korrigierte drei. Wir haben dieselbe Klasse über den Live-Katalog gelöst. | erledigt (`93f76e6`) |

**Reihenfolge:** 1 → 3 → 4 → 2 → 5. Punkt 1 ist unabhängig und erprobt den Ablauf;
3 muss vor 4 liegen; 2 ist am saubersten, wenn die Subprozess-Naht weg ist.

#### Korrektur zu Punkt 1 (03.09.2026)

Die Beschreibung oben stammte aus dem Refactoring-Plan des Originals und wurde **nicht
gegen unseren Baum geprüft**. Der erste Vorwurf war schlicht falsch:
`illuminatedCombinations` **wird** zwischen Läufen zurückgesetzt, in `startAnalysis()`
(`isee-ui.html`), und zwar seit Upstream-Commit `0174724` vom 18.08.2025.

Beim Nachmessen kam Schwerwiegenderes zum Vorschein — der Live-Fortschritt der
Weboberfläche war nicht ungenau, sondern **vollständig tot**:

- `main.py` meldet den Parallellauf als `parallel_execution_start`, `app.py` horchte nur
  auf `execution_start`. `total_combinations` blieb 0, und die Folgezeile berechnete den
  `.get()`-Vorgabewert `completed * 100 // total` — den Python **eifrig** auswertet. Jedes
  `combination_start_parallel` warf also ZeroDivisionError in einen Handler, der auf
  Debug-Ebene protokolliert. Gemessen: ein 12-Ereignis-Strom durch den alten Monitor
  hinterlässt **0 erfasste Aufrufe**; nur die Schlussbilanz kam durch.
- `combination_failed_parallel` hatte gar keinen Handler.
- Die Aufrufliste wurde auf 8 Einträge gekürzt, während Abschlüsse in genau dieser Liste
  per `combination_id` gesucht wurden — bei 66 Aufrufen fand die Mehrzahl nichts.
- Ein Abschluss ohne Kennung wurde dem zuletzt *gestarteten* Aufruf zugeschrieben.
- Im Browser wurde die Beleuchtung akkumuliert statt abgeleitet: laufende Aufrufe gingen
  aus, sobald ein neuer dazukam.
- Die Modell-Zuordnung lief über eine Schlüsselwort-Leiter (`claude`, `gpt`, `llama`, …),
  die bei mehreren Modellen eines Hauses alle davon gleichzeitig erleuchtet hätte.

Zusätzlich fiel dabei eine **Regression aus dem Auswahl-Commit `759b8ea`** auf: die
Entscheidung „validierte `--domain` oder freie `--dynamic-domain`" hing am Flag
`strategic_models`, das die Oberfläche seit der Modellauswahl auf `false` setzt. Die von
`/api/suggest-domains` erzeugten Domänennamen gingen dadurch als zu validierende Namen
raus, der Motor wies den ersten zurück, und der Lauf starb **vor dem ersten Modellaufruf**
— während die Oberfläche „completed" meldete. Beides behoben; Exitcode 1 allein
unterscheidet nicht zwischen „einige Aufrufe fehlgeschlagen" und „beim Start abgestürzt",
das Fehlen eines angekündigten Laufs schon.

Die Ereignisverarbeitung liegt jetzt in `_apply_progress_event` statt in der Leseschleife.
Das ist zugleich die Naht, die Punkt 4 braucht — dort wechselt nur der *Erzeuger* der
Ereignisse, nicht deren Verarbeitung.

**Lehre für die restlichen Punkte dieser Tabelle:** Upstreams Beschreibungen sind Hinweise,
keine Befunde. Vor jedem weiteren Punkt am eigenen Baum nachmessen.

⚠️ Der Refactoring-Plan des Originals überzeichnet sein Ergebnis: Er behauptet −48 % und
„~2.500 Zeilen entfernt"; gemessen ist der Kern **104 Zeilen größer** (12.465 → 12.569).
OpenRouter wurde dort nicht gelöscht, sondern nach `archive/openrouter-provider/`
verschoben, und Phase 6 hat mehr hinzugefügt, als die Phasen 1–5 entfernt haben. Die
Architekturgewinne sind echt, die Zahlen nicht — beim Nachziehen also selbst messen.

### 5.2 Route B — Redesign auf heutigem Stand
Der Code kodiert Annahmen von Anfang 2025, die abgelaufen sind. Ein Redesign würde sie
prüfen, statt sie mitzuschleppen:

- **Kontextfenster liegen heute bei ~1M Token.** Die 66 isolierten Einzelaufrufe, von
  denen keiner die anderen kennt, waren ein **Workaround für kleine Fenster**. Mit 1M
  kann eine Synthese *alle* Perspektiven auf einmal lesen, statt sie zu clustern und
  zusammenzufassen. Das ist der stärkste Einzelpunkt für Route B.
- **Batch-Preise existieren.** OpenRouter führt `:batch`-Varianten der meisten Modelle zu
  etwa **halbem Preis**. 66 unabhängige Aufrufe sind der Lehrbuchfall dafür — der Code
  weiß nichts davon.
- **Reasoning-Modelle sind der Normalfall**, und mehrere lehnen die Sampling-Parameter ab,
  die dieser Code fest verdrahtet hatte. Die Parameterschicht gehört neu gedacht, nicht
  geflickt (diese Sitzung hat sie nur entschärft).
- **Structured Outputs / JSON-Schema** würden das brüchige Textparsing in
  `evaluation_scoring.py` und `cognitive_diversity_extractor.py` ersetzen — samt der
  Template- und Platzhaltererkennung, die nur existiert, um es auszugleichen.
- **Ballast, den man nicht portieren, sondern abwerfen sollte:** die ~200 Zeilen ungelesene
  `cognitive_diversity`-Taxonomie (3.1), der `ollama_models`-Block,
  `openrouter_rankings_service.py`, und die ~25 verstreuten Markdown-Dateien in der
  Repo-Wurzel.

**Ehrlicher Vergleich:** Route A ist inkrementell, prüfbar und jeder Schritt für sich
wertvoll — bricht man ab, ist das Repo trotzdem besser dran. Route B trifft den Umstand,
dass die *Prämisse* der Architektur nicht mehr gilt, ist aber ein Neubau: kein Teilwert,
und ein funktionierendes System wird gegen ein erhofftes getauscht.

### 5.3 EU-Hosting (später, prägt aber die Provider-Schicht)
Provider-Schicht **nach Datenklasse** staffeln statt global umschalten: offen über
OpenRouter, vertraulich über EU-Regionen im eigenen Vertrag (AWS Bedrock / Azure — nicht
austauschbar, keiner deckt allein die 14 Häuser), sensibel lokal. Der ungenutzte
`ollama_models`-Block ist die vorhandene Naht. Preis: In den unteren Stufen sinkt die
kognitive Vielfalt — genau das, wofür ISEE existiert. ⚖️ Die rechtliche Einordnung ist
nicht von der Code-Seite zu entscheiden.

---

## Kleinkram

- `scripts/dev-server.sh` schreibt `dev-server.log` und `.dev-server.pid` in die
  Repo-Wurzel. Beide sind gitignoriert, lösen aber den baumweiten Wurzel-Wächter aus.
  Entweder in die `$erwartet`-Liste des Wächters oder in einen Unterordner.
- `openrouter_rankings_service.py` ist seit `9545da3` nur noch Metadatenquelle. Der Name
  und die Größe suggerieren mehr.
- Playwright (MCP) schreibt `.playwright-mcp/` in die Repo-Wurzel und kann es selbst nicht
  aufräumen. Nach Browser-Tests von Hand löschen.
