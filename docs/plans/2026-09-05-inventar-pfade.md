# Inventar: Pfadauflösung im Motorpfad

**Stand:** 05.09.2026 · **Branch:** `fix/honest-failure-reporting` · Vorarbeit zu
`docs/plans/2026-09-03-engine-naht.md` R5 (Schritt 0d). Reine Recherche, kein Code
geändert.

## Methode

Gegrept über den gesamten Baum (`*.py`, außer `archive/` — laut `CLAUDE.md` Referenz,
kein Laufzeitpfad) nach: `Path(__file__)`, `os.getcwd()`, `sqlite3.connect`,
`subprocess.(Popen|run|call)`, `data/output` (wörtlich und als f-String-Fragment),
`data\\output`. Für jeden Treffer die umgebende Funktion gelesen, um die tatsächliche
Basis zu bestimmen — ein Treffer auf `data/output` allein sagt nichts darüber, ob der
String später mit einer absoluten Basis kombiniert wird oder roh bleibt.

Zusätzlich gezielt gelesen: `main.py::ISEEApplication.__init__` (Zeilen 450–518,
Konstruktion von `run_output_dir`/`output_directory`), `main.py::load_config` (520–531),
`reporting.py` Konstruktor und die vier Schreibstellen (47–61, 680, 752, 880, 965),
`performance_tracker.py`/`enhancement_tracking.py` Konstruktoren, `app.py`s beide
`subprocess`-Aufrufe (821–831 und 2994–3000) im Vergleich, `launch_cognitive_explorer.py`
(1–100), `organize_runs.py` (1–40), sowie `Dockerfile` und `nixpacks.toml` für die
Arbeitsverzeichnis-Vorgabe der Auslieferung.

Nicht gelesen: `.env`/`.env.template` (Tabu-Scope), `data/output/*` (Laufdaten),
`tools/codex_ro.py` (Review-Werkzeug, nicht Teil der Web→Motor-Naht).

---

## Tabelle

Spalten: **Datei:Zeile** · **Was aufgelöst wird** · **Woher der Basispfad kommt** ·
**relativ zu cwd?** · **wer setzt ihn**.

