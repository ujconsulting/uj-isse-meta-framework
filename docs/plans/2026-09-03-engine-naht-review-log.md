# Plan-Review-Log: die Motor-Naht (Route A #3/#4)

Begonnen 03.09.2026. MAX_ROUNDS=5.

- Plan: `docs/plans/2026-09-03-engine-naht.md` (sha256 `0d841576b167429f…`)
- Kritiker: Codex, `gpt-5.6-terra`, reasoning effort `high`, read-only
- Wrapper: `tools/codex_ro.py` 2.3.1 (in dieser Sitzung von 2.3.0 nachgezogen,
  beide Sperren gegengeprüft)
- Tabu-Scope im Prompt wiederholt: `.env*`, `data/output/**`,
  `data/analysis_reports/**`, `data/*.db`, `archive/**`, `.claude/**`

---

## Runde 1 — Codex

⚠️ **Einschränkung dieser Runde, wörtlich aus der Antwort:** Codex konnte *keine* Repo-Datei öffnen. Sein eigener Sandbox wies unter Windows jedes `exec_command` ab — laut stderr sogar `Get-ChildItem -Name` (`rejected: blocked by policy`). Die Kritik beruht also allein auf dem Plantext plus einem Datei-*Listing*, das offenbar im Kontext lag: alle zehn von Codex genannten Dateien und beide Datenbanknamen wurden von mir nachgeprüft und existieren. Aussagen über Datei-*Inhalte* sind damit unbelegt und von mir einzeln zu prüfen, nicht zu übernehmen.

The plan is not ready to implement. It removes a process-isolation boundary without defining the lifecycle, concurrency, and failure contracts required once web requests and analysis share one interpreter.

I could not perform the requested source verification: the read-only command runner rejected even a directory listing. I therefore opened no repository files and did not access any prohibited path. Unopened accessible files include `main.py`, `app.py`, `analysis.py`, `provider_manager.py`, `model_api_integration.py`, `performance_tracker.py`, `cost_estimation.py`, `reporting.py`, all listed output-reader scripts, and all tests. Prohibited paths (`.env*`, `data/output/**`, `data/analysis_reports/**`, `data/*.db`, `archive/**`, `.claude/**`) were not attempted.

- **The “eight `sys.exit()`” claim is not a transitive call-graph audit.** R2 audits only eight exits stated to be in `main()`, but `run_analysis()` will call `run_complete_pipeline()`, reporting, analysis, provider, and cost code; the plan neither inventories their `sys.exit`, `raise SystemExit`, `os._exit`, `print`, nor `stderr` writes. Its proposed tests cover only the plan’s preselected abort reasons, so a callee can still silently kill the Flask worker thread or emit unstructured error output.  
  Fix: require a repository-wide audit of all process termination and stdout/stderr sites reachable from `run_analysis`, replace engine-side termination with typed results/exceptions, and test the complete reachable set.

- **`except BaseException` is actively unsafe and does not solve R4.** It catches `KeyboardInterrupt`, `SystemExit`, and shutdown/control-flow exceptions that Gunicorn/Flask may rely on, then reports an ordinary failed run from a potentially corrupted interpreter. It cannot catch a segfault, native abort, or many forms of process-wide memory exhaustion—the exact hazards R4 claims to mitigate.  
  Fix: catch only expected `Exception` subclasses at the web boundary, re-raise control-flow exceptions, and retain a process/task-worker isolation boundary for untrusted or memory-intensive runs.

- **One unauthenticated HTTP request gains the ability to harm the serving process, not merely its child.** The existing unauthenticated `0.0.0.0` deployment already permits expensive runs; after this change, one request can exhaust the shared worker’s CPU/RAM, poison process-global event-loop/matplotlib state, or crash the worker serving unrelated users. Concurrent requests can now interfere inside the same address space.  
  Fix: add authentication, per-user rate/concurrency limits, and a durable background worker/process boundary before routing HTTP requests into `run_analysis`.

- **R6 considers only instance attributes and ignores module/class/process state.** Creating a new `ISEEApplication` does not reset module globals, class attributes, provider-health caches, logging handlers, executor pools, asyncio-loop policy/state, configuration caches, or Flask-side run registries. The plan provides no inventory, ownership rule, reset policy, or concurrent-run test for any of these.  
  Fix: inventory every mutable module/class global reachable from the engine, make state run-scoped or explicitly synchronized, and test two overlapping as well as two sequential runs.

- **The progress callback has no concurrency contract.** Model work is parallel; callbacks may therefore call `_apply_progress_event` concurrently while HTTP status routes read `execution_status`. A plain nested dict/list update can expose half-written state, lose active-call increments, or throw inside an engine worker and turn progress handling into a run failure.  
  Fix: use a per-run `queue.Queue` with one status-state consumer, or lock every write and return immutable snapshots to readers.

- **R3’s `asyncio.run` simplification is incomplete.** `asyncio.run()` fails when called in a thread that already owns a running loop; “keep the Jupyter special case” is not an ownership model and the proposed test covers only a fresh `threading.Thread`. It does not test concurrent web runs, loop reuse, cancellation, or shutdown.  
  Fix: make the engine’s async boundary explicit—own a dedicated loop/thread or accept an awaited API—and test no-loop, running-loop, concurrent, cancellation, and shutdown cases.

- **R5 contradicts the promise to freeze CLI behavior.** Resolving all engine-relative paths against the module directory changes behavior for any CLI invocation deliberately launched from another working directory, including which `openrouter_config.json`, `globant_enterprise_config.json`, and `data/output` location is selected. The current subprocess’s explicit `cwd` is not equivalent to changing every direct CLI invocation globally.  
  Fix: pass an explicit `base_directory` in `RunRequest`; preserve CLI cwd semantics and have only the web adapter supply the repository root.

