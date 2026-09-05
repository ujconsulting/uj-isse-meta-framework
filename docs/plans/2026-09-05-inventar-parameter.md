# Inventar: Parameter — Web-Formular → Motor

**Stand:** 05.09.2026 · **Branch:** `fix/honest-failure-reporting` · Vorarbeit zu
`docs/plans/2026-09-03-engine-naht.md` §3b (Schritt 0d). Reine Recherche, kein Code
geändert.

## Methode

Quellen, in dieser Reihenfolge gelesen:

1. `main.py:3009-3054` — vollständiger `parser.add_argument`-Block (alle CLI-Flags).
2. `main.py`, gezielt gegrept auf `args.<flag>` für jedes Flag, dessen Vorgabewert nicht
   trivial aus `add_argument` folgt (`--config`, `--max-combinations`, `--variations`,
   `--domain-config`), um zu sehen, was ein *fehlendes* Argument tatsächlich bewirkt statt
   nur, welchen Wert argparse einträgt.
3. `app.py::_convert_web_params_to_isee` (Zeilen 1034–1229) — vollständig gelesen.
4. `app.py::execute_isee_command` (Zeilen 589–971) — vollständig gelesen, insbesondere der
   Abschnitt, der `cmd = ["python", "main.py"]` befüllt (632–753). Das ist die einzige
   Stelle, an der ein Web-Parameter tatsächlich zu einem CLI-Flag wird — Werte, die es bis
   `converted_params` schaffen, aber hier nicht in `cmd.extend(...)` landen, erreichen den
   Motor **nicht**.
5. `app.py::generate_command_preview` (521–587) und `app.py::api_preview_queries`
   (2028–2079) — zwei weitere, unabhängige Leser von
   `_convert_web_params_to_isee`, mit **eigenen** Fallback-Werten. Gelesen, weil sie
   zeigen, dass „was ein fehlender Wert bedeutet" nicht einmal innerhalb von `app.py`
   einheitlich beantwortet wird.
6. `app.py::_domain_flags` (351–373), `_is_known_domain` (375–391),
   `_process_model_params` (1625–1665) — die Normalisierungsfunktionen, die
   `_convert_web_params_to_isee` aufruft.
7. `isee-ui.html`, der `fetch('/api/execute', …)`-Aufruf (Zeilen 2927–2946) — das
   tatsächliche JSON, das der Browser schickt. Das ist die einzige verlässliche Quelle für
   „was schickt die Oberfläche wirklich", nicht die serverseitige Doku-Erwartung.
8. `cost_estimation.py`, gegrept auf `balanced_models`, `use_ollama`, `dry_run`, weil diese
   drei Felder in `_convert_web_params_to_isee` gesetzt werden, aber in
   `execute_isee_command` nirgends in `cmd.extend(...)` auftauchen — zu klären, ob sie
   irgendwo sonst wirken oder tot sind.

Nicht gelesen: `archive/` (laut `CLAUDE.md` Referenz, nicht Laufzeitpfad),
`.env`/`.env.template` (Tabu-Scope dieser Aufgabe), `data/output/*` (Laufdaten, keine
Parameterquelle).

---

## Tabelle

Spalten: **CLI-Flag** · **Web-Feld** · **Typ** · **Vorgabewert** · **weggelassen vs.
ausdrücklich gesetzt** · **Normalisierung** · **wer besitzt sie**.

„Vorgabewert" nennt zuerst den CLI-seitigen (aus `add_argument` bzw., wo abweichend, aus
dem tatsächlichen Verhalten bei fehlendem Argument), danach — wenn abweichend — den
web-seitigen Fallback aus `_convert_web_params_to_isee`. ⚠️ markiert einen Widerspruch.

