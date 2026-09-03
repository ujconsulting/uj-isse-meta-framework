# Plan: die Bewertung reparieren — und dann erst anschalten

**Stand:** 03.09.2026, Runde 3 · **Branch:** `fix/honest-failure-reporting` · **Basis:** `7f5eb86`
**Grundlage:** `docs/audit/2026-09-03-baseline.md`, Punkte 1 und 2

> **Runde 3.** Zwei Runden Codex-Kritik eingearbeitet, alle 19 Punkte angenommen. Fünf
> waren Fehler von mir: ein Datenschutzfehler (§4a-2), eine zu starke zentrale Behauptung
> (§4), ein **Rechenfehler** (11 Rahmen × 2 Paare = 22, verfügbar 18 — §4a-3), ein
> **statistischer Fehler** (Wilson-Intervall gegen Punktwert statt gepaartem Test — §4b)
> und eine Kostenrechnung (+50 % statt +100 % — §3 C).

---

## 1. Der Befund, gemessen

`main.py:461` baut das Bewertungsgerüst und ruft in `evaluate_results` `score_text()` —
**nicht** `score_text_with_quality_gates()`. Die Qualitätsschleuse ruft niemand auf.

| Eingabe | Pfad, der läuft | Pfad, den `CLAUDE.md` beschreibt |
| --- | --- | --- |
| gute, knappe Antwort | 0,298 | 0,050 |
| **reine Platzhalter-Vorlage** | **0,292** | 0,050 |

Anschalten geht nicht. Eine Antwort mit Kosten, Fristen, Temperaturen, Grenzwerten und
Messergebnissen (138 Wörter):

| Variante | Ergebnis |
| --- | --- |
| unverändert | 0,195, scheitert an `insufficient_implementation_details` |
| + ein Auslassungszeichen / ein JSON-Beispiel / das Wort „TODO" | je 0,050 |
| dieselbe Aussage in 21 Wörtern | 0,050 |

---

## 2. Die Wurzel: die Schleuse misst die *Form*, nicht die Substanz

`evaluation_scoring.py:500` verlangt zwei Treffer aus:

```python
r'step \d+[:\.)]'   r'phase \d+[:\.)]'   r'for example.*…'
r'specifically.*[a-zA-Z]{6,}'   r'implementation.*(?:plan|strategy|approach)'
r'\b(?:deploy|configure|setup|install)\b.*\b\w{4,}\b'
```

Erkannt wird **die Gestalt einer englischsprachigen Umsetzungs-Checkliste**. „84.000 Euro,
Amortisation 3,1 Jahre, Mindestvorlauf 55 Grad" enthält mehr überprüfbare Substanz als
jede „Step 1:"-Liste und fällt trotzdem durch. Auf Deutsch ohnehin.

**Wortvorkommen ist kein Qualitätsmaß.** Ein Flicken an den Listen ändert das nicht.

---

## 3. Die anfechtbare Grundentscheidung

**A — Heuristiken flicken.** Billig, hält an „Wörter zählen" fest. Der nächste Fehler
derselben Art kommt bestimmt.

**B — innere Bestimmtheit statt Vokabellisten.** ⭐ *In Runde 3 ehrlicher benannt.*
Gezählt wird eine Größe mit Einheit, die an einen Mechanismus, eine Rechnung oder eine im
selben Text konsistente Vergleichsgröße gebunden ist. „Kostet 84.000 EUR" zählt nicht;
„84.000 EUR Investition, Amortisation 3,1 Jahre bei 27.000 EUR jährlicher Einsparung"
zählt, weil die drei Zahlen zueinander passen müssen.

⚠️ **Das Maß heißt bewusst nicht „belegt".** Runde 2: Verankerung verschiebt das
Vortäuschen nur nach außen — eine in sich stimmige *erfundene* Rechnung erfüllt das
Kriterium vollständig. Gemessen wird also **innere Bestimmtheit und Widerspruchsfreiheit**,
nicht Wahrheit. Diese Schicht kann Wahrheit nicht prüfen und behauptet es nicht.