- **Provider compatibility is treated as “out of scope” even though this refactor reroutes provider construction.** `RunRequest` must carry every provider-selection and model-normalization input currently supplied by argparse. Without explicit OpenRouter, Globant, and hybrid tests, the direct path can regress Globant’s `{provider}/{model}` requirement, endpoint/header behavior, o-series parameters, or hybrid switching—and may fall into the documented misleading fallback behavior.  
  Fix: specify the provider fields and normalization owner, then regression-test OpenRouter, Globant, and hybrid fallback with failures remaining visible.

- **The two SQLite databases have no shared-process design.** The plan changes Flask and analysis from separate processes into concurrent threads in one process, but says nothing about connection ownership, `check_same_thread`, transaction duration, `busy_timeout`, WAL policy, retries, or reporting lock failures. Existing Flask and analysis writers for `performance_tracking.db` and `enhancement_tracking.db` can now share a connection incorrectly or interleave writes more frequently.  
  Fix: use a per-thread/per-run SQLite connection factory, short transactions, explicit `busy_timeout`/locking policy, and contention tests against disposable test databases.

- **The output-directory contract is asserted rather than protected.** The known consumers are `app.py`, `reporting.py`, `cognitive_diversity_extractor.py`, `extract_raw_responses.py`, `read_raw_responses.py`, `organize_runs.py`, `undo_organization.py`, and `launch_cognitive_explorer.py`. The plan calls this “seven readers,” does not enumerate them, and tests only a web run. Direct concurrent calls also need an atomic unique run-directory allocation; timestamp/rank allocation can otherwise collide and corrupt raw-response ordering.  
  Fix: document every reader and writer, allocate the run directory atomically with a collision-proof run ID, and add compatibility tests for every listed reader.

- **Stdout/stderr remain an unowned shared resource.** Removing the subprocess monitor does not remove prints from the engine; it redirects them into shared Flask/Gunicorn logs, where parallel runs can still interleave and exception text can expose configuration or request details. `RunResult.error` has no redaction or observability contract.  
  Fix: give the engine explicit structured event/log sinks, keep CLI formatting in the CLI adapter, and redact secrets/headers before logs, status APIs, and `RunResult`.

- **R1 is process-global and inadequately scoped.** `matplotlib.use("Agg")` only works reliably before any `pyplot` import in the process; placing it in `analysis.py` is insufficient unless all pyplot imports and import order are inventoried. It also changes plotting behavior for the whole web worker, not only one run.  
  Fix: set the backend once at controlled process startup before all plotting imports, verify all pyplot import sites, and test it in the actual Flask-worker import order.

- **The acceptance criteria do not prove the stated compatibility claim.** “One CLI run” and 27 unchanged progress tests cannot establish identical CLI output, parser validation, help/error exits, all flag combinations, provider modes, or output-layout behavior. The claimed counts (“141”, “9”, “27”, “four PNGs”, and 250–350 lines) are not linked to reproducible measurements.  
  Fix: add golden CLI tests for success and every exit category, parameterized provider/flag tests, and record the commands and measured results in the implementation report.

- **The plan adds `isee_engine.py` at the monitored, already overloaded repository root without the required justification.** It also omits the architecture/operation documentation that must move with a changed web/CLI execution model.  
  Fix: justify the root module placement or use an existing package location, and update the relevant README/operations documentation in the same change.

VERDICT: REVISE

### Claudes Antwort auf Runde 1

Grundsatz: Codex hatte keinen Repo-Zugriff, also ist **jede** repo-bezogene Behauptung
von mir nachgemessen worden, bevor ich sie übernommen oder verworfen habe.

**Angenommen und in den Plan übernommen**

| Befund | Was sich am Plan ändert |
| --- | --- |
| `except BaseException` ist unsicher | R4: nur `Exception` fangen, `BaseException` weiterreichen. Und der Verlust der Prozess-Isolation wird als **nicht gelöstes** Risiko benannt statt als abgedeckt. |
| R5 bricht das CLI-Versprechen | Treffer. Pfade gegen das Modulverzeichnis aufzulösen hätte CLI-Aufrufe aus Fremdverzeichnissen verändert. Jetzt `base_directory` im `RunRequest`; CLI behält `os.getcwd()`. |
| Rückruf ohne Nebenläufigkeitsvertrag | Der schärfste Befund, und ein **neu eingeführtes** Risiko: parallele Worker schreiben, während `jsonify` in `/api/status` über dieselben Dicts iteriert → `RuntimeError: dictionary changed size during iteration` im Webdienst. Neu als R6 mit Sperre, Schnappschuss und Achtthread-Test. |
| Ein HTTP-Aufruf erreicht jetzt den Dienst | Neu als R11. Authentifizierung bleibt ein eigenes Vorhaben, aber zwei billige Maßnahmen kommen in diesen Umbau: Standardbindung auf `127.0.0.1` und ein Lauf zur Zeit. |
| Geheimnisse in Ausgabe und `RunResult.error` | Neu als R7 mit Redigierung und Test. |
| Abnahme belegt die Kompatibilität nicht | §8: Golden-Tests je Exitcode-Kategorie, `--help`, Argumentfehler. |
| Provider-Felder müssen ins `RunRequest` | Übernommen. |
| `isee_engine.py` im überwachten Wurzelverzeichnis | §3a.6: begründet (konsistent zu `main.py`/`app.py`), einmalige Wächter-Meldung bewusst in Kauf genommen. |
| Doku muss mitziehen | In §5 als Teil des Umbaus. |

**Teilweise angenommen, mit Messung begrenzt**

- *Transitiver Audit der Beendigungsstellen (R2):* außerhalb `main()` gibt es `sys.exit`
  nur in eigenständigen Skripten; das einzige, das der Server anfasst
  (`cognitive_diversity_extractor.py`), wird als **Unterprozess** gestartet, nicht
  importiert. Der Pfad ist kürzer als behauptet. **Dabei aber ein eigener Fund:**
  `run_cost_report.load_run_summary` — von mir in dieser Sitzung geschrieben — wirft
  `SystemExit` aus einer Bibliotheksfunktion, genau der Fehler, den R2 verbietet. Kommt
  als Schritt 0c mit.
