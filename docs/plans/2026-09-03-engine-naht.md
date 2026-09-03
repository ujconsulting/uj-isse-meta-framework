# Plan: die Motor-Naht — Route A #3 und #4

**Stand:** 03.09.2026, Runde 3 · **Branch:** `fix/honest-failure-reporting` · **Basis:** `d1f20d1`

Ziel: `app.py` startet den Motor nicht mehr als Unterprozess und liest dessen stdout,
sondern ruft ihn direkt auf. Damit verschwindet die Übersetzungsschicht
Web-Parameter → Kommandozeile → argparse → Objekte und der Rückweg
Objekte → Text → Parser → Zustand.

> **Runde 3.** Zwei Runden Codex-Kritik eingearbeitet. Codex hatte in **keiner** Runde
> Repo-Zugriff (sein Sandbox wies unter Windows jedes `exec_command` ab), also ist jede
> repo-bezogene Behauptung von mir nachgemessen. Runde 2 hat vier eigene Widersprüche
> aufgedeckt und **einen bestehenden Fehler im Auslieferungsstand** sichtbar gemacht,
> der nichts mit diesem Umbau zu tun hat (§0).

---

## 0. Vorab: der Auslieferungsstand ist heute schon kaputt

Beim Prüfen von Codex' Einwand „`127.0.0.1` schützt eine Gunicorn-Auslieferung nicht"
kam heraus:

```toml
# nixpacks.toml
cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 ... app:app"
```

**Zwei Gunicorn-Worker sind zwei Prozesse.** `execution_status` ist ein Dict im
Arbeitsspeicher **je Prozess**. Ein Lauf, der auf Worker A startet, ist für eine
Statusabfrage unsichtbar, die auf Worker B landet — sie antwortet `not_found`. Das gilt
**heute**, unabhängig von diesem Plan.

Folgen für den Plan, ehrlich benannt statt weggeredet:

- Jede Maßnahme „ein Lauf zur Zeit" oder „Sperre im Arbeitsspeicher" gilt **je Prozess**.
  In der Zweiworker-Auslieferung hält sie nicht.
- `Dockerfile` startet `python app.py`, `nixpacks.toml` startet Gunicorn — zwei
  verschiedene Startwege mit verschiedenem Verhalten. Auch das ist bestehend.

**Die Voraussetzung wird durchgesetzt, nicht nur genannt** *(Runde 3 — Codex hat zu Recht
darauf bestanden: eine Bedingung zu erklären und im selben Atemzug den Stand zu belassen,
der sie verletzt, macht den Plan unsolide)*:

1. `nixpacks.toml` auf `--workers 1` — ein Wort, und es macht die Auslieferung nicht
   schlechter, sondern erstmals stimmig: mit zwei Workern ist die Statusanzeige heute
   schon zufällig.
2. Eine **Betriebssystem-Sperre** auf einer offenen Datei im Ausgabe-Wurzelverzeichnis
   (`msvcrt.locking` unter Windows, `fcntl.flock` sonst), gehalten über die Lebensdauer
   des Prozesses. Eine bloße Markierungsdatei genügt **nicht** — sie überlebt einen
   Absturz und sperrt den Dienst dann dauerhaft aus; „prüfen, dann anlegen" ist zudem
   selbst ein Wettlauf. Eine Handle-Sperre gibt das Betriebssystem beim Prozesstod
   automatisch frei.

   Der Halter bedient alles. **Ein Nicht-Halter lehnt `/api/execute` *und*
   `/api/status/<id>` mit `503` ab** — er darf **nicht** `not_found` antworten. Denn er
   hat den Lauf nur deshalb nicht im Speicher, weil er der falsche Prozess ist; eine
   `not_found`-Antwort wäre eine Lüge über einen laufenden Lauf. Genau dieser Fall wurde
   in Runde 5 gefunden.

   *Prüfung:* zwei Prozesse gleichzeitig starten — der zweite lehnt beide Routen mit
   `503` ab; danach den ersten hart beenden und prüfen, dass der zweite die Sperre
   bekommt (Absturz-Wiederanlauf).