Zwei Folgen daraus: der Anteil dieses Signals an der Gesamtbewertung wird **gedeckelt**
(kein Kriterium darf allein den Ausschlag geben), und unter die Abnahmefälle kommen
**stimmige Fälschungen** — ausdrücklich mit dem erwarteten Ergebnis, dass sie **bestehen**.
Ein Abnahmefall, der eine bekannte Grenze festhält, ist mehr wert als einer, der sie
verschweigt.

**C — ein Modell urteilen lassen.** Fachlich der heutige Stand, kostet aber **66
zusätzliche Aufrufe je Volllauf — eine Verdopplung der Aufrufzahl, nicht „+50 %"** wie in
Runde 1 falsch gerechnet. *Nicht jetzt*; B ist so gebaut, dass C danebentreten kann.

⚠️ **Gegen B, unverändert ehrlich:** Eine kluge strukturelle Einsicht ohne eine einzige
Zahl — genau das, was der kontrarische oder historische Rahmen liefern soll — wird
benachteiligt. Die naheliegende Abhilfe wäre eine Gewichtung je Rahmen; die trägt die
Referenzmenge aber nicht (§4a-3), sie ist **entfallen**. Es bleiben die Deckelung oben und
R2 — und damit ein **offen bleibender Nachteil**, kein gelöstes Problem.

⚠️ **„Sprachunabhängig" war überzogen** (Codex, berechtigt): Dezimalkomma gegen
Dezimalpunkt, `84.000` gegen `84,000`, Datumsformate, Einheitenschreibweisen. Der Plan
nennt jetzt ausdrücklich die unterstützten Formate (de-DE, en-US) und prüft
gleichbedeutende deutsche und englische Angaben gegeneinander.

---

## 4. Der Knackpunkt: was eine Referenzmenge beweisen kann — und was nicht

Runde 1 dieses Plans behauptete, eine Referenzmenge mache die Änderung widerlegbar.
**Das war zu stark.** Codex: Verbesserung auf 30 Paaren *eines* Beurteilers über *ein*
Thema belegt, dass man die Vorlieben dieses Beurteilers getroffen hat — mehr nicht.

Das bleibt richtig und wird nicht wegdiskutiert. Was der Plan stattdessen tut:

### 4a. Die Menge ehrlich zuschneiden

- **Zwei Fragestellungen**, nicht eine — die aus den Läufen vom 03.09.2026, hier nur als
  `Q1` und `Q2` geführt. ⚠️ Der Wortlaut steht **nicht** in diesem Plan: das Repo ist
  öffentlich, und die Fragen gehören dem Betreiber. Zweiter Fund derselben Art in dieser
  Prüfung, s. §4a-2. Beide stammen aus demselben Themenfeld; **das ist eine Schwäche und
  wird als solche ausgewiesen.**
- **Aufteilung Entwicklung / verschlossene Bestätigungsmenge (60/40)**, vor der ersten
  Codezeile festgelegt. Die
  Bestätigungsmenge wird während der Arbeit nicht wieder geöffnet und **genau einmal** am
  Ende gemessen.
- **Vorab festgeschrieben:** alle Paare werden geurteilt, **bevor** eine Zeile geändert
  wird, und das Urteil wird committet.
- **Unentschieden ist erlaubt** und zählt weder als Treffer noch als Fehler.

⚠️ **Es heißt bewusst nicht Rückhalt** *(Runde 2, berechtigt)*. Derselbe Mensch
urteilt über alle Paare, bevor die Entwicklung beginnt — damit sind ihm Inhalt und
Vorlieben der Bestätigungsmenge bekannt, und sie sickern in die Umsetzung ein. Der saubere
Weg wäre ein unabhängiger Verwahrer, der sie erst nach dem Codefreeze herausgibt. **Den gibt es hier nicht — es ist ein Mensch.**

Was bleibt, mildert das nur: die Paare werden **ohne Kenntnis von Modell und Rahmen**
geurteilt (nur die beiden Texte), und die Paare der Bestätigungsmenge werden während der
Arbeit nicht erneut geöffnet. Sie **bestätigt** damit allenfalls, sie **belegt** nicht —
daher der Name, und daher steht es so im Bericht.