| Datei:Zeile | Was aufgelöst wird | Woher der Basispfad kommt | relativ zu cwd? | wer setzt ihn |
|---|---|---|---|---|
| `main.py:530` (`load_config`, aufgerufen aus `main.py:3182`) | Konfigurationsdatei (`--config`) | `args.config` — eine bare Zeichenkette (`"openrouter_config.json"` o. ä.) wird direkt an `open(...)` gereicht | **ja** | CLI-Nutzer / bei Web-Läufen `app.py` (Dateiname aus `provider` abgeleitet, s. Parameter-Inventar) |
| `model_api_integration.py:21` | `.env`-Datei | `Path(__file__).parent / '.env'` | **nein** — ausdrücklich gegen den Modulpfad, nicht cwd | fest im Code, einzige cwd-unabhängige Stelle im ganzen Motorpfad |
| `main.py:500-508` (`ISEEApplication.__init__`, wenn **kein** `output_directory` übergeben) | Lauf-Verzeichnis, organisiert: `data/output/YYYY-MM/weekX/run_TIMESTAMP` | `os.path.join(organized_path, f"run_{timestamp}")`, `organized_path` aus einem reinen String-Literal `"data/output/…"` gebaut | **ja** | die Engine selbst — das ist der Pfad, den eine bare CLI-Ausführung bekommt |
| `main.py:511-514` | Basisverzeichnisse `data/`, `data/output/`, `data/state/`, sowie das konkrete Lauf-Verzeichnis | `os.makedirs("data", …)` usw. — Literale, unabhängig davon, ob `output_directory` gesetzt war | **ja** | die Engine, unbedingt bei jeder Instanziierung |
| `app.py:737` (`execute_isee_command`) | Lauf-Verzeichnis für einen Web-Lauf: `data/output/run_TIMESTAMP` (**flach**, nicht organisiert) | `Path("data/output") / f"run_{timestamp}"`, `timestamp` **von `app.py` selbst** über `datetime.now()` erzeugt — nicht derselbe Zeitstempel, den `ISEEApplication` intern bilden würde | **ja**, relativ zum cwd des Flask/Gunicorn-Prozesses zum Zeitpunkt des Requests | `app.py`, ausdrücklich, **bevor** die Engine überhaupt instanziiert wird |
| `app.py:748-749` | `--output-file` für einen Web-Lauf | `run_dir / f"isee_result.{extension}"`, `run_dir` wie oben | **ja**, gleiche Basis wie `app.py:737` | `app.py` |
| `app.py:821-831` (`subprocess.Popen`) | Arbeitsverzeichnis des Motor-Unterprozesses selbst | `cwd=Path(__file__).parent` — **Modulpfad von `app.py`**, nicht der cwd des Flask-Prozesses | **nein** — bewusst gegen den Modulpfad gepinnt | `app.py`, hartkodiert |
| `main.py:3071`, `main.py:3204` | Domänen-Konfigurationsdatei (`--domain-config`) | `args.domain_config`, bare String an `os.path.exists`/`open` | **ja** | CLI-Nutzer; vom Web-Pfad nie gesetzt (s. Parameter-Inventar) |
| `main.py:1122`, `main.py:1826` | `raw_responses/` bzw. `failed_responses/` je Antwort | `Path(self.output_directory) / "raw_responses"` — Basis ist `self.output_directory`, also das Ergebnis der beiden Zeilen oben (`main.py:500-508` **oder** der von `app.py` übergebene `--output-directory`-Wert) | **ja**, geerbt | Engine, abgeleitet |
| `reporting.py:47,56,61` | Basisverzeichnis für alle Berichte (Konstruktor-Default `"data/output"`, überschrieben durch `run_output_dir`, wenn übergeben) | Default-Parameter-String **oder** der von `main.py`/`app.py` durchgereichte `run_output_dir` | **ja** | Aufrufer von `ReportGenerator(...)` — in der Praxis immer mit `run_output_dir=app.run_output_dir` aufgerufen (main.py:3577), also derselbe geerbte Wert wie oben |
| `reporting.py:680,752,880,965` | einzelne Berichtsdateien (Markdown/JSON/CSV) | `os.path.join(self.output_directory, filename)` | **ja**, geerbt | `reporting.py`, abgeleitet |
| `performance_tracker.py:40-46,216,335,357,379` | `performance_tracking.db` | Konstruktor-Default `db_path: str = "data/performance_tracking.db"`, **nirgends** im Repo mit einem anderen Wert instanziiert (geprüft: `app.py:854`, `performance_tracker.py:412` — beide ohne Argument) | **ja** | fest im Code; wirkt sowohl bei der Engine (falls sie selbst schreibt) als auch bei `app.py`s Nachbearbeitung nach Subprozess-Ende (`app.py:850-878`) — **letztere läuft im cwd des Flask-Prozesses, nicht im gepinnten `Path(__file__).parent` des Kindes** |
| `enhancement_tracking.py:62-63,69,144,174,208,230,272,319` | `enhancement_tracking.db` | Konstruktor-Default `db_path: str = "data/enhancement_tracking.db"`, gewrappt in `Path(...)`, nirgends mit anderem Wert instanziiert (`enhancement_tracking.py:396`) | **ja** | fest im Code |
| `app.py:2994-3000` | zweiter Unterprozess: `cognitive_diversity_extractor.py` | `script_path = os.path.join(os.getcwd(), 'cognitive_diversity_extractor.py')`; `subprocess.run([…], cwd=os.getcwd(), …)` | **ja**, und zwar an **zwei** Stellen im selben Aufruf (Skriptpfad *und* `cwd`) | `app.py` — ⚠️ siehe Widerspruch unten, andere Basis als der Motor-Unterprozess |
| `app.py:2277,2350,2356,2398,2402-2405,2446,2946,2959,3046,3100,3130,3175` | diverse Lese-/Serving-Routen für Lauf-Ergebnisse (`/api/status`, `/api/markdown`, ZIP-Export, Explorer-Start …) | durchgängig `Path("data/output")` bzw. f-Strings mit `data/output/…` | **ja** | `app.py`, jede Route für sich, keine gemeinsame Konstante |
| `launch_cognitive_explorer.py:85` | eigene HTML-Vorlage (`cognitive_diversity_web.html`) | `Path(__file__).parent / "cognitive_diversity_web.html"` | **nein** | fest im Code |
| `launch_cognitive_explorer.py:60` (`handle_raw_response_request`) | Basisverzeichnis für angeforderte Rohantwort-Dateien | `Path(self.index_file).parent` — `index_file` kommt als **positionales CLI-Argument** (`sys.argv[1]`, s. `launch_cognitive_explorer.py:205`) | **ja**, falls das Argument relativ übergeben wird | Aufrufer des Skripts — ⚠️ dieselbe Datei nutzt an zwei Stellen zwei verschiedene Basen (s. u.) |
| `main.py:2957-2985` (`update_latest_symlink`), `read_raw_responses.py:17,55`, `enable_raw_response_storage.py:165,203` | `data/output/latest`-Zeiger | Literal `Path("data/output/latest")` | **ja** | keiner aktiv — laut Code-Kommentar (`main.py:2966`) und `tests/test_latest_pointer.py:9` existiert dieser Zeiger auf dieser Maschine nie; tote, aber weiterhin gelesene Stelle |
| `organize_runs.py:26-27`, `undo_organization.py:9`, `extend_weekly_organization.py:26` | Basisverzeichnis für die Lauf-Reorganisation, **plus** `os.chdir(output_dir)` unmittelbar danach | hartkodiertes Literal `"/Users/josephfajen/git/ISEE_Meta_Framework/data/output"` — der absolute Pfad der Original-Maschine des Upstream-Autors | **nein** — absolut, aber auf einen Pfad, der auf diesem Fork nicht existiert | niemand hat es an diesen Fork angepasst |
| `Dockerfile:4` (`WORKDIR /app`) | Arbeitsverzeichnis für `CMD ["python", "app.py"]` | Docker-`WORKDIR`-Direktive | (setzt cwd, wird nicht relativ zu ihm aufgelöst) | Deployment-Konfiguration |
| `nixpacks.toml` (`[start] cmd = "gunicorn … app:app"`) | Arbeitsverzeichnis für den Gunicorn-Start | **keine ausdrückliche Vorgabe in dieser Datei** | nicht ermittelbar aus dieser Datei allein | nixpacks/Railway-Konvention (nicht geprüft, s. „Nicht ermittelt") |

---

## ⚠️ Gefundene Widersprüche

1. **Zwei Unterprozess-Starts in `app.py`, zwei verschiedene Basen.** Der Haupt-Motor
   wird mit `cwd=Path(__file__).parent` gestartet (app.py:829) — unabhängig vom
   Arbeitsverzeichnis des Flask-Prozesses selbst. Der zweite Unterprozess
   (`cognitive_diversity_extractor.py`, app.py:2994-3000) verwendet stattdessen
   `os.getcwd()` für **beides**, den Skriptpfad *und* `cwd`. Beide Aufrufe funktionieren
   heute nur, weil `app.py` konventionell aus dem Repo-Root gestartet wird — nichts im
   Code erzwingt das. Startete jemand `python app.py` aus einem anderen Verzeichnis, würde
   der erste Unterprozess weiterhin `main.py` finden (weil sein `cwd` auf den Modulpfad
   gepinnt ist), der zweite aber nicht (`cognitive_diversity_extractor.py` würde am
   falschen Ort gesucht). Genau die Art Inkonsistenz, vor der R5 warnt — sie besteht
   bereits **heute**, unabhängig vom geplanten Umbau.
2. **`app.py`s eigene Datenbank-Nachbearbeitung läuft außerhalb der gepinnten Basis.**
   Nach Ende des Motor-Unterprozesses ruft `app.py:854` `PerformanceTracker()` auf —
   ***im Flask-Prozess***, nicht im gepinnten `cwd` des Kindes. `data/performance_tracking.db`
   wird also relativ zum cwd von `app.py` selbst aufgelöst, während `raw_responses/` und
   die Berichte relativ zum (Modulpfad-gepinnten) cwd des Kindes entstanden. Beide Basen
   fallen heute zusammen, weil beide Prozesse de facto im selben Verzeichnis laufen — aber
   das ist eine Annahme, keine erzwungene Eigenschaft.
3. **`app.py:737` erzeugt einen eigenen Zeitstempel und damit ein eigenes
   Verzeichnis-Layout**, das vom organisierten Layout abweicht, das `ISEEApplication`
   selbst bilden würde, wenn man ihr kein `output_directory` vorgäbe (s. auch
   Parameter-Inventar, Widerspruch 4). Für die Pfad-Frage hier ist relevant: **jedes**
   Werkzeug, das das organisierte Layout `data/output/YYYY-MM/weekX/…` erwartet
   (`organize_runs.py`, `extend_weekly_organization.py`), findet Web-Läufe nie an der
   erwarteten Stelle, weil sie flach unter `data/output/run_TIMESTAMP` liegen.
4. **`launch_cognitive_explorer.py` mischt zwei Basen in derselben Datei.** Die
   Werkzeug-eigene HTML-Vorlage wird robust gegen cwd geladen
   (`Path(__file__).parent`, Zeile 85); die Nutzdaten des Laufs (`index_file`, ein
   Kommandozeilenargument) werden dagegen so verwendet, wie sie übergeben wurden — relativ
   zum cwd, falls der Aufrufer keinen absoluten Pfad angibt.
5. **Ein vorhandener, unabhängiger Beleg für genau das Muster, das R5 verbietet:**
   `organize_runs.py`/`undo_organization.py` rufen `os.chdir()` auf einen hartkodierten,
   auf diesem Fork nicht existierenden Pfad. Diese drei Skripte sind auf diesem Fork **als
   ausgeliefert unbenutzbar** — kein Zusammenhang mit dem geplanten Umbau, aber einer der
   „acht Leser" aus R10, und ein Fund, der unabhängig vom Umbau eine eigene Korrektur
   verdient (s. Bericht).

---

## Nicht ermittelt

- **Das tatsächliche Arbeitsverzeichnis von Gunicorn unter nixpacks/Railway.**
  `nixpacks.toml` benennt kein `WORKDIR`; ob die Build-Plattform es implizit auf das
  Repo-Root setzt (übliche Nixpacks/Railway-Konvention) oder ob es von einer
  Projekteinstellung außerhalb dieses Repos abhängt, wurde nicht geprüft — dazu wäre
  Zugriff auf die tatsächliche Railway-Konfiguration nötig, die nicht Teil dieses Repos
  ist.
- **Ob `instruction_templates.py`/`create_default_library()` irgendwo optional eine
  externe Datei liest** (z. B. ein JSON-Override für Templates). Die Funktion wurde nicht
  vollständig gelesen; aus dem Namen und den übrigen Fundstellen (keine
  `open(...)`-Aufrufe im Grep-Ergebnis für diese Datei) ist die Vermutung, dass Templates
  reine Python-Literale sind, aber das ist eine Vermutung, kein bestätigter Befund.
- **Ob main.py selbst — nicht nur `app.py` nach Subprozessende — an irgendeiner Stelle in
  `performance_tracking.db` schreibt.** Die Konstruktor-Fundstellen wurden geprüft
  (`app.py:854`, `performance_tracker.py:412`), aber nicht jede Aufrufstelle von
  `tracker.ingest_test_run(...)` oder vergleichbaren Methoden wurde zurückverfolgt, um
  auszuschließen, dass die Engine selbst (im gepinnten `cwd`) ebenfalls in dieselbe
  Datenbank schreibt, nur unter einer anderen Pfad-Auflösung — das wäre ein zweites
  Beispiel für Widerspruch 2 oben, aber nicht bestätigt.
- **Vollständige Liste aller `data/output`-Treffer in `app.py`.** Die Tabelle nennt jede
  Zeilennummer aus dem Grep-Lauf, aber nicht jede einzelne wurde bis zur letzten Klammer
  gelesen — bei Routen mit identischem Muster (`Path("data/output") / …`) wurde nach den
  ersten drei bis vier Belegen nicht mehr jede weitere Fundstelle einzeln nachvollzogen,
  sondern als „gleiches Muster" eingeordnet.
- **`tools/codex_ro.py` und die übrige claudex-loop-Werkzeugkette** wurden absichtlich
  nicht einbezogen — sie liegen außerhalb der Web→Motor-Naht, um die es in
  `2026-09-03-engine-naht.md` geht, und ein Blick hinein war für diesen Auftrag nicht
  nötig.