| CLI-Flag | Web-Feld | Typ | Vorgabewert | weggelassen / ausdrücklich | Normalisierung | Besitzer |
|---|---|---|---|---|---|---|
| `--config` | kein direktes Feld | Pfad (str) | CLI: `None` (kein Config wird geladen) | Web setzt `--config` nur **innerhalb** des `if selected_models:`-Zweigs (app.py:679-685); ohne Modellauswahl bleibt es weg wie bei der CLI | Web wählt den Dateinamen aus `provider` (`openrouter_config.json` / `globant_enterprise_config.json`), keine Pfadauflösung | App (`execute_isee_command`) |
| `--save-state` | — | Pfad | `None` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--load-state` | — | Pfad | `None` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--domain-config` | — | Pfad | `None` | von der Oberfläche nie gesetzt; keine entsprechende UI-Kontrolle existiert | — | nur CLI |
| `--query` | `query` | str | CLI: `None` (argparse erzwingt nichts; ein leerer Lauf scheitert erst später) | Web validiert `query` als Pflichtfeld **vor** dem Senden (`isee-ui.html:2859`) *und* serverseitig in `_validate_parameters` (app.py:978-979) | keine | geteilt — Web ist strenger als die CLI |
| `--domain` (append) | `selected_domains` (Liste von Namen aus `/api/suggest-domains`) | Liste[str] | CLI: `None` → leer, Engine wählt Domänen selbst | Web: leere `selected_domains`-Liste erzeugt ebenfalls keine `--domain`/`--dynamic-domain`-Flags → gleiches Auto-Wahl-Verhalten | `_is_known_domain`: ID- oder fallunabhängiger Namensabgleich gegen `domain_manager`; bekannt → `--domain`, sonst → `--dynamic-domain`. Genau diese Ladder war am 03.09.2026 defekt (s. Kommentar app.py:1063-1104) — der Fix ist bereits eingecheckt, aber die Stelle bleibt der heikelste Punkt der ganzen Tabelle | App (`_domain_flags`) |
| `--dynamic-domain` (append) | dieselbe `selected_domains`-Liste, Zweig „nicht bekannt" | Liste[str] | CLI: `None` → leer | wie oben | `dynamic:`-Präfix wird abgeschnitten, falls explizit gesetzt | App |
| `--models` | abgeleitet aus `selected_models` / `selected_collection` / `use_strategic_models` | int | **CLI: `2`**; **Web-Fallback (kein Feld gesetzt): `3`** ⚠️ | Web setzt `--models` nur innerhalb des `if selected_models:`-Zweigs von `execute_isee_command` (app.py:671-690) — der abweichende Fallback-Wert 3 (app.py:1211-1213) wird nur für Kostenschätzung/Vorschau gebraucht, nie für den echten Lauf, weil `_validate_parameters` mindestens eine Modellauswahl erzwingt | — | geteilt, Widerspruch praktisch nicht erreichbar |
| `--selected-models` | `selected_models`, oder aufgelöst aus `selected_collection` (`resolve_collection_models`) bzw. `use_strategic_models` (`get_individual_models(strategic_only=True)`) | comma-str | `None` | ausdrücklich, sobald eine der drei Quellen etwas liefert | `_process_model_params`: `provider/model`-Strings werden gegen `openrouter_config.json` aufgelöst (bestehende Config-ID) oder als dynamische ID durchgereicht | App |
| `--use-ollama` | — (kein Feld in `/api/execute`) | bool (`store_true`) | CLI: `False` | `_convert_web_params_to_isee` setzt `converted["use_ollama"]=False` (app.py:1226), aber **kein** `cmd.append("--use-ollama")` existiert — das Feld wirkt nur in `cost_estimation.py:687,713,726,736` (Kostenschätzung), nie im echten Lauf | — | ⚠️ zwei verschiedene Besitzer: Schätzung liest es, Ausführung ignoriert es |
| `--instructions` | abgeleitet aus `len(cognitive_frameworks)` | int | CLI: `3` | wird in `converted_params` berechnet (app.py:1138 bzw. 1180 Default `3`), aber **nie** in `cmd.extend(...)` verwendet — nur `--instruction-templates` erreicht die CLI. `converted["instructions"]` wird ausschließlich von `/api/preview-queries` gelesen (app.py:2071) | — | für die echte Ausführung tot; lebt nur in der Vorschau |
| `--instruction-templates` | `cognitive_frameworks` (Liste von Anzeigenamen) | comma-str | CLI: `None` | Web sendet immer eine Liste — entweder die Auswahl des Nutzers oder, falls die Oberfläche noch nicht gerendert hat, alle elf Frameworks (`ALL_FRAMEWORKS`, isee-ui.html:2917-2921); ein leeres Array würde `converted["instruction_templates"]=None` ergeben und damit den Flag entfallen lassen | `framework_mapping`-Dict Anzeigename → `ins_*`-ID; unbekannter Name fällt unverändert durch (`self.logger.warning`, app.py:1171-1174) und geht als Klartext an die CLI | App |
| `--variations` | `variations` | int | **CLI: `2`**; **Web-interner Fallback bei fehlendem Feld: `0`** ⚠️ | Die aktuelle Oberfläche sendet immer `variations: 2` fest verdrahtet (isee-ui.html:2941) — nicht nutzerkonfigurierbar, obwohl `_validate_parameters` einen Bereich 0–5 vorsieht (app.py:994-1001), als sei ein UI-Feld dafür vorgesehen. **Live-Defekt:** `execute_isee_command` prüft `if converted_params.get("variations"):` (app.py:693) — eine **ausdrücklich** gewünschte `0` ist in Python falsy und wird genauso behandelt wie „nicht gesetzt"; das Flag entfällt, und die CLI verwendet ihren eigenen Default `2` statt der angeforderten `0`. Ein Aufrufer, der bewusst „keine Variationen" will, bekommt sie trotzdem | keine | ⚠️ Widerspruch + eigener Defekt |
| `--max-combinations` | `max_combinations` | int | **CLI: `None`, was downstream „unbegrenzt/erschöpfend" bedeutet** (main.py:2880 zeigt „Unlimited", main.py:3273-3274 setzt bei `--quick` ohne Wert `36`); **Web-interner Fallback bei fehlendem Feld: `30`** (app.py:1220-1221); **`/api/preview-queries` verwendet bei fehlendem Feld nochmals einen dritten Wert: `100`** (app.py:2073) ⚠️⚠️ | Web sendet immer explizit `11` (Testmodus) oder `66` (Vollmodus) (isee-ui.html:2913/2942) | dieselbe Falsy-Falle wie bei `--variations`: `if converted_params.get("max_combinations"):` (app.py:696) würde eine ausdrückliche `0` verwerfen — bei diesem Feld praktisch folgenlos, weil `0` kein sinnvoller Lauf wäre, aber dieselbe Codeform wie beim `variations`-Defekt | drei verschiedene Stellen im selben Modul, drei verschiedene Vorstellungen von „nicht gesetzt" |
| `--output-format` | `output_format` | choices `markdown`/`json` | CLI: `markdown`; Web-Fallback: `converted_params.get("output_format") or "markdown"` — **jetzt identisch**, war es aber nicht immer | Web sendet aktuell immer `"markdown"` (isee-ui.html:2943) | keine | App — der Kommentar app.py:701-712 dokumentiert einen bereits behobenen Fall, in dem beide Seiten sich unterschiedliche Defaults einbildeten (Web nahm `"json"` an und ließ das Flag weg, während die Datei bereits `.json` hieß, obwohl main.py mangels Flag Markdown schrieb) |
| `--output-file` | kein Nutzerfeld — von `execute_isee_command` selbst berechnet | Pfad | CLI: `None` (main.py würde selbst benennen, s. Inventar Pfade) | Web setzt es **immer** ausdrücklich: `run_dir / f"isee_result.{extension}"` (app.py:748-749) | Extension aus `output_format` abgeleitet (`md`/`json`) | App |
| `--output-directory` | kein Nutzerfeld — von `execute_isee_command` selbst berechnet | Pfad | CLI: `None` → `ISEEApplication` erzeugt selbst einen organisierten Pfad `data/output/YYYY-MM/weekX/run_TIMESTAMP` (main.py:500-508) | Web setzt es **immer** ausdrücklich auf einen **eigenen**, flachen Pfad `data/output/run_{timestamp}` mit einem **eigenen**, in `app.py` erzeugten Zeitstempel (app.py:736-737) — nicht dem Zeitstempel, den `ISEEApplication` intern gebildet hätte | keine | ⚠️ App entscheidet abweichend von der CLI-eigenen Logik — Layout-Unterschied, Details im Pfad-Inventar |
| `--simulate` | kein Nutzerfeld | bool | CLI: `False` | App hängt es **automatisch** an, wenn `_detect_apis_with_session_key(...)` keinen nutzbaren API-Key findet (app.py:730-733) — der Nutzer hat dafür keine sichtbare Kontrolle in `/api/execute` | Verfügbarkeitsprüfung über Session-Key + Umgebungsvariablen | App entscheidet, nicht der Nutzer |
| `--dry-run` | `dry_run` (nur intern) | bool | CLI: `False`; `converted_params.setdefault("dry_run", False)` (app.py:1225) | von der Oberfläche nie ausdrücklich gesetzt; das Feld wird von `cost_estimation.py:833,845` gelesen (Kostenschätzung), aber **nie** in `execute_isee_command` zu einem `cmd.append("--dry-run")` — tot für die echte Ausführung | — | Schätzung ja, Ausführung nein |
| `--synthesize-method` | — | choices | CLI: `cluster_based` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--generate-reports` | kein Nutzerfeld | bool | CLI: `False` | Web hängt es **immer unbedingt** an (app.py:715) | — | App erzwingt es |
| `--report-format` | `report_format` | choices | CLI: `markdown` | Web-Mapping existiert (`param_mapping`), aber `/api/execute` sendet dieses Feld aktuell nie im JSON-Body → in `converted_params` fehlt es → `if converted_params.get("report_format") and … != "markdown":` (app.py:722) bleibt aus → CLI-Default `markdown` gilt | — | konsistent durch Weglassen |
| `--export-csv` | kein Nutzerfeld | bool | CLI: `False` | Web hängt es **immer unbedingt** an (app.py:716) | — | App erzwingt es |
| `--no-rank-files` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--analyze-results` | kein Nutzerfeld | bool | CLI: `False` | Web hängt es **immer unbedingt** an (app.py:717) | — | App erzwingt es |
| `--no-visualizations` | `no_visualizations` | bool | CLI: `False` | Web-Mapping existiert, aber `/api/execute` sendet das Feld nie → bleibt weg → CLI-Default `False` (Visualisierungen laufen) | — | konsistent durch Weglassen |
| `--quick` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--full` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--list-domains` | — | bool | CLI: `False` | rein CLI-seitige Introspektion, kein Web-Äquivalent | — | nur CLI |
| `--expert-mode` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--force` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--verbose-queries` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--show-all-queries` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--query-preview-only` | — | bool | CLI: `False` | Die Oberfläche hat eine eigene HTTP-Route `/api/preview-queries` (app.py:2028-2079), die die Vorschau-Logik **im Web-Prozess selbst** nachbaut, statt diesen Flag an einen Unterprozess zu reichen — zwei unabhängige Implementierungen desselben Zwecks | — | architektonisch getrennt, nicht nur „weggelassen" |
| `--enhance-query` | — | bool | CLI: `False` | von der Oberfläche nie gesetzt; die verwandte Funktionalität läuft über `enhancement_info` (s. u.), einen komplett anderen Kanal | — | nur CLI |
| `--json-progress` | kein Nutzerfeld | bool | CLI: `False` | Web hängt es **immer unbedingt** an (app.py:718) — das ist genau der Kanal, den `docs/plans/2026-09-03-engine-naht.md` abschaffen will | — | App erzwingt es |
| `--parallel` | kein Nutzerfeld | bool | CLI: `False` | Web hängt es **immer unbedingt** an (app.py:719) | — | App erzwingt es |
| `--max-workers` | — | int | CLI: `8` | von der Oberfläche nie gesetzt | — | nur CLI |
| `--provider` | `provider` (Radio-Button `openrouter`/`globant`/`hybrid`) | choices | CLI: `openrouter`; Web-Fallback identisch: `converted_params.get("provider", "openrouter")` (app.py:667) | Web sendet es immer ausdrücklich (isee-ui.html:2944) | keine | geteilt, konsistent |