*(Punkt 2 ersetzt eine Fehlannahme aus Runde 3: dort sollte `app.py` „die
Gunicorn-Umgebung auswerten" und bei mehr als einem Worker abbrechen. Runde 4 hält zu
Recht dagegen, dass ein Worker den `--workers`-Wert des Masters gar nicht zuverlässig
kennt — der Test wäre eine Scheinsicherheit gewesen. Eine Sperrdatei fragt nicht nach der
Konfiguration, sondern stellt die Tatsache fest, und sie greift auch dann, wenn jemand
Gunicorn von Hand mit anderen Werten startet.)*

Beides gehört als Schritt 0e in diesen Umbau. Den Mehrworker-Betrieb *korrekt* zu machen,
verlangt geteilten Zustand (Redis, DB) und bleibt ein eigenes Vorhaben — ⚠️ als eigener
Punkt ins Todo-Dokument.

---

## 1. Warum überhaupt

Die Naht hat in zwei Sitzungen **fünf** eigenständige Fehler hervorgebracht, alle
derselben Bauart — Information geht im Textkanal verloren, ohne dass es auffällt:

| Fehler | Ursache in der Naht | belegt |
| --- | --- | --- |
| Live-Ansicht komplett tot | `parallel_execution_start` gegen `execution_start` | `837c01f`, Replay: 0 erfasste Aufrufe |
| Ein Drittel der Ereignisse verschluckt | nebenläufige `print()` verschmelzen | `a3c0f6d`, Replay: 5 von 11 |
| Absturz als „completed" gemeldet | Exitcode 1 heißt zweierlei | `837c01f` |
| Domänen falsch geflaggt | Web-Flag entschied über ein CLI-Argument | `837c01f` |
| Unicode-Verlust über die Pipe | cp1252 auf der Leseseite | `43fc828` |

Umfang der Schicht: `execute_isee_command` 383, `_convert_web_params_to_isee` 183,
`_monitor_subprocess_progress` 102, `extract_progress_events` 33,
`_analyze_execution_error` 42 — **743 Zeilen** Umweg.

---

## 2. Korrektur an der Aufgabenbeschreibung

Das Todo nennt #3 „Kernlogik in ein importierbares Modul extrahieren". **Trifft nicht zu** —
`main.py` ist importierbar, `app.py` importiert daraus. Nicht erreichbar ist die
*Reihenfolge*: `main()` (663 Zeilen), darin `if args.query:` ab 3245 (246 Zeilen), nur
über argparse betretbar. **#3 heißt richtig:** den Ablauf herauslösen, nicht die Klassen.

---

## 3. Schnitt

```python
@dataclass(frozen=True)
class RunRequest:
    query: str
    paths: EnginePaths           # s. R5 — ein Feld reicht nicht
    provider: str = "openrouter"
    ...                          # vollständige Feldtabelle: §3b
    progress: Optional[Callable[[dict], None]] = None

@dataclass
class RunResult:
    status: str                  # completed | completed_with_failures | failed
    run_directory: str
    output_file: Optional[str]
    succeeded: int; failed: int; total: int
    cost: Optional[dict]
    error: Optional[str]         # redigiert, s. R7

class RunAborted(Exception):
    def __init__(self, message: str, exit_code: int = 1): ...

def run_analysis(request: RunRequest) -> RunResult: ...
```

- `main()` baut `RunRequest` aus `args`, übersetzt `RunAborted` an **einer** Stelle in
  `sys.exit`. **CLI-Verhalten unverändert.**
- `app.py` baut dasselbe `RunRequest`, mit `progress=`.

`_apply_progress_event` bleibt unverändert; nur der Erzeuger wechselt. Die 27 Tests
darauf müssen **ohne Anpassung** grün bleiben.

### 3b. Feldtabelle — Pflicht, kein „…"

*(neu in Runde 3 — Codex hat zu Recht bemängelt, dass ein Auslassungszeichen genau dort
steht, wo dieser Naht schon einmal ein Fehler entstanden ist)*

Vor Schritt 1 wird eine Tabelle geschrieben und im Plan abgelegt, eine Zeile je Feld:
**CLI-Flag · Web-Formularfeld · Typ · Vorgabewert · „weggelassen" gegen „ausdrücklich
gesetzt" · Normalisierung · wer sie besitzt.** Erzeugt aus `parser.add_argument` und
`_convert_web_params_to_isee`, damit nichts vergessen wird.