- *Ereignisschleife (R3):* Vertrag festgeschrieben statt „Sonderfall behalten"; Test um
  laufende Schleife und zwei gleichzeitige Läufe erweitert.
- *Globant/Hybrid-Regression:* Felder übernommen. Echte Regressionstests sind **ohne
  Zugangsdaten nicht möglich** — geprüft wird stattdessen, dass die Eindämmung (Exit 2)
  weiter greift. Als Grenze in §7 benannt statt stillschweigend übergangen.

**Verworfen, mit Beleg**

- *„R6 ignoriert Modul- und Klassenzustand":* gemessen — `main.py`,
  `model_api_integration.py` und `provider_manager.py` haben auf Modulebene **keinen**
  veränderlichen Zustand, nur Konstanten. In `app.py` sind es `app`, `logger`, `demo`.
  Der reale Rest (Zwischenspeicher auf `demo`, Instanzzustand der `ISEEApplication`)
  steht jetzt als R8 im Plan, ohne die behauptete Breite.
- *„Geteilte SQLite-Verbindungen, `check_same_thread`":* gemessen — beide Schreiber
  öffnen **je Operation** eine eigene Verbindung, keine liegt auf `self`. Die Klasse
  existiert nicht. Übrig bleibt der Andrang; dafür `busy_timeout` (R9).
- *„Alle pyplot-Importstellen inventarisieren":* gemessen — es gibt **genau eine**
  (`analysis.py:10`). Die Einzeilerlösung genügt (R1).

**Berichtigt, weil Codex recht hatte und ich falsch lag**

- Der Plan sprach von „sieben Lesern" des Ausgabelayouts. Es sind **acht**; Codex hat sie
  aufgezählt, ich habe alle acht als vorhanden nachgeprüft. Jetzt vollständig in R10.
- Kollision des Lauf-Verzeichnisses: berechtigt — **aber sie besteht schon heute.**
  `/api/execute` startet den Lauf in einem `threading.Thread` ohne Sperre, und das
  Verzeichnis trägt Sekundenauflösung. Als bestehender Mangel eingeordnet und trotzdem
  behoben, statt ihn diesem Umbau anzulasten.

**Schätzung nach unten korrigiert:** 250–350 eingesparte Zeilen → **150–300**, weil
Sperre, eindeutige Kennung, Redigierung und deren Tests Zeilen kosten.

---

## Runde 2 — Codex

(Wieder ohne Repo-Zugriff; Codex sagt das in Zeile 1 selbst und behandelt meine Messungen ausdrücklich als bloße Behauptungen. Richtig so.)

I cannot verify the new measurements without source access, so I treat them as plan assertions. Internally, the revised plan still has material contradictions and gaps.

- **R6’s lock is underspecified and may still race.** “A copy” is not enough for nested `execution_status` data: a shallow copy releases nested dicts/lists to concurrent mutation before `jsonify` iterates them. The plan also does not define lock ownership/lifetime when a run is removed, nor what happens if `_apply_progress_event` re-enters status handling while a non-reentrant lock is held.  
  Fix: use a per-run state object with lifecycle locking and return an immutable deep snapshot (or JSON-serialize under lock); prefer a queue/single status writer after checking reentrancy.

- **R6 can create polling-driven worker starvation.** Eight model workers and repeated `/api/status` calls contend for the same lock; deep copying a large active-call/status structure under that lock makes web polling block progress, while high-rate polling can delay all workers.  
  Fix: make progress ingestion a bounded queue and publish an atomically replaced immutable snapshot, with status reads lock-free.

- **R4 still leaves `BaseException` failures silent in the actual worker-thread topology.** Letting `SystemExit` or `KeyboardInterrupt` escape a background `threading.Thread` does not notify the HTTP client and can leave `execution_status` permanently “running” with active calls never cleared; “not caught” is not a terminal-state protocol.  
  Fix: wrap the thread entry point in `try/finally` that marks the run terminal and clears active state, logs a redacted failure, then re-raises `BaseException`.

- **R11’s binding mitigation does not cover the stated deployment.** Changing Flask’s development bind to `127.0.0.1` does not protect a Railway/Gunicorn deployment configured to bind `0.0.0.0:$PORT`; the plan’s “external not reachable” test can pass locally while production remains unauthenticated and exposed.  
  Fix: update and test every production launcher/deployment configuration, or do not claim R11 mitigates remote exposure without authentication.

- **R10 directly contradicts R9’s proposed test.** Step 4 introduces “one run at a time” with rejection of the second run, yet R9’s verification requires two overlapping runs to write performance data successfully. Both cannot be true through `/api/execute`.  
  Fix: test R9 with an independent legitimate database writer while one run is active, and separately test a second web execution receives a defined rejection response.

- **“One run at a time per server” is not a global lock.** Multiple Gunicorn workers, multiple Railway instances, a restarted worker, or CLI runs can still overlap; they can collide on the directory and contend on SQLite despite the in-memory server lock.  
  Fix: use an interprocess lock with explicit ownership/recovery semantics, or state and enforce a verified single-worker/single-instance deployment assumption.

- **The new random run suffix changes the run-directory contract while R10 says the layout is untouched.** Existing consumers may parse `run_YYYYMMDD_HHMMSS` rather than merely enumerate directories; listing eight readers is not compatibility evidence, and the plan’s acceptance criteria do not run each reader.  
  Fix: define the revised directory-name grammar, update every reader that assumes the old grammar, and add one compatibility test per named reader.