### Web-Felder ohne jedes CLI-Flag

Diese Felder erreichen den Motor nie über argparse — entweder über einen Seitenkanal
(Umgebungsvariable) oder gar nicht:

| Web-Feld | Ziel | Mechanismus |
|---|---|---|
| `session_api_key` (Parameter von `execute_isee_command`, nicht Teil des `/api/execute`-JSON-Bodys, sondern aus der Flask-Session) | `OPENROUTER_API_KEY` | wird in `env` (Kopie von `os.environ`) geschrieben, bevor `subprocess.Popen` startet (app.py:787-789) — main.py liest es wie jede andere Umgebungsvariable |
| `enhancement_info` (`originalQuery`/`enhancementType`/`enhancementRationale`) | `ISEE_ORIGINAL_QUERY` / `ISEE_ENHANCEMENT_TYPE` / `ISEE_ENHANCEMENT_RATIONALE` | ebenfalls über `env`, aber **nicht** direkt — zwischengespeichert in `self.pending_enhancement_info[execution_id]` und erst beim tatsächlichen `Popen`-Aufruf eingemischt (app.py:754-796). main.py liest diese drei Variablen ausdrücklich zurück in `args.original_query` etc. (main.py:3060-3063) — ein echter, funktionierender Seitenkanal, kein totes Feld |
| `use_strategic_models` (bool) | löst sich vollständig in `--selected-models` auf | `get_individual_models(strategic_only=True)` (app.py:1184-1191) |
| `selected_collection` (str) | löst sich vollständig in `--selected-models` auf | `resolve_collection_models(collection_id)` (app.py:1192-1204); `converted["collection_id"]` wird zusätzlich gesetzt, aber **nirgends** in `cmd.extend(...)` gelesen — tot für die Kommandozeile. (Ein Anzeigename für dieselbe Collection wird an anderer Stelle verwendet, aber aus den **unkonvertierten** `self.execution_parameters[execution_id]`, nicht aus `converted_params` — ein zweiter, unabhängiger Pfad für denselben Wert, app.py:856-868) |
| `balanced_models` (bool) | `converted.setdefault("balanced_models", False)` (app.py:1227) | wird von `cost_estimation.py:704` gelesen (beeinflusst die Modellauswahl **der Schätzung**), aber nie ein CLI-Flag — für die echte Ausführung folgenlos |