Prüfung: ein Test je Feld, der das aus dem Web-Formular gebaute `RunRequest` gegen das
aus dem bisherigen argv gebaute vergleicht. Genau hier entstand der Domänenfehler.

---

## 3a. Anfechtbare Entscheidungen

1. **Fassade statt Umzug.** Nur `RunRequest`/`RunResult`/`run_analysis` sind neu;
   `ISEEApplication` (2.000 Zeilen) bleibt in `main.py`.
2. **Ein Prozess statt zwei.** Der Unterprozess ist heute auch Isolationsgrenze (R4).
   *Verworfene Alternative:* Prozess behalten, Kanal auf JSON-Lines über eine eigene Pipe —
   behebt die Verschmelzung, nicht die Parameter-Übersetzung.
3. **Fortschritt als unveränderlicher Schnappschuss** (R6, in Runde 3 erneut geändert).
4. **CLI-Verhalten eingefroren**, inklusive Arbeitsverzeichnis-Semantik (R5).
5. **Einprozess-Auslieferung wird vorausgesetzt und festgeschrieben** (§0).
6. **`isee_engine.py` im Wurzelverzeichnis**, wie `main.py`/`app.py`. Preis: eine
   einmalige Meldung des Wurzel-Wächters.

---

## 4. Risiken

### R1 — matplotlib ohne Backend  *(Umfang gemessen)*
`analysis.py:10` importiert pyplot ohne `use("Agg")`. **Gemessen: genau eine
pyplot-Importstelle** außerhalb `archive/`/`tests/` — die Einzeilerlösung genügt.
*Prüfung:* Diagramme aus einem Nicht-Haupt-Thread, vier PNG > 0 Bytes, vor dem Umbau.

### R2 — Prozessbeendigung  *(Umfang gemessen, ein eigener Fund)*
Acht `sys.exit` in `main()`. **Gemessen:** außerhalb nur in eigenständigen Skripten; das
einzige vom Server berührte (`cognitive_diversity_extractor.py`) wird als **Unterprozess**
gestartet. **Eigener Fund:** `run_cost_report.load_run_summary` wirft `SystemExit` aus
einer Bibliotheksfunktion — genau der Fehler, den R2 verbietet. Kommt als Schritt 0c mit.
*Gegenmaßnahme:* `RunAborted`; Übersetzung nur in `main()`.
*Prüfung:* kein `SystemExit` dringt aus `run_analysis`; zusätzlich eine Quelltextprüfung
des Motorpfads auf `sys.exit`/`os._exit`.

### R3 — Ereignisschleife im Thread
*Gegenmaßnahme:* `run_analysis` ist synchron und besitzt seine Schleife; Aufruf aus einem
Thread mit laufender Schleife → `RunAborted`, kein Absturz.
*Prüfung:* ohne Schleife, mit laufender Schleife, zwei gleichzeitige Läufe.

### R4 — Verlust der Prozess-Isolation  *(Endzustand ergänzt)*
Nur `Exception` fangen, `BaseException` weiterreichen.

Codex' Nachschlag in Runde 2 ist berechtigt: eine durchgereichte `BaseException` beendet
den Hintergrund-Thread **still**, und `execution_status` bliebe für immer auf „running"
stehen — dieselbe Krankheit, die diese Sitzung dreimal behandelt hat.
*Gegenmaßnahme:* der Thread-Einstieg bekommt ein `try/finally`, das den Lauf in einen
**Endzustand** setzt und aktive Aufrufe leert, redigiert protokolliert und die
`BaseException` danach **weiterwirft**.
*Ehrlich:* Prozess-Isolation geht verloren und ist durch Ausnahmebehandlung nicht
zurückzugewinnen. Ein Segfault nimmt den Webdienst mit. Das ist der Preis, kein gelöstes
Risiko.
*Prüfung:* erzwungene `Exception` → Dienst antwortet weiter; erzwungene `BaseException` →
wird **nicht** gefangen, Lauf steht trotzdem auf einem Endzustand.