- **R10 does not define the rejected-run API contract.** A second request now changes observable web behavior, but the plan omits its HTTP status, response body, whether an execution ID is allocated, and whether stale status/locks are cleaned after exception or restart.  
  Fix: specify a `409 Conflict`-style response and test duplicate launch, failure, cancellation, and worker-restart cleanup paths.

- **`base_directory` is not, by itself, a path-resolution design.** The engine, reports, provider configuration, templates, auxiliary subprocesses, and `run_cost_report` may each resolve paths differently. Using `os.chdir()` to make the field effective would be process-global and unsafe with Flask threads; not using it leaves relative-path callers unchanged.  
  Fix: inventory every file/subprocess path, pass explicit `Path` values to each dependency, and forbid engine-side `chdir`.

- **R8’s mitigation does not actually protect the `demo` singleton.** Constructing a new `ISEEApplication` does nothing to prove that ranking/domain services do not read or write `demo` caches; “no run accesses it writeably” is an assertion without an enforcement mechanism. The proposed combinations test also does not detect cache contamination in those services.  
  Fix: make those services explicitly per-run or read-only by interface, and test cache identity and contents across overlapping runs.

- **R9 addresses only one of the two tracked SQLite resources.** Per-operation connections eliminate `check_same_thread` but not write locking. The plan sets `busy_timeout` for `performance_tracking.db` while leaving `enhancement_tracking.db` without an equivalent policy or a demonstrated reason it cannot be concurrently written.  
  Fix: centralize connection setup for both databases, set timeout/transaction policy consistently, and test concurrent writes to each database.

- **R7 still leaks through server logs and error paths.** Redacting only `RunResult.error` and `execution_status` does not redact legacy `print`, traceback logging, subprocess stderr, request headers, or report-generation errors now emitted in the web process. A passing example-key test can therefore coexist with a real secret in Gunicorn logs.  
  Fix: install a centralized redacting logging filter before every server/engine handler and test captured logs, status responses, and generated error artifacts.

- **The refactor still lacks a complete web-parameter contract.** `RunRequest` says “all CLI flags” with an ellipsis, but this seam previously produced incorrect domain selection. There is no field-by-field table for defaults, omitted-vs-explicit values, validation, or web-form normalization, and no regression test comparing each web input to the prior argv behavior.  
  Fix: specify and test every form field → `RunRequest` mapping, including defaults, mutually exclusive choices, and provider/model normalization.

- **The acceptance suite can pass while core behavior is broken.** A non-empty raw response and present `cost_report.json` do not prove real provider calls rather than simulation/fallback; unchanged progress tests do not cover callback concurrency; the listed CLI cases do not cover provider modes; and no criterion checks the production bind, second-run rejection, all eight output readers, or estimated-versus-actual cost/call count.  
  Fix: add explicit assertions for visible provider failure, each provider mode’s request construction, second-run API behavior, all output readers, production binding, and cost-estimate accuracy.

- **Step ordering still permits a broken intermediate web state.** Steps 3–4 modify `/api/status`, run IDs, database behavior, and execution admission while `app.py` still starts the old subprocess/monitor path; the plan does not say those old paths use the new lock, identifier, or terminal-state cleanup consistently.  
  Fix: implement compatibility adapters for the old subprocess path before steps 3–4, or move all web-state changes into the same atomic step as the direct-engine switch.

- **Documentation and deployment consequences remain unowned.** The plan changes execution isolation, binding defaults, run admission, directory naming, and failure semantics, but names no operational documentation to update.  
  Fix: include the relevant README/operations/deployment documentation and document the unrecoverable loss of process isolation.

VERDICT: REVISE

### Claudes Antwort auf Runde 2

Runde 2 war die ergiebigere. Sie hat vier Widersprüche gefunden, die **ich** eingebaut
hatte, und einen bestehenden Fehler im Auslieferungsstand freigelegt.

**Der wichtigste Fund kam beim Nachprüfen, nicht aus der Kritik selbst**

Codex' Einwand „`127.0.0.1` schützt eine Gunicorn-Auslieferung nicht" führte zu
`nixpacks.toml`: `gunicorn --bind 0.0.0.0:$PORT --workers 2`. **Zwei Worker sind zwei
Prozesse**, und `execution_status` ist ein Dict je Prozess. Ein Lauf auf Worker A ist für
eine Statusabfrage auf Worker B unsichtbar — sie antwortet `not_found`. Das gilt **heute**
und hat mit diesem Umbau nichts zu tun. Steht jetzt als §0 im Plan, kommt als eigener
Punkt ins Todo-Dokument, und der Plan schreibt die Einprozess-Annahme ausdrücklich fest,
statt sie stillschweigend vorauszusetzen.

**Angenommen — eigene Widersprüche**

