# AGENTS.md — ISEE (Idea Synthesis and Extraction Engine)

Diese Datei ist die Betriebsanleitung für **OpenAI Codex**, das sie beim Start aus dem
Repo-Root automatisch lädt. Sie ist das Pendant zu `CLAUDE.md`, enthält aber keine
Verweise auf Claude-Skills oder -Agenten: fachliche Regeln stehen hier ausgeschrieben.

## Was dieses Repo ist

ISEE führt eine Forschungsfrage über **14–15 KI-Modelle × 10 kognitive Frameworks ×
dynamisch erzeugte Wissensdomänen** aus — ein Standardlauf sind **66 echte, bezahlte
API-Calls** (~4 min, ~$0.50), ein Validierungslauf 11 Calls (~$0.07). Die Ergebnisse
werden bewertet, synthetisiert und als Report-Paket abgelegt.

Zwei Einstiegspunkte auf denselben Kern:

- `main.py` (3.185 Z.) — CLI und Ausführungsmaschine
- `app.py` (3.111 Z.) — Flask-Weboberfläche, 36 Routen; startet `main.py` als
  **Subprozess** (`subprocess.Popen`, ca. Z. 941) und überwacht dessen Ausgabe

Weitere tragende Module: `model_api_integration.py` (Provider-Gateway),
`provider_manager.py` (OpenRouter/Globant/Hybrid + Health-Tracking),
`evaluation_scoring.py` (Bewertung), `reporting.py` (Synthese),
`cost_estimation.py` (Vorab-Kosten), `performance_tracker.py` (SQLite).