### R5 — Pfadauflösung  *(zweimal verschärft)*
Runde 1 wollte gegen das Modulverzeichnis auflösen — das hätte CLI-Aufrufe aus
Fremdverzeichnissen verändert. Runde 2: ein einzelnes `base_directory` ist **keine**
Pfad-Architektur; Konfiguration, Vorlagen, Ausgabe, Berichte und Hilfs-Unterprozesse
lösen je eigen auf.
*Gegenmaßnahme:* ein `EnginePaths`-Objekt mit **ausdrücklichen** `Path`-Feldern
(`config`, `output_root`, `domain_config`, …), an jede Abhängigkeit durchgereicht. Die
CLI füllt es aus `os.getcwd()` (Verhalten unverändert), der Web-Adapter aus dem
Repo-Wurzelverzeichnis. **`os.chdir` im Motor ist verboten** — prozessglobal und mit
Threads unbrauchbar; ein Test sucht den Aufruf im Motorpfad.
*Vorarbeit:* Inventar aller Pfadquellen, wie die Feldtabelle in §3b.

### R6 — Nebenläufigkeit des Fortschritts  ⚠️ *(in Runde 3 neu gelöst)*
Neu eingeführtes Risiko: parallele Worker schreiben, während `jsonify` in `/api/status`
über dieselben verschachtelten Dicts iteriert → `RuntimeError: dictionary changed size
during iteration`, im Webdienst.

Runde 2 hat die Sperrlösung aus Runde 2 zu Recht zerlegt: eine flache Kopie gibt die
verschachtelten Listen weiterhin frei, Sperr-Lebensdauer und Wiedereintritt waren
undefiniert, und Statusabfragen konnten Worker ausbremsen.

*Gegenmaßnahme:* **unveränderlicher Schnappschuss statt gemeinsamer Struktur.**
`/api/status` liest ein einzelnes Attribut — **ohne Sperre**, weil die Zuweisung in
CPython unteilbar ist und der Schnappschuss danach nie mehr verändert wird. Damit
entfallen Wiedereintritt, Verhungern und die Frage nach der Kopiertiefe zugleich.

Drei Festlegungen, die Runde 3 zu Recht eingefordert hat:

1. **Anwenden, serialisieren und veröffentlichen liegen zusammen unter *einer* Sperre.**
   Sonst: Worker A ändert, Worker B ändert und veröffentlicht, dann veröffentlicht A
   seinen **älteren** Schnappschuss — die Anzeige fällt zurück und bleibt bis zum
   nächsten Ereignis falsch. Ein Klassiker, und er war in Runde 2 nicht ausgeschlossen.
2. **Der Schnappschuss ist JSON-*Text*, nicht ein Dict.** `/api/status` gibt ihn als
   `Response(schnappschuss, mimetype="application/json")` zurück, **nicht** über
   `jsonify` — das würde eine Zeichenkette doppelt kodieren und den Antwortvertrag
   brechen. Ein Test vergleicht die Antwort Feld für Feld mit der heutigen.
3. **Serialisierung kann scheitern** (unerwarteter Wert, `NaN`, Zyklus). Sie läuft im
   Rückruf eines Modell-Workers; eine Ausnahme dort darf weder den Worker töten noch den
   Status einfrieren.

   Runde 3 sah dafür `default=str` vor. **Runde 4 hat das zu Recht verworfen:** das ruft
   ein beliebiges `__str__` auf — unter der Sperre, mit unbekannter Laufzeit, und die
   Zeichenkette eines Konfigurations- oder Client-Objekts kann einen Schlüssel enthalten.
   Ein Redigierschritt, der danach greift, käme zu spät für alles, was er nicht kennt.

   Stattdessen: **festes, enges Schema** für Fortschrittsereignisse (nur `str`, `int`,
   `float`, `bool`, `None`, Listen und Dicts davon), geprüft **an der Rückrufkante**.
   Alles andere wird durch einen Platzhalter mit Typnamen ersetzt — ohne `str()` auf dem
   Objekt. Scheitert es dennoch, wird ein **eigenständig aufgebauter** Minimal-Schnappschuss
   veröffentlicht (Status, Zählstände, Fehlermeldung), der den ursprünglichen Zustand gar
   nicht erst anfasst — Zyklen sind damit ebenfalls erledigt.

*Prüfung:* acht Threads speisen Ereignisse ein, während ein neunter dauerhaft
`/api/status` liest — kein `RuntimeError`, kein Rückfall auf einen älteren Stand
(monoton steigende Folgenummer je Schnappschuss), am Ende stimmt die Zählung; plus ein
Test mit einem nicht serialisierbaren Ereigniswert.