| Befund | Was sich ändert |
| --- | --- |
| Flache Kopie unter Sperre genügt nicht; Sperr-Lebensdauer und Wiedereintritt undefiniert; Statusabfragen können Worker ausbremsen | R6 neu gelöst: **unveränderlicher, fertig serialisierter Schnappschuss** in einem Attribut, Lesen **ohne** Sperre. Kopiertiefe, Wiedereintritt und Verhungern entfallen damit zugleich. |
| `BaseException` durchreichen lässt den Lauf für immer auf „running" | R4: `try/finally` am Thread-Einstieg setzt einen **Endzustand**, leert aktive Aufrufe, protokolliert redigiert — und wirft dann weiter. |
| R10 („ein Lauf zur Zeit") widerspricht R9s Test („zwei überlappende Läufe") | Echter Widerspruch von mir. R9 wird jetzt **direkt** gegen Wegwerf-Datenbanken geprüft, nicht über `/api/execute`. |
| Schritte 3–4 ändern Web-Zustand, während der alte Pfad noch läuft | Reihenfolge umgestellt: **alle** Web-Zustandsänderungen liegen im selben Schritt wie die Umstellung. Schritt 3 ist bewusst groß und als Ganzes rückbaubar. |
| `base_directory` ist keine Pfad-Architektur; `chdir` wäre prozessglobal | `EnginePaths` mit ausdrücklichen `Path`-Feldern; `os.chdir` im Motor **verboten**, mit Test. |
| R9 behandelte nur eine der beiden Datenbanken | Verbindungsfabrik für **beide**. |
| R7 redigiert nur `RunResult.error`, nicht Logs und Rückverfolgungen | Zentraler redigierender Log-Filter. |
| `RunRequest` mit „…" genau dort, wo dieser Naht schon ein Fehler entstand | §3b: Pflicht-Feldtabelle vor Schritt 1, ein Test je Feld gegen das bisherige argv-Verhalten. |
| Abnahme beweist keine echten Provideraufrufe | §8.4 prüft jetzt gegen `cost_report.json` (abgerechnete Token > 0, Aufrufzahl = Kombinationszahl) statt gegen „Datei nicht leer". |
| Abgelehnter Lauf ohne API-Vertrag | `409 Conflict` mit definiertem Rumpf, plus Aufräumtests. |
| R8 behauptet statt durchzusetzen | Der Motor bekommt `demo` nicht übergeben und importiert `app` nicht — Test auf die Importkante. |
| Doku und Auslieferung unbesetzt | §8.10: READMEs, `CLAUDE.md`, `SECURITY.md`. |

**Anspruch zurückgenommen**

- R11 behauptete, `127.0.0.1` mindere die Reichweite. Für die **Auslieferung** stimmt das
  nicht — `nixpacks.toml` bindet ausdrücklich `0.0.0.0`. Der Standard gilt jetzt nur für
  `python app.py`, und für die Auslieferung wird ausdrücklich **nicht** behauptet, dieser
  Umbau mache sie sicherer.

**Verworfen, mit Beleg**

- *„Das Zufallssuffix bricht die Namensgrammatik":* an allen vier vorhandenen Parsern
  durchgerechnet — `app.py:2931` (`[:13]`), `app.py:2946` (`len >= 19`),
  `extend_weekly_organization.py:51` (`split('_')[1]`) und `startswith('run_')` vertragen
  `run_JJJJMMTT_HHMMSS_xxxx` sämtlich. Die Grammatik wird trotzdem festgeschrieben und die
  acht Leser bekommen je einen Test.
- *Interprozess-Sperre:* verworfen zugunsten der ausdrücklichen Einprozess-Annahme plus
  `mkdir(exist_ok=False)` als tatsächlicher prozessübergreifender Schutz des
  Verzeichnisses. Eine Interprozess-Sperre ohne geteilten Zustand für `execution_status`
  löst nur die halbe Sache und täuscht Sicherheit vor.
- *Vollständige Provider-Regression und Genauigkeit der Kostenschätzung:* außerhalb, mit
  Begründung in §7.

**Schätzung erneut nach unten:** 150–300 → **50–200 Zeilen**, mit der ausdrücklichen
Möglichkeit, dass der Kern am Ende größer ist. Der Gewinn liegt im Wegfall einer
Fehlerklasse, nicht in der Zeilenzahl.

---

## Runde 3 — Codex

I cannot independently verify the cited measurements. On the plan’s own terms, it is still not sound enough to start: its declared deployment prerequisite is contradicted by the current deployment it knowingly leaves in place.

- **Section 0 documents a violated prerequisite, then defers it.** The plan requires a single-process deployment, while `nixpacks.toml` is stated to launch two Gunicorn workers. Step 3 will therefore deploy with per-process execution IDs, snapshots, admission locks, and terminal states that are still unreliable; calling this pre-existing does not make the refactor safe under the configured production command.  
  Fix: make single-worker deployment a precondition implemented in this change, or hard-fail startup when more than one worker is configured.

- **R6’s snapshot is safe only if serialization and publication occur while holding the state lock.** If a worker updates state, another worker publishes a newer snapshot, and the first subsequently publishes its older serialized snapshot, `/api/status` can regress permanently until another event arrives. The plan does not state the required lock scope.  
  Fix: under one lock, apply the event, serialize the complete state, and publish the resulting immutable snapshot before releasing the lock.

- **“Already serialized” has an unhandled failure path.** JSON serialization can fail on an unexpected event value, non-finite number, recursive structure, or future event-schema change; that exception occurs in a model worker callback and can lose progress or leave the run’s public status stale.  
  Fix: define a JSON-safe progress-event schema, validate at the callback boundary, and make serialization failure produce a visible terminal diagnostic without killing the engine worker.

- **A serialized snapshot still needs a response contract.** If the attribute contains JSON text, `jsonify(snapshot)` returns a JSON string rather than the existing status object; parsing it before `jsonify` is safe locally but must preserve the former response schema and HTTP content type. The plan does not specify either.  
  Fix: specify the snapshot’s representation and add contract tests asserting byte-level/status-schema compatibility for `/api/status/<id>`.

- **R7’s logging mitigation does not handle `print` or direct stderr.** A Python logging filter applies to logging handlers, not existing `print()`, tracebacks written directly to stderr, or subprocess output inherited by Gunicorn. The plan correctly identifies those sources, then proposes a control that does not intercept all of them.  
  Fix: route engine output through an explicit redacting logger/output sink and capture or eliminate direct stdout/stderr writes on the web path.

- **R10 changes CLI-visible output naming while Section 3 promises frozen CLI behavior.** The common engine will now create `run_YYYYMMDD_HHMMSS_xxxx` instead of the prior directory name. Even if the four measured parsers accept it, that is an output-layout and CLI-observable behavior change, not “unchanged CLI behavior.”  
  Fix: either preserve the legacy CLI directory grammar or explicitly change the CLI contract, documentation, and golden filesystem expectations.

