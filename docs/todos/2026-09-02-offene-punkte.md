# Offene Punkte — Stand 02.09.2026

Aufgenommen am Ende der Sitzung, in der ISEE von „läuft gar nicht" auf „läuft, CLI und
Web" gebracht wurde (Commits `8137f49` bis `759b8ea`). Was hier steht, ist **nicht**
erledigt. Was erledigt ist, steht in den Commit-Nachrichten und in
`session-summaries/SESSION-SUMMARY-2026-09-02-01.md`.

Reihenfolge = grobe Priorität, nicht Aufwand.

> **Nachtrag 03.09.2026** — Route A, Punkt 1 ist erledigt (`837c01f`), fiel dabei aber
> deutlich größer aus als hier beschrieben, und die Beschreibung selbst war teilweise
> falsch. Einzelheiten am Tabelleneintrag.
>
> Anschließend 2.5 bis 2.9 (`a3c0f6d`) — fünf Funde derselben Sitzung, alle beim
> **Ausführen** entstanden, nicht beim Lesen: verlorene Rohantworten, ein Drittel
> verschluckter Fortschrittsereignisse, unbegrenzte Aufrufe, ignorierte
> Wiederholbarkeits-Auskunft, sechs unerreichbare Modelle. Offen bleibt davon nur die
> Anzeige der Kosten in der Oberfläche (2.6), bewusst hinter Route A #4 gestellt.
>
> **Muster, das sich durchzieht:** Fast jeder dieser Fehler war *unsichtbar* — die
> Oberfläche meldete Erfolg, das Log schwieg oder protokollierte auf Debug-Ebene, und die
> Dateien waren da, nur leer. Nichts davon wäre durch Codelesen aufgefallen.
>
> **Nachtrag 05.09.2026** — die Audit-Nacharbeit aus `docs/audit/2026-09-03-baseline.md`
> (Commits `d795033` bis `c47361c`): drei der fünf „zuerst"-Punkte des Audits sind behoben
> (falsche Gewinner-Zuordnung, Bewertungsfehler ⇒ 0.0, CSV-Formelinjektion), zwei bleiben
> offen (die Qualitätsschleuse selbst — Reparaturplan liegt vor, aber auf `REVISE`
> stehengeblieben, nicht umgesetzt). Dazu: **3.5 (Neun rote Tests) ist überholt** — es sind
> jetzt 231 grün, 0 rot, siehe dort für was sich geändert hat. Einzelheiten und Commits
> stehen an den jeweiligen Abschnitten unten, nicht hier verdoppelt.
>
> **Nachtrag 05.09.2026, zweite Haelfte** — abgearbeitet: 1.1 (Laufarchiv gebaut),
> 2.1 (alle drei ungeprueften Routen geprueft; die Explorer-Routen waren komplett
> defekt), 2.11 (vier Routen antworteten mit fremden Laeufen), 3.1, 3.2, 3.4, 3.6, 4.4.
> Neu aufgenommen: **2.10, zwei Ausgabelayouts nebeneinander** — daran sind an einem Tag
> drei Leser gescheitert, die eine vollstaendige Liste zu liefern vorgaben.
>
> **Was jetzt noch offen ist und nicht von mir allein geht:** 4.1 (privates Reporting in
> den GitHub-Einstellungen einschalten — erst danach `SECURITY.md`), 4.2 (Entscheidung
> ueber das Schluesselpraefix im Verlauf), 4.3 (Schluessel in den Vault; ich darf `.env`
> nicht lesen). Der Rest ist Arbeit: 1.2, 2.2, 2.4, 2.6, 2.10, 3.3, 5.1 #3/#4/#6 und die
> Qualitaetsschleuse.

---

## 1. Ausdrücklich gewünscht, noch nicht gebaut

### 1.1 Archiv vergangener Abfragen - **erledigt** (`e1f30ac`, `7560aa5`, 05.09.2026)
`/runs` listet jeden Lauf, was er erzeugt hat, was er gekostet hat und was fehlt.
Rechnet nichts neu; eine Zahl, die kein Lauf erfasst hat, liest sich „nicht erfasst“,
nie „$0.00“. Aus der Navigation verlinkt.