### R7 — Geheimnisse in Ausgabe und Fehlern  *(erweitert)*
Codex hat recht: nur `RunResult.error` zu redigieren, lässt `print`, Rückverfolgungen und
Berichtsfehler ungeschützt, die künftig im Server-Log landen.
*Gegenmaßnahme, in Runde 4 zum zweiten Mal korrigiert:*

Runde 3 verwarf den bloßen `logging`-Filter zu Recht — er sieht `print` und direkt nach
stderr geschriebene Rückverfolgungen nicht. Mein Ersatz war aber schlechter als das
Problem: `contextlib.redirect_stdout` ersetzt `sys.stdout` **prozessweit**, nicht für
einen Thread. In einem Server mit mehreren gleichzeitigen Anfragen würde damit die
Ausgabe **fremder** Threads in die Senke eines laufenden Analyselaufs umgeleitet — und
schreibt die Senke selbst über einen Handler auf stdout, ist die Rekursion fertig. Runde 4
hat das gefunden; der Vorschlag ist gestrichen.

*Stattdessen:* der Motor bekommt eine **injizierte Ausgabesenke** (`emit(text)`) im
`RunRequest`. Die CLI reicht `print` durch — Verhalten unverändert. Der Web-Adapter reicht
einen redigierenden, laufbezogenen Logger durch. Kein globaler Strom wird angefasst.

⚠️ Das verlangt, **jeden** Schreiber auf stdout/stderr im Motorpfad umzustellen — und
das ist mehr als `print(x)`. Runde 5 zählt zu Recht auf: `traceback.print_exc()`,
`print(..., file=sys.stderr)`, `print` mit mehreren Argumenten oder eigenem `end=`, und
Bibliotheken, die von sich aus nach stderr schreiben.

*Vorarbeit, wie die Inventare in §3b und R5:* eine Liste aller stdout/stderr-Schreiber im
Motorpfad, erzeugt aus dem Quelltext, jeder einzeln zugeordnet. Rückverfolgungen werden
über `traceback.format_exc()` in die Senke geschrieben, nicht gedruckt. Bibliotheken, die
sich nicht umstellen lassen, werden benannt statt übergangen — der Redigier-Test kann
sonst nicht bestehen, und ein Test, der nicht bestehen kann, ist schlimmer als keiner.

Diese Arbeit gehört in Schritt 1 und ist ein Grund, warum die Zeilenschätzung in §6 nicht
besser wird.

*Prüfung:* Beispielschlüssel, dreifach — in einem `print` des Motors, in einer
Rückverfolgung und in `RunResult.error`; er darf in keinem der drei Wege auftauchen. Plus
ein Test, dass während eines Laufs die Ausgabe eines **unbeteiligten** Threads unverändert
dort ankommt, wo sie hingehört.

### R8 — Zustand über Läufe  *(Umfang gemessen, Durchsetzung ergänzt)*
**Gemessen:** in `main.py`, `model_api_integration.py`, `provider_manager.py` **kein**
veränderlicher Modulzustand. In `app.py`: `app`, `logger`, `demo`.
Übrig: Zwischenspeicher auf `demo` und Instanzzustand der `ISEEApplication`.
*Gegenmaßnahme:* `run_analysis` erzeugt seine `ISEEApplication` selbst. Auf `demo`
greift der Motor **gar nicht** zu — durchgesetzt, nicht behauptet: der Motor bekommt
`demo` nicht übergeben und importiert `app` nicht (Test auf die Importkante).
*Prüfung:* zwei Läufe nacheinander **und** zwei überlappend; keine Kombination des einen
im anderen.