- **`mkdir(exist_ok=False)` detects a collision but does not guarantee a unique run.** A suffix collision now becomes a failed paid run unless the plan defines bounded regeneration, error reporting, and cleanup; the stated “one run per process” also does not cover the known two-process deployment or CLI processes.  
  Fix: atomically reserve a generated ID in a bounded retry loop and report an allocation failure before any paid provider work begins.

- **Step 3 is too broad to call safely reversible merely because it is one commit.** It simultaneously changes execution topology, progress publication, terminal-state semantics, run IDs, admission behavior, and redaction. A production failure cannot be diagnosed or selectively rolled back, and live runs/files created under the new contract are not reverted by `git revert`.  
  Fix: first introduce and test compatibility adapters for snapshot status, admission, IDs, and redaction on the old subprocess path; make the direct-engine call the isolated final switch.

- **The plan still changes a provider/request seam without validating both provider contracts.** `RunRequest` and the web-to-engine mapping now own provider inputs, yet Globant and hybrid paths are excluded from regression testing. “Exit 2 without credentials” cannot validate provider/model formatting, endpoint selection, organization headers, or hybrid switching.  
  Fix: add credential-free request-construction tests with mocked transports for OpenRouter, Globant, and hybrid fallback.

- **The live acceptance run has unbudgeted real-cost implications.** Section 8 requires real calls and token-bearing cost reports, but does not state the call count, estimated spend, retry limit, or how the test avoids accidentally running the full paid matrix repeatedly.  
  Fix: state the exact expected calls/cost and gate live verification behind an explicit opt-in, with mocked coverage for normal CI.

VERDICT: REVISE

### Claudes Antwort auf Runde 3

Diesmal fast durchgehend angenommen — die Befunde waren Korrektheitsfragen, keine
Vollständigkeitswünsche, und zwei davon waren Widersprüche in meinem eigenen Text.

**Angenommen**

| Befund | Was sich ändert |
| --- | --- |
| §0 nennt eine Voraussetzung und lässt den Stand, der sie verletzt | Berechtigt. `nixpacks.toml` geht auf `--workers 1`, und `app.py` bricht beim Start ab, wenn mehr konfiguriert sind. Als Schritt 0e **in** diesen Umbau, nicht daneben. |
| Schnappschuss muss **unter derselben Sperre** serialisiert und veröffentlicht werden | Echte Lücke. Sonst überholt ein jüngerer Schnappschuss einen älteren und die Anzeige fällt zurück. Jetzt ausdrücklich festgelegt, plus monoton steigende Folgenummer als Prüfmittel. |
| „Fertig serialisiert" hat einen ungenannten Fehlerpfad | Richtig — die Serialisierung läuft im Rückruf eines Modell-Workers. Jetzt `default=str`, Auffanglinie, und im Fehlerfall ein Schnappschuss, der den Fehler **meldet**, statt den alten stehenzulassen. |
| JSON-Text plus `jsonify` = doppelte Kodierung | Guter Fang. `/api/status` gibt jetzt `Response(..., mimetype="application/json")` zurück, mit Feld-für-Feld-Vergleich gegen die heutige Antwort. |
| Ein `logging`-Filter sieht `print` und stderr nicht | Stimmt. Der Web-Pfad führt den Motor zusätzlich unter `redirect_stdout`/`redirect_stderr` in eine redigierende Senke; die CLI bleibt unberührt. |
| Suffix für jeden Lauf ändert auch den CLI-Verzeichnisnamen | Widerspruch zu §3, von mir eingebaut. Gelöst besser als beide angebotenen Auswege: **Suffix nur bei Kollision**, begrenzte Schleife, **vor** dem ersten bezahlten Aufruf. Im Normalfall heißt das Verzeichnis exakt wie heute; ein Suffix erscheint nur, wo heute stillschweigend überschrieben würde. |
| `mkdir(exist_ok=False)` erkennt, garantiert aber nicht | Mit der begrenzten Schleife und `RunAborted` vor dem ersten bezahlten Aufruf erledigt. |
| Schritt 3 zu breit für „rückbaubar, weil ein Commit" | Angenommen — und der scheinbare Widerspruch zu Runde 2 löst sich auf: der **alte** Pfad schreibt in dasselbe `execution_status`, die neue Verrohrung lässt sich also zuerst dort scharf schalten (3a), dann wechselt allein der Erzeuger (3b). Keine halbe Lage, und ein kleiner, eindeutiger Umschalt-Commit. |
| Bezahlter Abnahmelauf ohne Budget | Jetzt beziffert: 11 Aufrufe, ~$0,12, höchstens dreimal, zusammen unter $0,40. Testsuite fälscht durchgehend den Transport; der bezahlte Lauf wird von Hand ausgelöst. |

**Zurückgenommene Ablehnung**

Ich hatte Provider-Regressionstests als „ohne Zugangsdaten nicht durchführbar" verworfen.
Zu kurz gedacht: der **Aufbau der Anfrage** ist ohne jedes Zugangsdatum prüfbar, wenn man
den Transport fälscht — genau dieses Muster steht schon in
`tests/test_failure_visibility.py::TestOpenRouterPayload`. Kommt für OpenRouter, Globant
und Hybrid dazu.

**Nicht angenommen**

- *Interprozess-Sperre statt Einprozess-Annahme:* bleibt verworfen, jetzt aber mit
  besserem Grund — mit `--workers 1` und Startabbruch (0e) ist die Annahme **durchgesetzt**
  statt nur erklärt. Eine Interprozess-Sperre löste ohnehin nur die halbe Sache, solange
  `execution_status` prozesslokal ist.

---

## Runde 4 — Codex

I cannot independently verify the cited repository measurements. On the plan’s stated design, two points remain correctness defects; the collision and 3a/3b structure are otherwise materially improved.