### 4a-2. Wo die echte Menge liegt

`.claudex-tmp/` ist gitignoriert, aber **das ist kein Schutz** — der Ordner liegt im
Arbeitsverzeichnis und wandert bei jeder Kopie mit (Runde 2, berechtigt).

Die echte Referenzmenge liegt daher **außerhalb des Repos**, unter
`D:\Dokumente\Projekte\_claude\scoring-reference\` (gesyncter, nicht öffentlicher Baum).
Im Repo steht ausschließlich ein **Integritäts-Verzeichnis**. Ein bloßer Hash des Urteils
genügt nicht (Runde 3, berechtigt) — er bindet das Urteil an nichts. Das Verzeichnis führt
je Paar: Paar-Kennung, Zugehörigkeit zu Entwicklung oder Bestätigung, **SHA-256 der beiden
Antworttexte**, das Urteil und den Zeitstempel. Damit ist nachweisbar, dass ein Urteil zu
genau diesen beiden Texten gehört und nachträglich weder Text noch Urteil getauscht wurde —
ohne einen einzigen Inhalt zu veröffentlichen.

### 4a-3. Rahmenabhängige Gewichtung — verschoben, weil die Arithmetik nicht aufgeht

Runde 1 verlangte „je Rahmen mindestens zwei Paare". **Nachgerechnet, Codex hat recht:**
11 Rahmen × 2 Paare = 22, aber 60 % von 30 sind 18. Vier zu wenig, und die Lücke mit
Paaren der Bestätigungsmenge zu füllen würde genau diese entwerten.

Realistisch ist die Menge nicht dafür da. Also: **rahmenabhängige Gewichtung entfällt aus
diesem Vorhaben**, ein einheitlicher Vorgabewert gilt für alle Rahmen. Der Einwand aus §3
(Einsicht ohne Zahlen wird benachteiligt) wird damit **nicht gelöst**, sondern als offene
Grenze geführt — und die Deckelung des Konkretheitsanteils (§3 B) ist die einzige
Milderung, die dieses Vorhaben leistet.

### 4b. Der Maßstab, mit Fehlerbalken

30 Paare, ein Umschlag = 3,3 Punkte. Eine solche Zahl ohne Unsicherheit vorzuzeigen wäre
Scheingenauigkeit.

Runde 1 dieses Plans wollte das Wilson-Intervall des **neuen** Bewerters gegen den
**Punktwert** des alten halten. **Das ist statistisch falsch** (Runde 2, berechtigt):
beide Bewerter werden auf **denselben** Paaren gemessen, die Ergebnisse sind also
verbunden, und der Ausgangswert hat selbst eine Unsicherheit.

Richtig ist ein **gepaarter** Test, und er wird **einmal** festgelegt und überall
derselbe verwendet (Runde 3: die Abnahme verlangte noch Wilson und widersprach damit
dieser Stelle).

**Das vorab festgelegte Kriterium:** Gezählt werden nur die **uneinigen** Paare — `b` =
neu richtig, alt falsch; `c` = alt richtig, neu falsch. Betrachtet wird `b / (b + c)`
gegen 0,5, mit **exaktem Binomial-Konfidenzintervall (Clopper-Pearson, 95 %)** — das ist
der exakte McNemar-Test. **Verbesserung gilt nur, wenn die untere Grenze über 0,5 liegt.**
Einige Paare bleiben `b + c = 0`; dann ist die Frage unentscheidbar und wird so berichtet,
nicht gerundet.

Bei 30 Paaren heißt das: **kleine Gewinne sind nicht nachweisbar.** Fällt es so aus, ist
das die Antwort, nicht ein Anlass den Maßstab zu senken.

### 4c. ⛔ Die echten Antworten dürfen nicht ins Repo

**Von mir übersehen, von Codex gefunden.** Die Rohantworten enthalten unter „Prompt Sent
to Model" die **vollständige Forschungsfrage** — geprüft. Dieses Repo ist **öffentlich**.
Sie nach `tests/data/` zu committen, würde die Fragen des Nutzers veröffentlichen.

Also:

- Im Repo liegen **ausschließlich** von Hand geschriebene, synthetische Beispieltexte —
  erfunden, ohne Bezug zu echten Läufen.
- Die echte Referenzmenge liegt **außerhalb des Repos** — Ort und Begründung in §4a-2.
  (Diese Zeile nannte in Runde 2 noch `.claudex-tmp/` und widersprach damit §4a-2.)
- Der Testlauf gegen die echte Menge ist ein Werkzeug für den Betreiber, kein Testfall der
  Suite.

---

## 5. Schritte

Reihenfolge in Runde 2 geändert — Codex hat zu Recht angemerkt, dass Schritt 8 der alten
Fassung gar nicht der letzte war und dass die Schleuse vor der Fehlerbehandlung
anzuschalten die Rangfolge kaputtmachen kann.

| # | Schritt | Prüfung |
| --- | --- | --- |
| 1 | **Fehler je Kriterium sichtbar machen** statt als 0.0 zu tarnen (Baseline eval #7) | Test mit einer werfenden Kriteriumsfunktion |
| 2 | Referenzmenge anlegen und **committen**, synthetisch im Repo, echt daneben (§4) | ≥30 Paare, geschichtet, 60/40 geteilt, Begründung je Paar |
| 3 | Heutigen Stand messen, **beide** Pfade, nur auf der Entwicklungshälfte | zwei Zahlen mit Intervall, im Plan festgehalten |
| 4 | Gewichte: Summe auf 1,0, dokumentiert = wirksam | Test `sum == 1.0`; `CLAUDE.md` nennt **eine** Fassung |
| 5 | Platzhaltererkennung: nur echte Vorlagen; **kein** `"..."`, kein blankes `{…}`, keine Wortuntergrenze | die vier konstruierten Fälle |
| 6 | Verankerte Angaben statt Vokabellisten (§3 B), Formate de-DE und en-US | Entwicklungshälfte + **Fälschungs-Fixtures** (erfundene, unzusammenhängende Zahlen dürfen **nicht** punkten) |
| 7 | R4-Grenzen aus der Verteilung bestimmen und **festschreiben**, bevor der neue Bewerter steht | zwei Zahlen im Plan, danach unveränderlich |
| 8 | `scoring_version` schreiben, Altbestand-Rückfall, je ein Lesertest | fünf Leser, je mit und ohne Feld |
| 9 | **Schattenbetrieb:** neuer Bewerter läuft mit, Ergebnis nur **protokolliert** | ein echter Lauf, beide Rangfolgen nebeneinander |
| 10a | **Generalprobe A:** Lauf mit dem neuen Bewerter in ein Wegwerf-Verzeichnis, Abdeckung **erfüllt** → Synthese entsteht; alle Leser, CLI, Ergebnisroute | echter Lauf, 11 Aufrufe |
| 10b | **Generalprobe B:** derselbe Weg mit **erzwungener** Verletzung (Abdeckung künstlich unterschritten, gefälschter Transport) → **keine** Synthese, `completed_with_failures` sichtbar | kein bezahlter Lauf |
| 11 | **Erst jetzt** umschalten | Bestätigungsmenge, **einmalig**, gepaarter Test nach §4b |

Schritt 9 stammt von Codex, Schritt 10 ebenfalls — er schließt eine Lücke, die ich
übersehen hatte: **Schattenbetrieb vergleicht nur Ränge.** Was beim Umschalten wirklich
anders wird — welche Antworten in die Synthese gehen, wie sich der Keine-Synthese-Zweig
verhält, ob die Leser das Format vertragen, was die Oberfläche anzeigt — sieht der
Schattenlauf nicht, weil sein Ergebnis nirgends hinfließt.

Die Teilung in 10a und 10b stammt aus Runde 3 und ist zwingend: die beiden Zweige
schließen einander aus, **ein** Lauf kann nie beide durchlaufen. 10b braucht kein Geld —
die Verletzung wird erzwungen, der Transport gefälscht.

Rahmenabhängige Gewichtung ist **entfallen** (§4a-3): die Referenzmenge trägt sie nicht.

---

## 6. Risiken

**R1 — Die Referenzmenge bildet einen Beurteiler und ein Themenfeld ab.** Bleibt so; §4
weist es aus. *Bedingung für Neubewertung:* sobald Läufe aus einem anderen Themenfeld
vorliegen, Menge erweitern und erneut messen.

**R2 — Bestimmtheit verdrängt Einsicht.** *Maßnahme:* mindestens sechs Paare der
Entwicklungsmenge, in denen die substanziellere Antwort **weniger** Zahlen enthält, und
dieselbe Bedingung als eigenes Abnahmekriterium. (Runde 2 verwies hier auf „Schritt 8" —
das war nach dem Umnummerieren `scoring_version`; die Maßnahme hing damit an nichts.)

**R3 — Erfundene Zahlen punkten.** Der Haupteinwand gegen B. *Maßnahme:* Verankerung
(§3 B) und ausdrückliche Fälschungs-Fixtures: eine Antwort mit zusammenhanglosen,
erfundenen Größen darf **nicht** besser abschneiden als eine ehrliche ohne Zahlen.
*Grenze:* Erfundene, aber in sich stimmige Zahlen sind von echten nicht zu unterscheiden.
Das kann diese Schicht nicht leisten und behauptet es auch nicht.

**R4 — Anschalten leert Läufe.** Runde 2 hält zu Recht fest, dass die vorige Fassung eine
„aus der Verteilung abgeleitete" Grenze **behauptete**, aber nur eine feste Regel
(„weniger als drei") enthielt — und dass drei überlebende Antworten radikal einseitig sein
können.

*Maßnahme, vorab festzulegen und dann nicht mehr zu ändern:*

1. **Ausschussquote.** „Median plus zwei Streuungen" ist keine umsetzbare Vorschrift
   (Runde 3, berechtigt). Genau: Beobachtungseinheit ist **ein Lauf**; gemessen wird der
   Anteil disqualifizierter Antworten je Lauf über die beiden Läufe vom 03.09.2026
   (11 + 11 Antworten). Grenze = Median + 2 × **mittlere absolute Abweichung vom Median**
   (robust bei n = 2), auf `[0, 1]` beschnitten, Vergleich **strikt größer**. Die Zahl wird
   **vor** dem neuen Bewerter berechnet und im Plan festgeschrieben. ⚠️ Bei zwei Läufen ist
   sie schwach belegt und wird nach den ersten fünf Läufen mit dem neuen Bewerter neu
   bestimmt.
2. **Abdeckung:** überleben Antworten aus weniger als drei verschiedenen Rahmen **oder**
   weniger als zwei verschiedenen Modellen, ist die Vielfalt dahin, auf die sich die
   Synthese beruft.
3. **Bei Verletzung einer der beiden Regeln: keine Synthese.** Der Lauf endet als
   `completed_with_failures` mit Begründung, in CLI und Oberfläche. Die Rohantworten
   bleiben vollständig erhalten — sie sind das eigentliche Ergebnis, die Synthese ist
   Zugabe.

⚖️ Das tauscht ein stilles schlechtes Ergebnis gegen ein lautes fehlendes. Das ist
Absicht: eine Synthese aus drei einseitigen Antworten sieht aus wie ein Ergebnis und ist
keins.

**R5 — Rangfolgen früherer Läufe werden unvergleichbar.** *Maßnahme:* `scoring_version`
in `isee_result.*` **und** `combinations.csv`. Leser: `reporting.py`, `analysis.py`,
`performance_tracker.py`, `cognitive_diversity_extractor.py`, die Ergebnisrouten in
`app.py`.

**Altbestand** *(Runde 2, berechtigt — vorher nicht bedacht)*: alle bisherigen Läufe haben
das Feld **nicht**. Fehlt es, gilt `scoring_version = "legacy-pre-2026-09"`, und wo Läufe
verglichen werden, wird ungleiche Version **angezeigt** statt stillschweigend gemischt. Je
Leser ein Test mit einem Lauf **ohne** das Feld.

**R6 — Laufzeit.** `evaluate_results` läuft im selben Prozess wie die Weboberfläche.
*Maßnahme:* Laufzeit auf den 21 echten Antworten vorher/nachher messen; keine neuen
Ausdrücke mit katastrophalem Backtracking (jeder neue Ausdruck gegen eine pathologische
Eingabe geprüft).

**R7 — Der Prüflauf kostet Geld.** Schritt 9 und 10 brauchen je einen echten Lauf.
*Budget:* Testmodus, 11 Aufrufe, ~$0,12 je Lauf, zusammen **unter $0,30**. Restguthaben
$17,94. Kein Volllauf nötig. Von Hand ausgelöst, nie automatisch; die Suite arbeitet
durchgehend mit gefälschtem Transport.

---

## 7. Ausdrücklich außerhalb

- Ein Modell als Bewerter (§3 C)
- Motor-Naht (`2026-09-03-engine-naht.md`) — unabhängig
- Cognitive Diversity Explorer, obwohl er dieselben Bewertungen anzeigt
- Übrige Baseline-Befunde zu `reporting.py`, `cost_estimation.py`, `query_generator.py`
- **Mehrere Beurteiler für die Referenzmenge.** Wäre methodisch richtig, es gibt hier aber
  nur einen Menschen. Als Grenze ausgewiesen, nicht als gelöst behauptet.
- **Rahmenabhängige Gewichtung** — entfallen, weil die Referenzmenge sie nicht trägt
  (§4a-3). Der Einwand aus §3 bleibt damit offen.

---

## 8. Abnahme

1. Referenzmenge committet **vor** der ersten Codeänderung; die Bestätigungsmenge wird bis
   zum Schluss nicht wieder geöffnet. Im Repo ausschließlich synthetische Texte plus das
   Integritäts-Verzeichnis aus §4a-2. ⚠️ Sie heißt Bestätigungsmenge und nicht Rückhalt,
   weil derselbe Mensch sie vorab beurteilt hat — sie **bestätigt**, sie **belegt** nicht.
2. **Das eine Kriterium aus §4b**, nirgends ein anderes: `b / (b + c)` über die uneinigen
   Paare, exaktes Clopper-Pearson-Intervall (95 %), gemessen auf der Bestätigungsmenge,
   **einmal**. Verbesserung gilt nur, wenn die untere Grenze über 0,5 liegt. Ist
   `b + c = 0`, ist die Frage unentscheidbar und wird so berichtet. Liegt die Grenze nicht
   darüber, gilt das Vorhaben als **nicht belegt** und wird zurückgenommen — nicht
   nachjustiert, bis die Zahl stimmt.
3. Die vier konstruierten Fälle: Platzhalter-Vorlage disqualifiziert, knappe gute Antwort
   **nicht**, konkrete deutsche Antwort nicht schlechter als die gleichwertige englische,
   Modewort-Antwort unter beiden.
4. Fälschungs-Fixtures: erfundene zusammenhanglose Zahlen punkten nicht.
5. Gewichte summieren auf 1,0; `CLAUDE.md` nennt genau **eine** Fassung, und sie stimmt.
6. Schattenlauf: beide Rangfolgen nebeneinander protokolliert, Abweichung benannt.
7. `scoring_version` im Ergebnis, je ein Lesertest für die fünf Leser aus R5.
8. Laufzeit der Bewertung nicht schlechter als vorher, gemessen.
9. Generalprobe (Schritt 10) durchlaufen: Synthese-Zweig, Keine-Synthese-Zweig, fünf
   Leser, CLI und Ergebnisroute — je mit und ohne `scoring_version`.
10. **Dokumentation vollständig nachgezogen**, nicht nur `CLAUDE.md`: `README.md`,
    `README_DE.md`, der Scoring-Abschnitt in `CLAUDE.md`, `docs/audit/2026-09-03-baseline.md`
    (Punkte 1, 2 und eval #7 als erledigt vermerkt) und diese Plandatei mit den gemessenen
    Ergebnissen.