### CLI-Flags, die kein Web-Pfad je setzt

`--save-state`, `--load-state`, `--domain-config`, `--use-ollama` (als echtes Flag),
`--dry-run` (als echtes Flag), `--synthesize-method`, `--no-rank-files`, `--quick`,
`--full`, `--list-domains`, `--expert-mode`, `--force`, `--verbose-queries`,
`--show-all-queries`, `--query-preview-only`, `--enhance-query`, `--max-workers`.

---

## ⚠️ Gefundene Widersprüche (der eigentliche Zweck dieser Übung)

1. **`--variations`, Falsy-Falle — der wahrscheinlichste Kandidat für einen zweiten
   „Domänenfehler".** `if converted_params.get("variations"):` in `execute_isee_command`
   (app.py:693) behandelt eine ausdrücklich gewünschte `0` genau wie „nicht gesetzt". Wer
   `variations=0` anfordert (keine Query-Variationen), bekommt durch das Weglassen des
   Flags den CLI-Default `2` — das Gegenteil der Anforderung. Die aktuelle Oberfläche
   sendet zwar immer `2` fest verdrahtet und trifft den Fall dadurch nicht, aber die
   Validierung (`app.py:994-999`) akzeptiert ausdrücklich einen Bereich `0`–`5` — der Code
   ist also für einen Aufrufer gebaut, der `0` sinnvoll finden könnte (z. B. ein künftiges
   UI-Feld oder ein API-Client), und würde ihn falsch bedienen.