- **R7’s `redirect_stdout`/`redirect_stderr` is unsafe in a threaded Flask/Gunicorn process.** Those context managers replace `sys.stdout` and `sys.stderr` process-wide, not for only the run thread. While a run is active, unrelated request threads and Gunicorn/framework logging can be diverted into the redacting sink; if that sink logs through a handler targeting stdout, it can recurse or deadlock.  
  Fix: remove global stream redirection from the web path and refactor engine output to an injected, redacting per-run writer/logger.

- **R6’s `default=str` is not a safe serialization fallback for a public status API.** It invokes arbitrary `__str__` implementations while holding the progress lock, can block or raise, and can turn opaque objects into secret-bearing strings before the snapshot is published. It also does not solve circular references; the fallback must avoid serializing the original state.  
  Fix: define a strict JSON-safe progress schema, reject/replace unsupported values without calling arbitrary `str`, and publish a minimal independently serializable diagnostic snapshot on failure.

- **The claimed application-level multi-worker enforcement is not specified in a way `app.py` can reliably implement.** A Gunicorn worker normally does not know the master’s effective `--workers` value; inspecting an unspecified “Gunicorn environment” can be absent or stale and would create false assurance. Updating `nixpacks.toml` to one worker is useful, but does not make the proposed startup hard-fail real.  
  Fix: enforce worker count in the Gunicorn/deployment configuration itself and add an integration test launching Gunicorn with two workers to prove the deployment is rejected or prevented.

- **Step 3b is not merely a producer swap.** R7’s direct-run stream handling and R4’s direct-thread `try/finally` only execute after `Popen` is removed; 3a can validate the old monitor’s terminal handling but cannot validate those direct-thread behaviors. Calling 3b isolated is accurate only after its tests explicitly exercise those newly activated paths.  
  Fix: make 3b’s required tests include direct-thread `Exception` and `BaseException` terminal-state behavior plus concurrent unrelated logging during a run.

- **The collision-only suffix prevents two successful runs from sharing a directory, assuming local atomic `mkdir` semantics.** That part is sound: the first atomic create wins and a colliding caller retries with a distinct name before paid work. It does, however, intentionally change the rare CLI collision case from overwrite to suffix, so “CLI behavior unchanged” must be qualified to normal non-collision runs.  
  Fix: state this as an intentional collision-safety exception to frozen CLI behavior and include a concurrent CLI/allocation test.

- **The 3a/3b split does remove the earlier half-migrated state in principle.** Installing snapshots, IDs, admission, and status cleanup on the old producer first is a valid compatibility migration, provided the old-path tests establish the same response contract before 3b. This is a coverage requirement, not an inherent design error.  
  Fix: require a 3a contract test proving old-path and direct-path status payloads are identical for the same scripted event sequence.

VERDICT: REVISE

### Claudes Antwort auf Runde 4

Alle sechs Punkte angenommen. Die beiden als Korrektheitsfehler bezeichneten waren beide
meine, und der erste war schlimmer als das Problem, das er lösen sollte.

| Befund | Was sich ändert |
| --- | --- |
| `redirect_stdout` ist prozessweit, nicht threadlokal | **Der schwerwiegendste Fund dieser Runde.** Mein Vorschlag aus Runde 3 hätte während eines Laufs die Ausgabe *fremder* Anfrage-Threads in die Senke des Laufs umgeleitet — und bei einem Handler auf stdout eine Rekursion erzeugt. Gestrichen. Stattdessen eine **injizierte Ausgabesenke** im `RunRequest`: die CLI reicht `print` durch, der Web-Adapter einen redigierenden laufbezogenen Logger. Kein globaler Strom wird angefasst. Kostet Arbeit (alle `print` im Motorpfad umstellen) — jetzt in §6 als Grund benannt, warum die Zeilenbilanz nicht besser wird. |
| `default=str` ruft beliebiges `__str__` unter der Sperre auf und kann Geheimnisse erzeugen | Angenommen. Jetzt ein **enges Schema** an der Rückrufkante (nur JSON-eigene Typen), Platzhalter mit Typnamen statt `str()` auf dem Objekt, und im Fehlerfall ein **eigenständig aufgebauter** Minimal-Schnappschuss, der den Originalzustand nicht anfasst — womit Zyklen ebenfalls erledigt sind. |
| Ein Gunicorn-Worker kennt `--workers` des Masters nicht zuverlässig | Berechtigt: mein „Startabbruch bei mehr als einem Worker" wäre Scheinsicherheit gewesen. Ersetzt durch eine **Sperrdatei** im Ausgabe-Wurzelverzeichnis — wer sie nicht bekommt, nimmt keine Läufe an (`503`), bedient aber lesende Routen. Das fragt nicht nach Konfiguration, sondern stellt eine Tatsache fest, und greift auch bei handgestartetem Gunicorn. |
| 3b ist nicht nur ein Erzeugerwechsel | Stimmt: Ausgabesenke und `try/finally` greifen am **direkten** Thread und werden erst dort betreten; 3a kann sie nicht prüfen. Die entsprechenden Tests sind jetzt ausdrücklich 3b zugeordnet. |
| „CLI unverändert" muss für den Kollisionsfall eingeschränkt werden | Angenommen und als **bewusste** Ausnahme ausgewiesen: von „überschreiben" zu „anderer Name". |
| 3a/3b braucht einen Vertragstest | Angenommen: gleiche Ereignisfolge ⇒ gleiche Statusantwort auf altem und neuem Weg. |

---

## Runde 5 — Codex (letzte Runde, MAX_ROUNDS)

Two correctness defects remain.

- **The startup lock does not make multi-worker operation safe.** With two Gunicorn workers, only the lock holder accepts `/api/execute`, but a later `/api/status/<id>` can still land on a non-holder, which “continues to serve read routes” and has no in-memory status. The plan therefore still returns `not_found` for active runs in the hand-started multi-worker case it claims to cover.  
  Fix: require single-worker deployment for all supported starts, or have non-owner workers reject/route execution-status requests rather than serve misleading reads.