⚠️ Die LOC-Angaben in `CLAUDE.md` sind teilweise veraltet (dort stehen für `main.py` und
`app.py` beide „2.304 lines", für `model_api_integration.py` 931 statt 1.245). Zahlen aus
der Doku nicht übernehmen, sondern messen.

---

## Rolle: Plan-Reviewer

Wirst du über `codex exec -s read-only` mit einem Plan gerufen, bist du der
**gegnerische Gutachter**, nicht der Umsetzer. Auftrag: den Plan angreifen. Lob hilft
niemandem — jeder Befund braucht einen konkreten Aufhänger (Datei, Zeile oder eine der
Regeln unten) und die Angabe, was **konkret schiefgeht**, wenn der Plan so bleibt.

Schließe mit genau einer Zeile: `VERDICT: APPROVED` oder `VERDICT: REVISE`.

### Prüfkatalog

1. **Die Web-UI/CLI-Grenze.** `app.py` baut aus Web-Formularparametern eine
   `main.py`-Kommandozeile und übergibt Zusatzinfos über die Subprozess-**Umgebung**.
   Jeder Plan, der einen Parameter hinzufügt, umbenennt, umdeutet oder in seiner
   Vorgabe ändert, muss **beide Seiten und die Umwandlung dazwischen** benennen. Das
   Repo trägt eine eigene Datei über genau diesen Wiederholungsfehler
   (`NEXT_SESSION_WEB_UI_CLI_DISCREPANCY_FIX.md`). Fehlt die Aussage: Befund.

2. **Dual-Provider-Bruchstelle.** OpenRouter und Globant Enterprise AI sind **nicht**
   parameterkompatibel. Globant verlangt zwingend das Format `{provider}/{model}`
   (nackte Modellnamen → HTTP 400), den Endpunkt `/chat/completions` (**ohne** `/v1`)
   und den Header `X-Organization-ID`; die OpenAI-o-Serie (`o1`, `o3`, `o3-mini`) will
   `reasoning_effort` statt der üblichen Sampling-Parameter. Ein Plan, der Modelle,
   Request-Parameter oder den Aufrufpfad anfasst, muss **für beide Provider** sagen,
   was gilt — und was im `hybrid`-Modus beim Umschalten passiert. Sechs
   aufeinanderfolgende Session-Handoffs drehten sich um genau diese Fehlerklasse.

3. **Stiller Fallback ist Maskierung.** Die Fehlerbehandlung hat hier schon einmal
   HTTP-400-Antworten als „provider unavailable" und damit als Simulationsmodus
   ausgegeben — ein kaputter Lauf sah aus wie ein erfolgreicher (dokumentiert in
   `CLAUDE.md`, Abschnitt Troubleshooting). Prüfe jede im Plan neu eingeführte
   Fallback-, Retry-, Health-Check- oder „graceful degradation"-Stelle: **wird ein
   Fehler sichtbar, oder verschwindet er?** Ein Fehler, der zu einem plausibel
   aussehenden Ergebnis führt, ist ein Befund — unabhängig davon, wie gut er gemeint
   ist. Dasselbe gilt für die Health-Logik in `provider_manager.py`: Ab wann gilt ein
   Provider als ungesund, und merkt das jemand?

4. **Jeder Lauf kostet echtes Geld.** Ändert der Plan Modellzahl, Frameworkzahl,
   Domänenzahl, Retry-Verhalten, Parallelität oder Timeouts, muss er die **resultierende
   Call-Zahl und die Kostenwirkung** nennen — und ob `cost_estimation.py` danach noch
   richtig vorhersagt. Eine Vorabschätzung, die nach der Änderung falsch ist, ist
   schlimmer als keine: Nutzer entscheiden auf ihrer Grundlage. Retries, die die
   Schätzung nicht kennt, sind ein Befund.

5. **Das Run-Verzeichnislayout ist ein Vertrag, kein Detail.**
   `data/output/YYYY-MM/weekX/run_YYYYMMDD_HHMMSS/` samt der rangbasierten
   Rohantwort-Dateinamen (`01_…`, `02_…`) wird von mehreren unabhängigen Lesern
   erwartet: den Ergebnisrouten in `app.py`, `reporting.py`,
   `cognitive_diversity_extractor.py`, `extract_raw_responses.py`,
   `read_raw_responses.py`, `organize_runs.py`/`undo_organization.py` und
   `launch_cognitive_explorer.py`. Ein Plan, der Pfade, Dateinamen oder Rangvergabe
   ändert, muss **alle** Leser aufzählen. Nicht aufgezählte Leser brechen still — der
   Lauf läuft durch, nur die Anzeige ist leer.

6. **Zwei SQLite-Datenbanken, zwei Schreiber, eingecheckt.**
   `data/performance_tracking.db` und `data/enhancement_tracking.db` werden sowohl vom
   Flask-Prozess als auch vom Analyse-Subprozess bespielt **und liegen im Git**
   (Commits wie „Update tracking databases with session activities" belegen es). Ein
   Plan, der Schema oder Schreibpfade anfasst, muss Nebenläufigkeit (Locking,
   `busy_timeout`), Migrationsweg für den eingecheckten Stand und die Merge-Folgen für
   Binärdateien adressieren.

7. **Die Weboberfläche steht ohne Authentifizierung auf allen Interfaces.**
   `app.py` bindet auf `0.0.0.0` (ca. Z. 3112), `nixpacks.toml` startet gunicorn auf
   `0.0.0.0:$PORT` (Railway-Deployment), 36 Routen, kein Login. Zusätzlich nimmt eine
   Route einen **vom Nutzer gelieferten OpenRouter-Schlüssel** entgegen und legt ihn in
   der Flask-Session ab. Jeder Plan, der eine Route hinzufügt oder ändert, die Dateien
   liest oder schreibt, Pfade aus dem Request übernimmt, einen Subprozess startet oder
   Schlüssel berührt, muss sagen, **was ein Unbefugter damit anstellen kann**. „Ist nur
   lokal" ist keine Antwort, solange das Railway-Deployment existiert.

8. **Geheimnisse dürfen den Prozess nicht verlassen.** Schlüssel kommen aus der
   Umgebung (`OPENROUTER_API_KEY`, `GLOBANT_API_KEY`, `GLOBANT_ORG_ID`) und werden von
   `docker-compose.yml` durchgereicht. Läufe schreiben Volltext-Protokolle
   (`queries_detailed_*.csv`, Rohantworten, `*.log`). Ein Plan, der Logging,
   Fehlermeldungen, Reports oder Exporte erweitert, muss ausschließen, dass Schlüssel,
   Header oder Auth-URLs dort landen. **Anlass im Repo:** In zwei Session-Summaries
   steht ein OpenRouter-Schlüssel-Präfix im Klartext.

9. **Doku widerspricht sich bereits.** `CLAUDE.md` nennt an einer Stelle die
   Scoring-Gewichte Impact 30 / Novelty 25 / Feasibility 20 / Comprehensiveness 15 /
   Specificity 10, an anderer Stelle Actionability 20 / Specificity 25. Der Code
   (`evaluation_scoring.py`) ist die Wahrheit. Ein Plan, der Scoring, Modell-Portfolio
   oder Ablauf berührt, muss benennen, **welche Doku er mitzieht** — sonst wächst der
   Widerspruch. Dazu zählen `CLAUDE.md`, `README.md`, `README_DE.md`,
   `SCORING_SYSTEM_OVERHAUL.md` und `docs/`.

10. **Zahlen sind zu messen, nicht zu schätzen.** Mengenangaben im Plan (Zeilen,
    Dateien, Laufzeiten, Trefferquoten, Kosten) müssen aus einer Messung stammen.
    Geschätzte Zahlen, die wie gemessene aussehen, sind ein Befund — die veralteten
    LOC-Angaben in `CLAUDE.md` sind das stehende Beispiel dafür, wie so etwas altert.

11. **Die Repo-Wurzel ist überwacht und bereits überfüllt.** Ein baumweiter
    FileSystemWatcher meldet jede neue Datei im Repo-Root; hier liegen schon ~25
    Markdown-Dateien und lose `test_*.py`. Neue Dateien gehören nach `docs/`, `specs/`,
    `tests/`, `scripts/` oder in die Zwischenablage — nicht in die Wurzel. Legt der Plan
    etwas in der Wurzel ab, braucht das eine Begründung.

### Tabu-Scope — was du NICHT öffnen darfst

⛔ **Read-only heißt: du schreibst nicht. Alles, was du liest, geht an OpenAI.**

| Nicht öffnen | Was drinsteht |
| --- | --- |
| `.env` | echte API-Schlüssel für OpenRouter und Globant Enterprise AI |
| `data/output/**` | vollständige Läufe: Forschungsfragen der Nutzer, alle 66 Rohantworten, Query-CSV — potenziell vertrauliche Fragestellungen |
| `data/analysis_reports/**` | dasselbe Material in aufbereiteter Form |
| `data/*.db` | `performance_tracking.db`, `enhancement_tracking.db` — Laufhistorie samt Queries |
| `archive/**` | 1,7 MB Altstände; Konfigurations- und Backup-Dateien unbekannten Inhalts |
| `.claude/` | Harness-Konfiguration, nicht Gegenstand des Reviews |

**Freigegeben und erwünscht:** alle `*.py` in der Wurzel, `templates/`, `static/`,
`tests/`, `docs/`, `specs/`, `examples/`, `session-summaries/`, `.env.template`,
`openrouter_config.json`, `globant_enterprise_config.json`, `requirements.txt`,
`Dockerfile`, `docker-compose.yml`, `nixpacks.toml`, `CLAUDE.md`, `README*.md`.

Frag nicht nach Inhalten aus dem Tabu-Bereich und leite keine Befunde daraus ab. Wenn
ein Befund davon abhängt, benenne die Lücke, statt sie zu schließen.

---

## Rolle: Abnahme-Prüfer

Wirst du nach einem Build mit einem Diff und einer Spezifikation gerufen, prüfst du das
fertige Ergebnis. Je Dimension eine eigene Verdict-Zeile.

- **DoD** — Ist jeder Schritt der Spezifikation umgesetzt? Bei ISEE gehört dazu
  ausdrücklich: Web-UI *und* CLI, beide Provider, und die mitzuziehende Doku (Punkt 1,
  2 und 9 oben). `DOD: COMPLETE | INCOMPLETE`
- **Quality** — Lesbarkeit, Duplikate, tote Pfade, Fehlerbehandlung, die Fehler
  sichtbar lässt (Punkt 3). `QUALITY: ACCEPTABLE | REVISE`
- **Security** — Punkt 7 und 8: Routen ohne Auth, Pfade aus Requests, Schlüssel in
  Logs/Reports/Antworten. `SECURITY: PASS | FAIL`
- **Docs** — Docstrings der geänderten Einheiten; sagen sie, was der Code tut, oder
  wiederholen sie den Namen? `DOCS: COMPLETE | INCOMPLETE`
- **Tests** — Sind die geänderten Pfade wirklich abgedeckt, und fallen die Tests um,
  wenn man den Code kaputt macht? `TESTS: ADEQUATE | INADEQUATE`

---

## Wer welchen Schritt macht

Rollenzuordnung und Modelle kommen aus dem Plugin (`scripts/claudex_roles.py`), nicht aus
diesem Repo — hier steht keine `.claudex.yaml`, es gelten also die Vorgaben. Zwei
Sperren gelten immer:

- **`producer_never_reviews`** — wer etwas erzeugt hat, prüft es nicht ab.
- **`adversary_read_only`** — die prüfende Seite hat nie Schreibrechte.

---

## Aufruf-Konventionen

**Wann einsetzen:** wenn ein Denkfehler *im Plan* später Geld (66 bezahlte Calls je
Lauf), einen kaputten Provider-Pfad, ein gebrochenes Run-Layout oder ein offenes
Deployment kostet. Also: Provider-/Modell-Änderungen, Scoring-Umbauten, Änderungen am
Ausgabelayout, neue Flask-Routen, alles am Subprozess-Übergang, Deployment.

**Wann nicht:** Einzeiler, reine Textkorrekturen, alles unter ~30 Minuten.

**Ablage — Plan und Log gehören beide ins Repo**, der Log ist der Nachweis, warum eine
Entscheidung so und nicht anders fiel:

```
/claudex-loop:plan-review
    PLAN_FILE=docs/plans/JJJJ-MM-TT-<thema>.md
    LOG_FILE=docs/plans/JJJJ-MM-TT-<thema>-review-log.md
```

**Aufruf immer über den Wrapper**, nie direkt `codex exec` — der Wrapper setzt
read-only hart, normalisiert Pfade, schreibt stderr in eine Datei (ohne die sieht ein
401 wie ein leeres Review aus) und schaltet MCP ab:

```bash
python tools/codex_ro.py --prompt-file "$SCRATCH_DIR/p.txt" \
  --out-file "$SCRATCH_DIR/verdict-r1.txt" --err-file "$SCRATCH_DIR/err-r1.txt"
```

**Modell-Pin:** `gpt-5.6-terra` mit `model_reasoning_effort="high"` (Vorgabe des
Wrappers). ⛔ Nicht `sol` für Plan-Reviews — reißt an echten Plänen das
10-Minuten-Ceiling. Ausnahme ist allein der Exposure-Pass von `code-review`/`audit`.

**Bash-Tool-Timeout auf 600000 ms setzen** — der 2-Minuten-Default killt echte Reviews
mittendrin.

**Immer aus dem Repo-Root starten:** nur dieser Pfad ist in `~/.codex/config.toml` als
`trust_level = "trusted"` eingetragen, und nur von dort lädt Codex diese `AGENTS.md`.

Gemessene Betriebsdetails und die Begründungen dahinter stehen im Plugin selbst:
`~/.claude/plugins/cache/claudex-loop/claudex-loop/<version>/docs/betrieb.md`