### R9 — SQLite  *(Umfang gemessen, auf beide Datenbanken erweitert)*
**Gemessen:** beide Schreiber öffnen **je Operation** eine eigene Verbindung; keine liegt
auf `self`. Die `check_same_thread`-Klasse existiert nicht.
Übrig: Andrang. *Gegenmaßnahme:* eine gemeinsame Verbindungsfabrik mit `busy_timeout` für
**beide** Datenbanken (`performance_tracking.db` **und** `enhancement_tracking.db` —
Codex' Einwand, dass ich nur eine behandelt hatte, ist berechtigt).
*Prüfung:* zwei Threads schreiben überlappend in **jede** Datenbank; beide Schreibvorgänge
kommen an. **Nicht** über `/api/execute` (das lässt nur einen Lauf zu — der Widerspruch,
den Codex gefunden hat), sondern direkt gegen Wegwerf-Datenbanken.

### R10 — Lauf-Verzeichnis  *(als bestehend eingeordnet, Grammatik gemessen)*
**Gemessen:** `/api/execute` startet Läufe schon heute in einem `threading.Thread` **ohne
Sperre**, Verzeichnisse tragen Sekundenauflösung — die Kollision besteht bereits.
*Gegenmaßnahme, in Runde 3 geändert:* **Das Suffix kommt nur bei einer Kollision.**

Runde 2 sah ein Suffix für jeden Lauf vor. Runde 3 hält dagegen, dass das den
Verzeichnisnamen für **jeden** Lauf ändert — auch den der CLI, deren Verhalten §3
ausdrücklich einfriert. Der Einwand ist berechtigt, und beide von Codex angebotenen
Auswege (Grammatik behalten *oder* Vertrag ändern) sind schlechter als der dritte:

- Erst `run_JJJJMMTT_HHMMSS` versuchen, `mkdir(exist_ok=False)`.
- Nur wenn das kollidiert: `_<4 Zeichen>` anhängen, in einer **begrenzten Schleife**
  (höchstens 8 Versuche), und zwar **bevor** ein einziger bezahlter Aufruf startet.
- Scheitern alle: `RunAborted` mit klarer Meldung — kein bezahlter Lauf ins Leere.

Damit heißt der Verzeichnisname im Normalfall exakt wie heute; ein Suffix erscheint nur
dort, wo heute **stillschweigend überschrieben** würde.

⚠️ **Einschränkung des CLI-Versprechens, ausdrücklich** *(Runde 4)*: „CLI-Verhalten
unverändert" gilt für den Normalfall. Im Kollisionsfall ändert es sich absichtlich — von
„überschreiben" zu „anderer Name". Das ist eine bewusste Ausnahme zugunsten der
Datensicherheit, keine übersehene Abweichung, und sie wird in der Doku genannt.

Die Suffixform ist trotzdem gegen alle vier vorhandenen Parser durchgerechnet —
`app.py:2931` (`[:13]`), `app.py:2946` (`len >= 19`),
`extend_weekly_organization.py:51` (`split('_')[1]`), `startswith('run_')` — und mit
jedem verträglich. Die Grammatik wird im Plan festgeschrieben.

Plus **ein Lauf zur Zeit je Prozess**, mit der Grenze aus §0.

**Die acht Leser** (Codex' Liste, von mir gegengeprüft; mein Plan sprach von „sieben" und
lag falsch): `app.py`, `reporting.py`, `cognitive_diversity_extractor.py`,
`extract_raw_responses.py`, `read_raw_responses.py`, `organize_runs.py`,
`undo_organization.py`, `launch_cognitive_explorer.py`. Je ein Verträglichkeitstest.

**Abgelehnter Lauf:** `409 Conflict` mit `{"error": "...", "running_execution_id": "..."}`;
Test für zweiten Start, Aufräumen nach Ausnahme und nach Neustart.

### R11 — Reichweite eines HTTP-Aufrufs  *(Anspruch zurückgenommen)*
Nachher teilt eine Anfrage den Adressraum mit dem Dienst.

Codex' Einwand trifft: `app.run(host="127.0.0.1")` ändert **nichts** am Gunicorn-Start aus
`nixpacks.toml`, der ausdrücklich `0.0.0.0` bindet. Der Anspruch wird zurückgenommen:

- Der Standard `127.0.0.1` gilt **nur** für `python app.py` (lokale Entwicklung), mit
  `0.0.0.0` über ausdrückliche Umgebungsvariable. Der Container bleibt wie er ist.
- Für die Auslieferung wird **nicht** behauptet, dieser Umbau mache sie sicherer. Sie ist
  unauthentifiziert und bleibt es. Das gehört in `SECURITY.md` und ins Todo, nicht in eine
  Zeile Beruhigung hier.

⚖️ Authentifizierung bleibt offen und wird als offener Punkt notiert.

---

## 5. Reihenfolge  *(nach Codex' Einwand zur Zwischenlage umgestellt)*

Codex hat zu Recht bemängelt, dass die Schritte 3–4 der Runde 2 den Web-Zustand ändern,
während der alte Unterprozess-Pfad noch läuft — eine halb umgestellte Lage, in der weder
der alte noch der neue Weg vollständig gilt.

Runde 3 hält dagegen, ein einziger Schritt, der Ausführungstopologie, Fortschritts­
veröffentlichung, Endzustände, Kennungen, Zulassung und Redigierung zugleich ändert, sei
im Fehlerfall weder zu diagnostizieren noch teilweise zurückzunehmen.

**Beide Einwände lassen sich versöhnen**, und dabei löst sich die scheinbare
Widersprüchlichkeit auf: Der alte Unterprozess-Pfad schreibt in **dasselbe**
`execution_status`. Schnappschuss, Endzustand, Kennung, Zulassung und Redigierung lassen
sich also **zuerst dort** einbauen und scharf schalten — das ist keine halb umgestellte
Lage, sondern dasselbe Verhalten auf besserer Verrohrung. Erst danach wechselt der
Erzeuger.

| # | Schritt | Prüfung |
| --- | --- | --- |
| 0a | R1: `matplotlib.use("Agg")` | Diagramme aus Nicht-Haupt-Thread |
| 0b | R2-Altlast: `SystemExit` aus `run_cost_report` | vorhandene Tests |
| 0c | R9: Verbindungsfabrik mit `busy_timeout`, beide DB | zwei Threads je DB |
| 0d | Inventare: Feldtabelle (§3b) und Pfadquellen (R5) | Gegenlesen, kein Code |
| 0e | §0: `--workers 1` in `nixpacks.toml`; Betriebssystem-Sperre beim Start | zwei Prozesse: der zweite lehnt `/api/execute` **und** `/api/status` mit `503` ab; nach hartem Ende des ersten bekommt er die Sperre |
| 1 | `RunRequest`/`EnginePaths`/`RunResult`/`RunAborted`/`run_analysis`, **nur** von `main()` benutzt | volle Suite + CLI-Golden-Tests |
| 2 | R2/R3/R5/R8 im Motor | je ein Test |
| 3a | Web-Verrohrung **am alten Pfad**: R6-Schnappschuss, R4-Endzustand, R10-Kennung, Ein-Lauf-Sperre, R7-Senke | Nebenläufigkeitstest + Weblauf über den **alten** Pfad + **Vertragstest**: gleiche Ereignisfolge ⇒ gleiche Statusantwort auf altem und neuem Weg |
| 3b | **Die Umstellung:** `app.py` ruft `run_analysis` statt `Popen` | Weblauf Ende zu Ende **plus** die erst hier scharf werdenden Pfade (s. u.) |
| 4 | Toten Umweg entfernen (Monitor, Textparser, Fehlerdeutung) | Suite + Weblauf |

Schritt 3b ist ein kleiner, klar umrissener Commit: der Erzeuger wechselt. `git revert`
stellt den alten Erzeuger wieder her, ohne die Verrohrung aus 3a zu verlieren.

⚠️ **3b ist trotzdem nicht nur ein Erzeugerwechsel** *(Runde 4, berechtigt)*: die
Ausgabesenke aus R7 und das `try/finally` aus R4 greifen am **direkten** Thread und werden
erst hier überhaupt betreten. 3a kann sie nicht prüfen. Deshalb gehören zu 3b
ausdrücklich: `Exception` und `BaseException` im direkten Thread mit Endzustandsprüfung,
und Protokollausgabe eines unbeteiligten Threads während eines Laufs.

⚠️ Was ein `git revert` **nicht** rückgängig macht: bereits erzeugte Lauf-Verzeichnisse
und die Zeilen in beiden Datenbanken. Die sind additiv und stören nicht — aber der
Vollständigkeit halber benannt, weil „rückbaubar" sonst mehr verspricht als es hält.

---

## 6. Was NICHT wegfällt

Der Originalplan behauptete −48 %; gemessen war der Kern **104 Zeilen größer**.

- Parameter-Abbildung bleibt (Web → `RunRequest`), von 183 Zeilen gut die Hälfte.
- `_apply_progress_event` und Statusverwaltung bleiben.
- `main()` bleibt groß (argparse, CLI-Ausgabe).
- Ausgabelayout unangetastet, acht Leser.
- **Neu hinzu:** Schnappschuss, Sperre, Kennung, Redigier-Filter, Verbindungsfabrik,
  `EnginePaths`, und deren Tests.

Erwartung, erneut nach unten korrigiert: **50–200 Zeilen weniger** netto. Möglich, dass
der Kern am Ende **größer** ist — der Gewinn liegt im Wegfall einer Fehlerklasse, nicht
in der Zeilenzahl. Wird gemessen, nicht geschätzt.

---

## 7. Ausdrücklich außerhalb

- Ausgabelayout flach machen; Globant/Hybrid entfernen; UI-Neugestaltung; Lauf-Archiv
- **Authentifizierung** — durch R11 dringlicher, eigenes Vorhaben
- **Mehrworker-Betrieb korrekt machen** (§0) — verlangt geteilten Zustand, eigenes Vorhaben
- Kosten in der Oberfläche zeigen — hängt an diesem Umbau, kommt danach
- Genauigkeit der Kostenschätzung — eigener Punkt (3.4 im Todo)

**Zurückgenommene Ablehnung** *(Runde 3)*: Ich hatte Provider-Regressionstests als „ohne
Zugangsdaten nicht durchführbar" abgelehnt. Das war zu kurz gedacht — Codex hat recht,
dass sich der **Aufbau der Anfrage** ohne jedes Zugangsdatum prüfen lässt, indem der
Transport gefälscht wird. Genau dieses Muster existiert bereits
(`tests/test_failure_visibility.py::TestOpenRouterPayload` fängt den Payload über einen
gefälschten `requests.post` ab). Also kommen dazu: je ein Test für OpenRouter, Globant und
Hybrid, der prüft, dass Modellformat, Endpunkt, Kopfzeilen und Umschaltverhalten aus dem
`RunRequest` korrekt entstehen. Nur der Netzverkehr bleibt gefälscht.

---

## 8. Abnahme

1. Volle Suite: 141 bestanden, dieselben 9 vorbestehenden Fehlschläge, keine neuen.
2. Die 27 Fortschritts-Tests unverändert grün, **ohne** Anpassung.
3. CLI-Golden-Tests: Exitcode 0, 1, 2, `--help`, Argumentfehler — Ausgabe und Code gegen
   den Stand vor dem Umbau.
4. Weblauf Ende zu Ende, **mit Nachweis echter Aufrufe**: Codex' Einwand, dass eine
   nicht-leere Rohantwort auch aus der Simulation stammen kann, trifft zu. Geprüft wird
   deshalb gegen `cost_report.json` — abgerechnete Token > 0 je Modell — und dass die
   Zahl der abgerechneten Aufrufe der Zahl der Kombinationen entspricht.

   **Budget, ausdrücklich** *(Runde 3, berechtigt)*: der Lauf ist ein Testlauf,
   **11 Aufrufe, ~$0,12**, gemessen an den beiden Läufen vom 03.09.2026 ($0,076 und
   $0,123). Er läuft **einmal je Scheibe**, also höchstens dreimal — Schritt 3a, 3b und
   die Abnahme, zusammen unter **$0,40**. Restguthaben zum Planungszeitpunkt: $17,94.
   Kein Volllauf (66 Aufrufe, ~$0,31) ist für die Abnahme nötig. In der normalen
   Testsuite laufen ausschließlich gefälschte Transporte; der bezahlte Lauf wird von Hand
   ausgelöst, nie automatisch.
5. Ein sichtbarer Fehlschlag: ein Lauf mit einem absichtlich ungültigen Modell muss als
   `completed_with_failures` erscheinen, nicht als Erfolg.
6. R1–R11 je mit eigenem Test, R4 zusätzlich mit dem Negativtest.
7. `409` beim zweiten gleichzeitigen Lauf.
8. Die acht Leser öffnen ein Verzeichnis aus dem Web-Pfad.
9. `git diff --stat` gegen `d1f20d1` — gemessene Zeilenzahl gegen die Schätzung aus §6.
10. `README.md`, `README_DE.md` und `CLAUDE.md` beschreiben den neuen Ausführungsweg;
    `SECURITY.md` nennt den Verlust der Prozess-Isolation.