2. **`--max-combinations`, drei verschiedene Vorgabewerte im selben Modul.** CLI-seitig
   bedeutet „nicht gesetzt" *unbegrenzt/erschöpfend*. Der gemeinsame Konverter
   `_convert_web_params_to_isee` bedeutet damit *30*. Der unabhängige Preview-Endpunkt
   `/api/preview-queries` bedeutet damit *100* (app.py:2073) — dieser dritte Wert ist zwar
   praktisch unerreichbar, weil der Konverter „max_combinations" schon vorher auf `30`
   gesetzt hat, aber er zeigt, dass drei Autor:innen an drei Stellen unabhängig geraten
   haben, ohne dass eine der drei Zahlen mit der CLI übereinstimmt.
3. **`--models`, abweichender Fallback-Default (`3` vs. `2`).** Praktisch unerreichbar,
   weil `_validate_parameters` eine Modellauswahl erzwingt, aber ein struktureller
   Widerspruch, der bei einer künftigen Lockerung der Validierung sofort scharf würde.
4. **`--output-directory`, eigener Zeitstempel statt CLI-Logik.** Die Web-Seite berechnet
   ihren Lauf-Zeitstempel selbst (`datetime.now().strftime(...)`, app.py:736) und erzwingt
   damit einen flachen Pfad `data/output/run_TIMESTAMP`. Ein CLI-Lauf ohne
   `--output-directory` bekommt stattdessen von `ISEEApplication.__init__` einen
   organisierten Pfad `data/output/YYYY-MM/weekX/run_TIMESTAMP` (main.py:500-508) —
   **unterschiedliche Verzeichnis-Layouts je nach Aufrufweg**, nicht nur ein anderer
   Zeitpunkt. Relevant für R10 im Umbauplan (die „acht Leser"): Werkzeuge, die das
   organisierte Layout erwarten (`organize_runs.py`, `extend_weekly_organization.py`),
   sehen Web-Läufe nie in der erwarteten Struktur.
5. **`--use-ollama`, `--dry-run`, `balanced_models` — Schätzung und Ausführung sehen
   unterschiedliche Welten.** Alle drei Felder fließen in `cost_estimation.py` ein und
   beeinflussen, was der Nutzer als Kostenschätzung/Modellvorschau sieht, erreichen aber
   `execute_isee_command`s `cmd`-Aufbau nie. Ein Nutzer könnte also eine Schätzung sehen,
   die auf einer anderen Modellmenge basiert (z. B. mit Ollama-Modellen), als die, die der
   tatsächliche Lauf verwendet — nicht geprüft, ob das aktuell beobachtbar ist, weil die
   Oberfläche derzeit keine UI-Kontrolle für diese drei Felder anbietet, aber der Code-Pfad
   existiert und wäre bei einer Erweiterung der Oberfläche sofort aktiv.
6. **`--instructions` wird berechnet, aber nie gesendet.** Nur `--instruction-templates`
   erreicht die CLI; `--instructions` (die Zählung) bleibt vollständig auf der Web-Seite.
   Ohne Belang für das heutige Verhalten (die CLI leitet die Anzahl aus der
   Template-Liste ab), aber ein weiteres Feld, das durch die Übersetzungsschicht läuft,
   ohne je anzukommen — genau der Umfang, den §3b der `engine-naht`-Planung mit „183
   Zeilen, gut die Hälfte bleibt" meint.

---

## Nicht ermittelt

- **Was main.py tut, wenn `--query` fehlt oder leer ist**, wurde nicht bis zur
  tatsächlichen Fehlermeldung zurückverfolgt (nur, dass argparse es nicht selbst
  verhindert). Relevant nur als Randfall, weil sowohl Browser- als auch
  Server-Validierung ihn heute abfangen.
- **Ob eine Instanz von `_convert_web_params_to_isee` je mit einem `web_params`-Dict
  aufgerufen wird, das `variations` oder `max_combinations` tatsächlich weglässt** (also
  ob die Falsy-Fallen unter #1/#2 oben von einem heute existierenden Aufrufer je ausgelöst
  werden) — die drei bekannten Aufrufer (`/api/execute`, `/api/estimate-cost`,
  `/api/preview-queries`) wurden gelesen, ein vierter könnte über andere Routen existieren,
  die nicht systematisch nach `_convert_web_params_to_isee(` durchsucht wurden (nur die vier
  Fundstellen aus dem ursprünglichen Grep, app.py:488/629/1034/2042, wurden geprüft — das
  deckt vermutlich alle ab, da `def _convert_web_params_to_isee` nur einmal definiert ist,
  aber eine Route, die `parameters` direkt anders zusammensetzt, wurde nicht ausgeschlossen).
- **Der genaue Fehlerpfad, wenn `get_individual_models(strategic_only=True)` eine leere
  Liste liefert** (z. B. weil `llm_collections.json` fehlt oder strategische Modelle nicht
  konfiguriert sind): `converted_params` bekäme dann kein `selected_models`, und
  `execute_isee_command` würde weder `--config` noch `--selected-models` noch `--models`
  setzen — die CLI liefe dann mit ihren eigenen Defaults (`--models 2`, kein `--config`,
  also kein geladenes Modell-Config). Ob dieser Pfad in der Praxis je erreicht wird, wurde
  nicht geprüft (`get_individual_models` selbst wurde nicht gelesen).
- **`command_wizard.py` und der komplette `archive/`-Baum** wurden nicht in diese Tabelle
  aufgenommen — laut `CLAUDE.md` ist `archive/` Referenz, kein Laufzeitpfad, und
  `command_wizard.py` ist ein eigenständiges interaktives CLI-Skript, kein Teil der
  Web→Motor-Naht, um die dieser Plan geht.