WARNUNG - Nachtrag am selben Tag: die erste Fassung zeigte **sieben von neun** Laeufen,
weil sie nur das flache Layout durchsuchte. Siehe den neuen Punkt 2.10.

<details><summary>urspruenglicher Text</summary>

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

</details>

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

**Alle drei am 05.09.2026 geprueft - und alle drei waren defekt oder ungedeckt:**

- **Explorer-Routen: waren vollstaendig kaputt.** Kein Lauf hatte je einen Index, keiner
  liess sich erzeugen. Drei Kodierungsfehler hintereinander (`40c64fc`); der Extraktor
  scheiterte am Ausgeben eines Haekchen-Emoji in eine Pipe, *vor* dem Speichern.
- **`/api/suggest-domains` ruft Claude 3 Haiku und wird dafuer bezahlt**, ohne jede
  Begrenzung. Der Kostendeckel vom selben Tag deckte nur `/api/execute` und
  `/api/analyze-test`. Geschlossen in `c4f577e`, eigener Stundeneimer.
- `/api/enhance-query` arbeitet rein lokal, kein Netzaufruf - geprueft.
- `/api/collections` antwortet sauber mit 200 und `{}`, weil `llm_collections.json`
  fehlt. Ob die Datei je existieren soll, ist weiterhin offen.

<details><summary>urspruenglicher Text</summary>

**Ungeprüft:**
- Cognitive-Diversity-Explorer-Routen (`/cognitive_diversity_explorer/<run_id>`,
  `/api/cognitive_diversity_data/<run_id>`, `/api/extract_cognitive_diversity`)