- **Section 0 and step 0e contradict each other.** Section 0 replaces “abort when more than one worker” with lock-file admission and `503`, yet the sequence still says “Startabbruch bei mehr” and tests that starting with two workers aborts. Implementers cannot satisfy both.  
  Fix: replace step 0e and its test with the lock-holder/non-holder behavior, including status-route behavior, or restore an actual deployment-level multi-worker rejection.

- **A lock file needs a crash-safe locking protocol, not merely a file.** A created marker file can survive a crash or deployment restart and permanently cause `503`; a check-then-create implementation also races.  
  Fix: specify an OS-backed nonblocking advisory lock held by an open handle and automatically released on process death, with an integration test for crash/restart recovery.

- **R7’s injected `emit(text)` does not automatically protect traceback output.** Converting `print()` calls is insufficient for `traceback.print_exc`, libraries writing to stderr, or print calls using `file=`, `end=`, and multiple arguments; the promised traceback-redaction test cannot pass unless those sites are also converted.  
  Fix: inventory every engine-path stdout/stderr writer and route each through a defined output interface, including traceback formatting with `file=` directed to the redacting sink.

The R6 publication design is sound for one process if validation, serialization, sequence assignment, and publication truly occur under the same lock. The collision-only `mkdir(exist_ok=False)` retry design also prevents two successful runs from sharing a directory under normal local filesystem atomicity. The 3a/3b split is now a valid migration strategy; it no longer creates the prior half-migrated state.

VERDICT: REVISE

### Claudes Antwort auf Runde 5

Alle vier Punkte angenommen; einer war ein Widerspruch, den ich beim Umschreiben selbst
stehengelassen hatte.

| Befund | Was sich ändert |
| --- | --- |
| §0 und Schritt 0e widersprechen sich | Meiner. Ich hatte in §0 den „Startabbruch" durch die Sperrdatei ersetzt, in der Schritt-Tabelle aber „Startabbruch bei mehr" stehenlassen. 0e ist jetzt auf das Sperrverhalten umgeschrieben. |
| Ein Nicht-Halter antwortet `not_found` auf einen laufenden Lauf | Guter Fang: die Sperre verhinderte nur den zweiten *Lauf*, nicht die irreführende *Auskunft*. Ein Nicht-Halter lehnt jetzt `/api/execute` **und** `/api/status` mit `503` ab — er hat den Lauf nicht im Speicher, weil er der falsche Prozess ist, nicht weil es ihn nicht gibt. |
| Eine Markierungsdatei ist nicht absturzsicher | Angenommen. Jetzt eine **Betriebssystem-Sperre** auf einem offenen Handle (`msvcrt.locking` / `fcntl.flock`), die das Betriebssystem beim Prozesstod freigibt, plus Wiederanlauftest nach hartem Ende. |
| `emit()` deckt Rückverfolgungen und `file=`-Ausgaben nicht ab | Angenommen. Inventar aller stdout/stderr-Schreiber im Motorpfad als Vorarbeit; `traceback.format_exc()` statt `print_exc()`; nicht umstellbare Bibliotheken werden **benannt**, weil der Redigier-Test sonst nicht bestehen kann — und ein Test, der nicht bestehen kann, ist schlimmer als keiner. |

**Von Codex ausdrücklich als solide bestätigt** (Runde 5, Absatz vor dem Verdikt): die
Veröffentlichungslogik aus R6 für einen Prozess, der Kollisionsschutz mit
`mkdir(exist_ok=False)` und Wiederholungsschleife, und die 3a/3b-Teilung als gültige
Migrationsstrategie ohne halb umgestellte Zwischenlage.

---

## Abschluss: MAX_ROUNDS erreicht, **kein** APPROVED

Der Ablauf endet nach fünf Runden auf `VERDICT: REVISE`. Das wird hier **nicht** als
Zustimmung ausgegeben.

**Ehrliche Einordnung:** Es ist keine Pattsituation im eigentlichen Sinn — ich habe jeden
Befund der Runde 5 angenommen und eingearbeitet. Aber: **die eingearbeitete Fassung wurde
nie erneut geprüft.** Ob die vier Korrekturen tragen, ist ungeprüfte Behauptung von mir.

**Restrisiko, das größte zuerst:**

1. ⚠️ **Codex hat in keiner der fünf Runden eine einzige Repo-Datei gelesen.** Sein
   Sandbox wies unter Windows jedes `exec_command` ab. Die gesamte Prüfung beruht auf dem
   Plantext. Ein Quervergleich am *Code* hat nie stattgefunden — die Kernaufgabe des
   Verfahrens ist also ausgefallen, und die Befunde sind gut, weil sie aus der Struktur
   des Plans folgen, nicht weil jemand den Code geprüft hat.
2. Alle repo-bezogenen Aussagen im Plan stammen aus **meinen eigenen** Messungen. Sie sind
   im Plan mit Datei und Zeile belegt, aber niemand hat sie unabhängig nachgerechnet.
3. Nicht geöffnete Dateien: **alle.** Namentlich für diesen Umbau bedeutsam: `main.py`,
   `app.py`, `analysis.py`, `provider_manager.py`, `model_api_integration.py`,
   `performance_tracker.py`, `enhancement_tracking.py`, `reporting.py`,
   `cost_estimation.py`, die acht Ausgabe-Leser und sämtliche Tests.
4. Die vier Korrekturen aus Runde 5 sind ungeprüft.

**Empfehlung:** umsetzbar, aber die Umsetzung ersetzt die fehlende Codeprüfung nicht.
Nach Schritt 1 und nach Schritt 3b lohnt je ein `/claudex-loop`-Durchgang **am Diff** —
dort ist Codex' Sandbox nicht im Weg, weil der Diff im Prompt steht.