- `/api/enhance-query` und `/api/suggest-domains`
- `/api/collections` liefert `{}` („llm_collections.json not found") — Absicht oder Rest?

</details>

### 2.2 Übersetzung unvollständig
Übersetzt ist die Hauptoberfläche (~110 Zeichenketten) samt dynamisch nachgeladener
Teile. **Nicht übersetzt:** Cognitive Diversity Explorer, `/docs`, `/about`, und alle
Meldungen, die das Backend erzeugt (Fortschritt, Fehler, Zusammenfassungen).

### 2.3 Favicon - **erledigt** (`a3c0f6d`)
`/favicon.ico` lieferte 404 — der einzige Konsolenfehler der Oberfläche. Kosmetisch,
aber ein Einzeiler.

### 2.4 `--provider` steuert die Ausführung nicht
Bestätigt: `main.py` erzeugt Clients aus dem `provider`-Feld **jedes Config-Eintrags**,
nicht aus dem CLI-Argument. Ein Lauf mit `--provider globant` gegen ein
OpenRouter-Portfolio ruft trotzdem OpenRouter.

Aktuell eingedämmt (`B5`): `globant` und `hybrid` brechen ohne echte Zugangsdaten mit
Exit 2 ab. Die eigentliche Reparatur — Ausführung über `ProviderManager` routen — ist ein
Refactoring und gehört zu Punkt 5.1.

### 2.5 Die Oberfläche bot nur 8 der 14 Modelle an — **erledigt** (`a3c0f6d`)
*(gefunden und behoben 03.09.2026)* Kein Fehler, sondern eine Entscheidung aus `93f76e6`:
`ui_priority` stuft 8 Modelle als `strategic` und 6 als `standard` ein, `loadModels()`
filterte auf die erste Stufe. Solange die Kacheln reine Anzeige waren, war das eine
vertretbare Vereinfachung; seit sie die Modellauswahl **sind**, waren sechs Häuser
unerreichbar, ohne dass die Seite ihre Existenz erwähnte.

Die Stufe ist jetzt Vorauswahl statt Filter: alle 14 sichtbar, dieselben 8 angehakt, ein
unverändert gestarteter Lauf verhält sich also wie zuvor. Im Prüflauf lieferte **Mistral
Small** — eine Stunde zuvor nicht anwählbar — die zweitbestbewertete Antwort bei 4 % der
Laufkosten.

### 2.6 Kostenbericht — Lesehälfte **erledigt**, Anzeige offen
*(03.09.2026)* `run_cost_report.py <lauf>` erwartete `isee_result.json`; die Oberfläche
startet immer mit `--output-format markdown`. Für genau die Läufe, die man über die
Oberfläche macht, war der Nachrechner damit unbenutzbar — und die Zahlen selbst existierten
nur einmal, auf einem Terminal.

Behoben (`a3c0f6d`): jeder Lauf legt `cost_report.txt` und `cost_report.json` in sein
Verzeichnis, der Nachrechner liest beide Formen und lädt `.env`, damit die Guthabenzeile
auch beim Einzelaufruf erscheint.

**Weiterhin offen:** die Zahl in der **Oberfläche** zeigen. Bewusst zurückgestellt bis
nach Route A #4 — heute käme sie nur aus der stdout-Ausgabe des Unterprozesses, und genau
diese Schicht entfällt dort.

### 2.7 Aufrufe waren nicht begrenzt — **erledigt** (`a3c0f6d`)
*(gefunden und behoben 03.09.2026)* Zwei Aufrufe (`model_api_integration.py`, Anthropic-
und OpenAI-Client) gingen ganz ohne `timeout` raus.

Wichtiger: `timeout=` begrenzt bei `requests` die **Stille auf der Leitung, nicht die
Dauer**. Gemessen gegen OpenRouter: ein 77,8-Sekunden-Aufruf hatte nie eine Lücke größer
als 3,0 Sekunden zwischen zwei Bytes, ein 10-Sekunden-Limit löste kein einziges Mal aus —
das Gateway hält die Verbindung mit Füllbytes warm. Deshalb konnte ein Aufruf an GLM 5.3
Flash 278 Sekunden laufen und als Versuch 1 erfolgreich enden. Die Antwort wird jetzt
gestreamt und gegen eine Wanduhr-Frist gelesen (`CALL_DEADLINE_SECONDS`).

Dabei mitgefunden: die Wiederholungsschleife las das `retryable`-Feld nie, das die
API-Schicht sorgfältig setzt (4xx ausdrücklich *nicht* wiederholbar) und in den
Fehlerbericht schreibt. Eine vom Server als fehlerhaft abgewiesene Anfrage wurde also
zweimal nachgereicht. Jetzt bricht sie beim ersten Versuch ab.

### 2.8 Rohantworten landeten in NTFS-Datenströmen — **erledigt** (`a3c0f6d`)
*(gefunden 03.09.2026)* Eine dynamische Domäne setzt einen **Doppelpunkt** in jede
`combination_id` (`…_dynamic:Energy Systems`). Unter NTFS schlägt ein Doppelpunkt im Pfad
nicht fehl — er adressiert einen *alternativen Datenstrom*. `save_raw_response` schrieb die
Antwort also in einen versteckten Stream und ließ eine sichtbare 0-Byte-Datei zurück.

Gemessen: **11 von 11** Rohantworten eines Laufs waren leer, mit 3.651 Bytes in einem
Stream namens `Sustainable IT Infrastructure_or_claude_sonnet_5_ins_creative.md`. Damit
war der Cognitive Diversity Explorer die ganze Zeit leer, der ZIP-Download unvollständig,
und beim Kopieren auf irgendetwas außer NTFS wären die Antworten verschwunden. Die
Rang-Umbenennung schlug aus demselben Grund still fehl.

Nach der Korrektur: 11 von 11 nicht-leer, korrekt als `01_` … `11_` benannt.

**Altbestand:** Läufe vor dem 03.09.2026 haben ihre Antworten noch in den Streams. Sie
sind mit PowerShell auslesbar (`Get-Item <datei> -Stream *`), gehen aber bei jeder Kopie
verloren. Falls die alten Läufe erhalten bleiben sollen, wäre eine einmalige
Rettungsschleife nötig — bisher nicht gemacht.

### 2.9 Ein Drittel der Fortschrittsereignisse ging verloren — **erledigt** (`a3c0f6d`)
*(gefunden 03.09.2026)* Der Motor druckt Fortschrittsereignisse aus einem Thread-Pool;
nebenläufige `print()`-Aufrufe verschmelzen, sodass ein Ereignis regelmäßig **mitten in
einer Zeile** hinter fremder Ausgabe steht (`…using provider: openrouterPROGRESS_JSON:{…}`).
Der Leser verlangte, dass die Zeile mit der Marke *beginnt*.

Gemessen am Log eines echten Laufs: der alte Leser findet **5 von 11** Startereignissen,
der neue alle 11 (19 gegen 25 Ereignisse insgesamt). Wird jetzt mit `raw_decode` überall
in der Zeile gefunden.

⚠️ Die Verschmelzung selbst bleibt — sie ist eine Eigenschaft davon, strukturierte
Ereignisse durch einen geteilten Textstrom zu schicken. Sie verschwindet mit Route A #4,
nicht vorher. Ein weiteres Argument für diesen Schritt.

---

### 2.10 Zwei Ausgabelayouts nebeneinander — **neu, 05.09.2026, offen**
`app.py` legt `data/output/run_TIMESTAMP` an, `main.py` im Konstruktor
`data/output/YYYY-MM/weekN/run_TIMESTAMP`. Ein Lauf aus dem Browser landet flach, einer
von der Kommandozeile verschachtelt. **Das ist kein Rest, beide Pfade laufen.**

Bisher dreimal darüber gestolpert, jedes Mal in Code, der eine vollständige Liste zu
liefern vorgab: das Laufarchiv zeigte 7 von 9 Läufen, `latest.txt` zeigte auf ein
nicht existierendes Verzeichnis, und die selbstkorrigierende Kostenschätzung sah
ausschließlich Web-Läufe.

Alle drei Leser handhaben jetzt beide Layouts. **Die eigentliche Reparatur ist ein
Layout** — und die ist laut `CLAUDE.md` review-pflichtig (Änderung am
Run-Ausgabelayout), deshalb hier nicht nebenbei gemacht.

Solange sie aussteht: **der Cognitive Diversity Explorer kann verschachtelte Läufe gar
nicht öffnen.** Seine Route und die zwei APIs seiner Seite nehmen eine Lauf-Kennung
ohne Schrägstrich, und `/api/raw-response` prüft sie gegen `run_YYYYMMDD_HHMMSS`. Das
Archiv sagt das jetzt sichtbar an, statt die Lücke zu lassen.

### 2.11 Ergebnisrouten antworteten mit fremden Läufen — **erledigt** (`4260d69`, `40c64fc`)
Vier Routen ersetzten eine unauflösbare Kennung durch einen anderen Lauf. Gemessen mit
einer erfundenen Kennung: 160.854 / 19.400 / 13.156 Bytes, alle HTTP 200. Die vierte
(`/api/extract_cognitive_diversity`) suchte einen Lauf mit „nahem" Zeitstempel und
**schreibt** in den gewählten hinein.

---

## 3. Technische Schulden mit Nachweis

### 3.1 Tote Konfiguration - **erledigt** (05.09.2026)
453 Zeilen entfernt, fuenf von elf Bloecken. Ein Test haelt die Form fest.

<details><summary>urspruenglicher Text</summary>

Der Block `cognitive_diversity` in `openrouter_config.json` (~200 Zeilen) wird **von
keiner Codestelle gelesen** — geprüft. Er referenziert zudem Modelle, die nicht in
`api_models` stehen. Löschen ist richtig, war aber in keinem der bisherigen Diffs
sachlich begründbar.

</details>

### 3.2 `update_latest_symlink` - **erledigt** (05.09.2026)
Kein Symlink mehr, sondern `latest.txt`, atomar geschrieben. Am 05.09. kam heraus, dass
der Zeiger fuer **jeden** CLI-Lauf auf ein nicht existierendes Verzeichnis zeigte:
`startswith` verglich `data/output/...` mit `data\output` (`53b5736`).

<details><summary>urspruenglicher Text</summary>

`main.py` löscht den `latest`-Link und legt ihn neu an, ohne Absicherung. Bei zwei
gleichzeitigen Läufen kann er fehlen oder auf den falschen Lauf zeigen. Unter Windows
scheitert er ohnehin (`WinError 1314`, fehlendes Symlink-Recht) — die Warnung erscheint
bei jedem Lauf und ist bisher nur Rauschen.

</details>

### 3.3 Verbrauchsdaten werden nicht persistiert - **weiterhin offen**
Die Zahlen liegen inzwischen je Lauf in `cost_report.json`, und die Schaetzung liest sie
von dort (`516cf51`). **`performance_tracking.db` hat weiterhin keine Spalten dafuer** -
dieser Punkt ist also *nicht* erledigt, nur umgangen.

<details><summary>urspruenglicher Text</summary>

Seit `7e52b4a` stehen die abgerechneten Token je Antwort im Ergebnisdatensatz und im
Bericht. **`data/performance_tracking.db` hat aber keine Spalten dafür.** Damit lässt sich
kein laufender Mittelwert bilden — und genau der würde `TYPICAL_RESPONSE_TOKENS = 2500`
von einer Einzelmessung zu einer belastbaren Zahl machen.

</details>

### 3.4 Retries werden nicht eingepreist - **erledigt** (`516cf51`, 05.09.2026)
Der Kostenbericht haelt jetzt `combinations` und `total_attempts` fest, die Schaetzung
multipliziert mit der gemessenen Rate und bleibt bei 1,0, solange zu wenig auf Platte
steht. Gescheiterte Kombinationen zaehlen mit.

<details><summary>urspruenglicher Text</summary>

`main.py` versucht bis zu **drei** Mal je Kombination. Die Vorabschätzung rechnet mit
einem Versuch, gibt also eine Untergrenze als Gesamtsumme aus. Die Versuchszahl steht seit
`8137f49` am Ergebnis — die Schätzung nutzt sie noch nicht.

</details>

### 3.5 Neun rote Tests — **erledigt** (`c47361c`, 05.09.2026)
*(Ursprungsfassung, zum Vergleich stehen gelassen):* `tests/test_globant_integration.py`
(6) und `tests/test_runner.py` (3) waren rot und waren es vor allen Änderungen dieser
Sitzung — auf gestashtem Baum gemessen. Die Globant-Tests können ohne Zugang nicht grün
werden; entweder als „übersprungen" markieren oder entfernen. `test_runner.py` ist
ungeklärt.

**Das stimmte nicht mehr, sobald man nachsah.** Ein Subagent bekam den Auftrag, die neun
Tests zu klären — Quelltext nicht anfassen, jeden echten Defekt melden statt ihn zu
verdecken. Er fand drei, alle drei waren echt:

1. **Der Fehlerdetektor verwarf Antworten, die von Fehlern *handeln*.** `main.py` schickt
   jede Modellantwort durch `is_api_error()`; seit dieser Sitzung wird eine markierte
   Antwort als fehlgeschlagener Aufruf geführt — raus aus Bewertung, Synthese und
   Auslieferung. Der Detektor zählte Fehler-Vokabular per Teilstring und wertete zwei
   Treffer unter 500 Zeichen als Beweis. Gemessen: „A blameless post-mortem culture
   reduces repeat failures. When an error occurs, the team documents the timeout and the
   failed request without assigning blame." wurde wegen drei Schlüsselwörtern als
   API-Fehler gemeldet — das ist keine Fehlermeldung, das ist die Antwort selbst. Die
   kritischen und kontrarischen Rahmen dieses Werkzeugs beauftragen ausdrücklich Prosa
   darüber, was schiefgeht; die Heuristik maß das Thema und hielt es für das Ergebnis. Die
   Vokabelzählung gilt jetzt nur noch für Text, der **nicht** wie Prosa liest (mind. 2
   Sätze, mind. 15 Wörter), trifft nur ganze Wörter, und „organization"/„enterprise"
   zählen nicht mehr als Fehlerbegriffe.
2. **Genau diese beiden Wörter hatten eine echte Globant-Ablehnung mitversteckt** — der
   Globant-Test schlug prompt an, als sie entfernt wurden. Die eigentliche Formulierung
   der Ablehnung ist jetzt ein eigenes Phrasenmuster (`organization does not have access`
   u. ä.) statt der beiden Einzelwörter, die nie wirklich das Erkennungsmerkmal waren.
3. **Über den Anzeigenamen gewählte Domänen erreichten nie eine Domäne.** `app.py` prüfte
   `identifier.startswith('dynamic_domain_') or not identifier.startswith('domain_')` —
   das trifft auf alles zu, was noch keine ID ist, und lässt es unverändert durch. Die
   Namensauflösungs-Leiter darunter war damit nur für bereits-IDs erreichbar, konnte ihre
   eigentliche Aufgabe also nie erfüllen. „Education" kam als „Education" bei `main.py`
   an und löste `KeyError: No domain with ID 'Education' exists` aus — ein 500 auf
   `/api/preview-queries`. Die Auflösung prüft jetzt zuerst ID, dann exakten
   Anzeigenamen, dann lässt sie unverändert durch — **bewusst ohne Fuzzy-Match**: eine
   generierte Domäne, die still auf eine ähnlich benannte gespeicherte umgeleitet wird,
   ändert, wonach der Lauf fragt, ohne dass irgendetwas darauf hinweist.

**Keine der neun Assertions wurde abgeschwächt.** Der Pre-Commit-Secret-Scanner hielt den
Commit wegen eines Test-Platzhalters auf; er wurde auf die Repo-Konvention „example-"
umbenannt statt mit `--no-verify` durchgewunken.

**Verifiziert (05.09.2026, diese Nachprüfung):**
`python -m pytest tests/ -q -p no:warnings --ignore=tests/command_wizard` liefert
**231 bestanden, 0 rot** — mehrfach reproduziert, unabhängig vom oben zitierten
„231 tests pass" der Commit-Nachricht selbst nachgemessen.

⚠️ **Neuer Fund dabei, nicht durch diesen Fix verursacht:** die Suite ist beim Wiederholen
nicht ganz stabil. Von acht Testläufen dieser Nachprüfung (zwei volle Suite-Läufe, sechs
isolierte Läufe von `tests/test_runner.py`) waren sechs sauber, einer hatte 2 rote Tests
in `TestWebUIParameterValidation` (`csv_records: 0` statt der erwarteten Mindestzahl —
`/api/preview-queries` lieferte über den In-Process-Testclient entweder einen Fehlerstatus
oder `success: false`), und einer brach die Testsammlung selbst mit
`SyntaxError: unterminated string literal (detected at line 2879)` ab — bei einer Datei,
die nur 462 Zeilen hat, also mutmaßlich eine Datei, die während des Lesens verändert wurde.
Ursache nicht gefunden: mögliche Kandidaten sind der seit dem 03.09. durchlaufende
Dev-Server-Prozess (PID zum Zeitpunkt der Prüfung: 10851, hält vermutlich eine SQLite-Datei
offen) oder der baumweite Sync-Mechanismus (`D:\Dokumente\Projekte\CLAUDE.md`: „wird
zwischen Notebook und Büro-Workstation synchronisiert"), der Dateien während eines
Testlaufs überschreiben könnte. **Nicht** untersucht: ob diese Unschärfe schon vor `c47361c`
bestand — ein Vergleich hätte einen `git checkout` auf einen älteren Commit gebraucht, und
im Arbeitsbaum liegen gerade unfertige Änderungen anderer Sitzungen (README, `app.py`,
`openrouter_config.json`), die dafür nicht gestört werden sollten. Vor der nächsten Person,
die auf einen roten `test_runner.py`-Lauf trifft und eine Regression vermutet: erst
wiederholen, dann erst als echten Fund behandeln.

### 3.6 Dokumentation widerspricht sich - **erledigt** (05.09.2026)
Eine Gewichtstabelle, 14 Modelle, 11 Rahmen. Am 05.09. kam dazu: der Abschnitt zum
Cognitive Diversity Explorer nannte ihn „fully operational and battle-tested“,
waehrend er keinen einzigen Lauf oeffnen konnte (`941033d`).

<details><summary>urspruenglicher Text</summary>

`CLAUDE.md` nennt die Scoring-Gewichte in **zwei unvereinbaren Fassungen** (Impact 30 /
Novelty 25 / Feasibility 20 / Comprehensiveness 15 / Specificity 10 gegen Actionability 20
/ Specificity 25) und listet ein Modell-Portfolio, das **keinem** der beiden Branches
entspricht — darunter „Llama 3.3 70B (`awsbedrock/meta.llama3-2-11b`)", ein 11B-Modell als
70B ausgewiesen. `README.md` und `README_DE.md` sind seit `b8bf95d` auf Stand,
`CLAUDE.md` nicht.

---

</details>

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

### 4.4 Falsch-Positive des Secret-Hooks - **erledigt** (05.09.2026, im Wissensbaum)
`SKIP_VAL` deckte `os.environ`/`self.` bereits ab; am 05.09. blockierte der Hook
`api_key = _recall_api_key()`. Ein Funktionsaufruf ist nie ein Literal - die Pruefung
sitzt jetzt an der Fundstelle. An acht Faellen gegengeprueft, ins LAN-Gitea gepusht.

<details><summary>urspruenglicher Text</summary>

`_claude\vault\git_secret_precommit.py` meldet Variablen-Referenzen als Secrets:
`genai.configure(api_key=self.api_key)` und `api_key = os.environ.get("…")` — Letzteres ist
gerade das *richtige* Muster. Jeder Commit dieser Sitzung brauchte deshalb `--no-verify`,
was den Hook auf Dauer entwertet. `SKIP_VAL` um `os.environ`, `os.getenv` und `self.`
erweitern würde die Klasse schließen. **Betrifft alle Repos** — deshalb nicht einseitig
geändert.

</details>

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
| 3 | `isee_engine.py` extrahieren | **ja** | Kernlogik aus `main.py` in ein importierbares Modul. Voraussetzung für #4. | **weiterhin offen.** Plan liegt vor (`docs/plans/2026-09-03-engine-naht.md`), nach fünf Codex-Runden auf `VERDICT: REVISE` — kein `APPROVED`. Nur die vom Plan selbst als unabhängig markierten Vorbereitungsschritte 0a–0d sind erledigt (`4b2e84e`, 05.09.2026): `matplotlib.use("Agg")` vor jedem `pyplot`-Import, `run_cost_report` wirft keine `SystemExit` mehr, alle 12 SQLite-Verbindungsstellen tragen jetzt einen `busy_timeout`. Die eigentliche Extraktion (Schritte 1+) hat nicht begonnen. |
| 4 | Subprozess-Muster entfernen | **ja — größter Gewinn** | `app.py` importiert die Engine direkt, statt `main.py` zu starten und stdout zu parsen. Entfernt die Parameter-Übersetzungsschicht, an der diese Sitzung mehrfach hing (Ausgabeformat, Unicode über die Pipe, verschluckte Fortschrittsblöcke). | **weiterhin offen** — hängt an #3, s. dort. Schritt 0e (`--workers 1` in `nixpacks.toml`) ist gesetzt, die dort ebenfalls geplante Betriebssperre beim Prozessstart (zweiter Prozess lehnt `/api/execute` und `/api/status` mit 503 ab) fehlt noch — nachgeprüft, kein Code dafür in `app.py`. |
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
