# Plan-Review-Log: die Bewertung reparieren

Begonnen 03.09.2026. MAX_ROUNDS=5.

- Plan: `docs/plans/2026-09-03-bewertung-reparieren.md` (sha256 `849ae8b37565212d…`)
- Kritiker: Codex, `gpt-5.6-terra`, effort `high`, read-only, Wrapper 2.3.1
- ⚠️ Codex' Sandbox weist auf diesem Rechner jeden Dateizugriff ab; die Prüfung
  beruht auf dem Plantext plus den eingebetteten Messungen.

---

## Runde 1 — Codex

- §4’s central falsifiability claim is wrong: improvement on ~30 selected pairs from one annotator is evidence only of fitting that annotator’s choices, not of improving scoring generally. Fix: use a preregistered, framework-stratified held-out set with multiple independent annotators and report uncertainty/disagreement.

- The reference-set design is internally inconsistent: §4 says one topic; R1 requires at least two questions, without specifying selection or a holdout. Fix: define the questions, framework coverage, sampling rule, development/holdout split, and annotation protocol before inspecting scores.

- Committing 21 “real raw answers” into `tests/data/` risks permanently publishing users’ research questions and model outputs. Fix: use approved redacted/synthetic fixtures for the repository and keep any sensitive evaluation corpus access-controlled outside Git.

- Thirty pairwise comparisons have no defined ties, randomization, blinding, or minimum effect size; one changed comparison is a 3.3-point “improvement.” Fix: define ties and annotation presentation, then require a practically meaningful held-out improvement with uncertainty bounds.

- Measurable signals are readily gamed and are not evidence: fabricated costs, arbitrary dates, irrelevant unit strings, and unsupported thresholds all raise the proposed score. Fix: score numerical claims only when linked to a relevant mechanism, source, calculation, or internally consistent comparison—and include adversarial fabricated-number fixtures.

- “Language-independent” is overstated: decimal commas, localized currency/date formats, unit spelling, and multilingual tool/protocol names require language-aware parsing. Fix: specify supported locale formats and test equivalent German/English/mixed-language claims plus ambiguous dates.

- Per-framework weighting is hand-waving unless the scorer receives a reliable framework identity and each framework has enough independently judged examples to calibrate it. Fix: trace framework metadata through every scoring call and define per-framework evidence, defaults, and validation criteria before assigning differing weights.

- Step 8 is not last—Step 9 follows it—and enabling the gate before criterion-failure semantics are fixed can change production rankings or empty results on an exception. Fix: implement and test visible per-criterion failure handling first, run the new scorer in shadow mode, then enable it.

- R4’s “more than half” threshold is arbitrary and only reports a problem after the run has already produced degraded synthesis input. Fix: justify thresholds from baseline distributions and define a fail-safe outcome (halt/mark report invalid/no synthesis), surfaced in both CLI and web UI.

- §3C contains a concrete cost error: 66 additional scorer calls on a 66-call run doubles direct call count, not “~+50%.” Fix: correct the estimate and state how `cost_estimation.py` will account for optional judge calls/retries.

- `scoring_version` changes the run-result contract, but the plan does not identify its storage location or every reader of run outputs, reports, and the web UI. Fix: enumerate all producers/readers and add backward-compatible parsing and display tests.

- The plan’s required “real web run” can silently create paid calls, but it gives neither exact call count/cost nor a validated low-cost validation configuration. Fix: state the concrete validation-run size, expected cost, provider behavior, and update the estimate shown to users.

Unexamined because the supplied constraints prohibit file access: `main.py`, `evaluation_scoring.py`, `app.py`, `cost_estimation.py`, all run-output readers, and the actual raw-response corpus.

VERDICT: REVISE

### Claudes Antwort auf Runde 1

Elf Punkte, alle angenommen. Drei waren Fehler von mir, einer davon schwerwiegend.

**⛔ Der Datenschutzfehler.** Ich wollte 21 echte Rohantworten nach `tests/data/`
committen. Geprüft: die Dateien enthalten unter „Prompt Sent to Model" die **vollständige
Forschungsfrage**, und dieses Repo ist **öffentlich**. Das hätte die Fragen des Nutzers
veröffentlicht. Jetzt: im Repo ausschließlich synthetische, erfundene Texte; die echte
Menge bleibt außerhalb von git unter `.claudex-tmp/`; der Bericht nennt nur Kennzahlen.

**Die zentrale Behauptung war zu stark.** „Eine Referenzmenge macht die Änderung
widerlegbar" — nein. 30 Paare eines Beurteilers über ein Themenfeld belegen, dass man die
Vorlieben dieses Beurteilers getroffen hat. Zurückgenommen und ersetzt durch: Vorab-
Festschreibung aller Urteile **vor** der ersten Codezeile, Aufteilung 60/40 in Entwicklung
und Rückhalt, Rückhalt **einmal** am Ende gemessen, Ergebnis mit Wilson-Intervall — und
die ausdrückliche Feststellung, dass bei 30 Paaren kleine Gewinne **nicht nachweisbar**
sind. Fällt es so aus, ist das die Antwort, kein Anlass den Maßstab zu senken.

**Weitere angenommene Punkte**

| Befund | Was sich ändert |
| --- | --- |
| Messbare Signale sind durch erfundene Zahlen zu spielen | Der stärkste Einwand gegen Weg B. Gezählt wird jetzt nur eine **verankerte** Angabe — an Mechanismus, Quelle, Rechnung oder eine im Text konsistente Vergleichsgröße gebunden. Plus ausdrückliche Fälschungs-Fixtures. Grenze benannt: in sich stimmige Erfindungen bleiben ununterscheidbar. |
| „Sprachunabhängig" überzogen | Stimmt — Dezimalkomma, `84.000` gegen `84,000`, Datumsformate. Unterstützte Formate jetzt benannt (de-DE, en-US), gleichbedeutende Angaben werden gegeneinander geprüft. |
| Rahmenabhängige Gewichtung ist Handwedeln ohne Rahmen-Identität | Treffer: `score_text(text)` bekommt **nur Text**. Ohne diese Naht ist der Vorschlag unmöglich. Als eigener Schritt 7 aufgenommen. |
| §4 widersprach sich selbst (ein Thema gegen zwei Fragen) | Meiner. Jetzt zwei Fragestellungen, nach Rahmen geschichtet — und ausgewiesen, dass beide aus demselben Themenfeld stammen. |
| Schritt 8 war nicht der letzte, Schritt 9 folgte | Meiner. Reihenfolge neu: Fehlerbehandlung **zuerst**, Anschalten **zuletzt**. |
| Schattenbetrieb fehlt | Übernommen als Schritt 9 — neuer Bewerter läuft mit, Ergebnis nur protokolliert. Beantwortet die Frage, die sonst offenbliebe: weicht die Rangfolge auf echten Daten überhaupt ab? |
| R4s „mehr als die Hälfte" willkürlich, und zu spät | Grenze wird aus der gemessenen Verteilung abgeleitet; bleiben unter drei Antworten übrig, wird **keine Synthese erzeugt** und der Lauf als `completed_with_failures` ausgewiesen. |
| §3C: 66 Zusatzaufrufe sind +100 %, nicht +50 % | Rechenfehler von mir, korrigiert. |
| `scoring_version` ändert den Ergebnisvertrag | Fünf Leser namentlich aufgezählt, je ein Test. |
| Prüflauf ohne Budget | Beziffert: 11 Aufrufe, ~$0,12, zusammen unter $0,30, von Hand ausgelöst. |

**Keine Ablehnung.** Mehrere Beurteiler für die Referenzmenge wären methodisch richtig —
es gibt hier nur einen Menschen. Das steht in §7 als Grenze, nicht als gelöst.

---

## Runde 2 — Codex

- **Defect:** The holdout cannot be “unseen during the entire work” if the same person labels all 30 pairs before development; this leaks its content and preferences into implementation. **Fix:** have an independent custodian create, label, lock, and reveal the holdout only after the code freeze.

- **Defect:** The real reference set is neither committed nor protected merely because `.claudex-tmp/` is Git-ignored; it remains inside the checkout and can be altered or exposed outside Git. **Fix:** store it outside the repository in access-controlled storage and commit only a privacy-preserving, timestamped integrity commitment plus split metadata.

- **Defect:** Comparing the new scorer’s Wilson lower bound with the old scorer’s point estimate is not a valid before/after test: both scorers are evaluated on the same pairs, so outcomes are paired and the baseline also has uncertainty. **Fix:** preregister a paired comparison of the score difference, with a confidence interval or exact paired test, and require its lower bound to exceed zero.

- **Defect:** The framework plan is arithmetically incompatible with its split: 11 frameworks × two pairs requires 22 pairs, but the 60% development set of 30 has only 18. Using holdout labels to tune weights would invalidate it. **Fix:** enlarge the development set to meet the per-framework minimum before splitting, or defer framework-specific weights and use one fixed default.

- **Defect:** Anchoring moves gaming outward; an internally coherent invented calculation and invented citation satisfy the proposed criterion, while the fixtures only reject incoherent fabrications. Calling these “substantiated claims” overstates what is measured. **Fix:** define this feature as internal-specificity/consistency only, cap its influence, and include coherent-fabrication cases in acceptance tests.

- **Defect:** R4 still claims a data-derived threshold while its only operative threshold is the fixed “fewer than three” rule; three surviving answers can still be radically unrepresentative. **Fix:** preregister the distribution-derived disqualification-rate formula and a minimum framework/response coverage rule, then block synthesis when either fails.

- **Defect:** Shadow mode compares ranks but cannot reveal what cutover changes downstream: selected inputs, synthesis behavior, persisted result format, reader failures, or the visible `completed_with_failures` path. **Fix:** add an isolated end-to-end staging run that exercises the exact cutover output, synthesis/no-synthesis branch, readers, CLI, and web result route.

- **Defect:** Adding `scoring_version` only to new artifacts does not specify how existing runs without that field are read. **Fix:** define and test a legacy-version fallback for every named reader and for both `isee_result.*` and `combinations.csv`.

- **Completeness wish:** Only `CLAUDE.md` is named for documentation alignment despite a scoring-contract change. **Fix:** inventory and update the relevant README, German README, scoring-overhaul, and `docs/` explanations alongside the code.

Unexamined due to the stated file-access restriction: the scorer/call graph, result schemas, all five readers, CLI/web result routes, test infrastructure, and cost-estimation implementation.

VERDICT: REVISE

### Claudes Antwort auf Runde 2

Acht Punkte, alle angenommen. Zwei davon waren harte Fehler von mir.

| Befund | Was sich ändert |
| --- | --- |
| **Rechenfehler:** 11 Rahmen × 2 Paare = 22, verfügbar 18 | Nachgerechnet, stimmt. Die Forderung war unerfüllbar. **Rahmenabhängige Gewichtung entfällt** aus dem Vorhaben; einheitlicher Vorgabewert. Der Nachteil für zahlenlose Einsicht bleibt damit **offen** und wird als solcher geführt, statt mit einer Maßnahme zugedeckt, die die Daten nicht tragen. |
| **Statistischer Fehler:** Wilson-Intervall des neuen gegen Punktwert des alten Bewerters | Stimmt — beide werden auf denselben Paaren gemessen, das ist verbunden. Jetzt ein **gepaarter** Test (McNemar über `b − c`), Verbesserung nur bei unterer Grenze über null. |
| Der Rückhalt ist keiner, wenn derselbe Mensch alles vorab urteilt | Berechtigt und **nicht behebbar** — es gibt hier einen Menschen, keinen unabhängigen Verwahrer. Als Grenze ausgewiesen; gemildert durch Urteil **ohne Kenntnis von Modell und Rahmen** und dadurch, dass Rückhalt-Paare während der Arbeit nicht erneut geöffnet werden. |
| `.claudex-tmp/` ist kein Schutz | Stimmt, der Ordner liegt im Arbeitsverzeichnis. Die echte Menge liegt jetzt **außerhalb des Repos**; im Repo nur SHA-256 je Urteil, Aufteilung und Kennzahlen. |
| Verankerung verschiebt das Vortäuschen nur nach außen | Der Name „belegte Angaben" war zu stark. Heißt jetzt **innere Bestimmtheit und Widerspruchsfreiheit**, Anteil gedeckelt, und **stimmige Fälschungen kommen als Abnahmefall mit dem erwarteten Ergebnis „besteht"** — eine festgehaltene Grenze ist mehr wert als eine verschwiegene. |
| R4 behauptete eine abgeleitete Grenze, hatte aber nur „weniger als drei" | Jetzt zwei vorab festzuschreibende Regeln: Ausschussquote aus der gemessenen Verteilung **und** Mindestabdeckung (≥3 Rahmen, ≥2 Modelle). Bei Verletzung: **keine Synthese**, Lauf als `completed_with_failures`. |
| Schattenbetrieb zeigt nur Ränge | Lücke, die ich übersehen hatte. Neuer Schritt 10: **Generalprobe** in ein Wegwerf-Verzeichnis, die den Umschaltpfad wirklich durchläuft — Synthese, Keine-Synthese, alle Leser, CLI, Ergebnisroute. |
| `scoring_version` sagt nichts über Altläufe | Stimmt. Fehlt das Feld, gilt `legacy-pre-2026-09`; ungleiche Versionen werden beim Vergleich **angezeigt**. Je Leser ein Test **ohne** das Feld. |
| Doku nur `CLAUDE.md` | Angenommen: beide READMEs, der Scoring-Abschnitt, die Audit-Baseline und diese Plandatei. |

---

## Runde 3 — Codex

Yes—there are still correctness defects.

- **Defect:** §4a-2 stores the real corpus outside the repo, but §4c still says it lives under `.claudex-tmp/`; it also names two real research topics in a public plan. **Fix:** remove the stale §4c location and replace real-topic names with opaque identifiers.

- **Defect:** The committed SHA-256 “pair judgment” does not prove that the judgment remains bound to the same response texts unless the commitment includes stable response-content digests and labels. **Fix:** commit a privacy-preserving manifest binding pair IDs, split, response digests, and judgments.

- **Defect:** The plan correctly admits this is not a true holdout, but Acceptance 1 still claims the holdout remains unseen until the end. The sole annotator necessarily saw it while labeling. **Fix:** call it a locked confirmation subset, not a holdout, and remove confirmatory claims unless an independent custodian is used.

- **Defect:** §4b adopts a paired method, but Acceptance 2 still requires Wilson intervals; moreover, exact McNemar is a test on discordant pairs, not automatically an “exact binomial interval for `b − c`.” **Fix:** specify one valid paired effect interval/test and use that same preregistered criterion in §4b, Step 11, and Acceptance.

- **Defect:** R2 says its six low-number/high-substance pairs are handled in Step 8, but Step 8 now concerns `scoring_version`; the mitigation is not scheduled or accepted. **Fix:** add those cases to the development fixtures and acceptance criteria, or remove the claimed mitigation.

- **Defect:** A single data-driven general-probe run cannot exercise both the synthesis and no-synthesis branches: R4 makes them mutually exclusive. **Fix:** run two controlled end-to-end cases—one satisfying coverage and one deliberately violating it—and budget/specify their model-framework matrices.

- **Defect:** “Median plus two dispersions” is not an implementable preregistered threshold without defining the observation unit, dispersion statistic, and handling of values outside 0–100%. **Fix:** define the exact statistic, sample, clamping, and boundary comparison before implementation.

The anchored-quantity measure is now sound only as a capped internal-consistency signal, not a truth test; the plan states that limit adequately. Shadow mode’s limits are also now correctly identified, but the general-probe design above still fails to test both outcomes.

Unexamined due to the stated restriction: scoring implementation, result schemas, test runner, reader call paths, CLI/web routes, and documentation files.

VERDICT: REVISE

### Claudes Antwort auf Runde 3

Sieben Defekte, alle angenommen — und **alle sieben waren Trümmer meiner eigenen
Überarbeitungen**: veraltete Verweise, umnummerierte Schritte und Abnahmekriterien, die dem
widersprachen, was ich weiter oben geändert hatte. Das ist die Klasse Fehler, die man beim
eigenen Text nicht sieht, weil man die letzte Fassung im Kopf hat und nicht die auf dem
Papier.

| Befund | Was sich ändert |
| --- | --- |
| §4c nannte weiter `.claudex-tmp/` und **die echten Forschungsthemen im Klartext** | Zweiter Datenschutzfund derselben Art in dieser Prüfung. Themen jetzt nur als `Q1`/`Q2`; der veraltete Ort ist weg. |
| Ein Hash des Urteils bindet das Urteil an nichts | Stimmt. Jetzt ein **Integritäts-Verzeichnis**: Paar-Kennung, Zugehörigkeit, **SHA-256 beider Antworttexte**, Urteil, Zeitstempel. |
| Abnahme 1 behauptete weiter, die Rückhalt-Menge sei ungesehen | Widerspruch zu §4a, den ich stehengelassen hatte. Heißt jetzt durchgängig **Bestätigungsmenge** — sie bestätigt, sie belegt nicht. |
| Abnahme 2 verlangte weiter Wilson, obwohl §4b auf gepaart umgestellt war | Ebenfalls meiner. Und meine McNemar-Beschreibung war unpräzise. Jetzt **ein** Kriterium, überall dasselbe: `b/(b+c)` gegen 0,5, exaktes Clopper-Pearson-Intervall, `b+c=0` heißt unentscheidbar. |
| R2 verwies auf „Schritt 8", der inzwischen `scoring_version` ist | Die Maßnahme hing an nichts. Jetzt eigenes Abnahmekriterium. |
| Eine Generalprobe kann nicht beide Zweige prüfen — sie schließen einander aus | Offensichtlich, sobald man es liest. Geteilt in **10a** (Abdeckung erfüllt, Synthese, bezahlt) und **10b** (erzwungene Verletzung, keine Synthese, gefälschter Transport, kostenlos). |
| „Median plus zwei Streuungen" ist keine umsetzbare Vorschrift | Stimmt. Jetzt exakt: Beobachtungseinheit Lauf, Median + 2 × mittlere absolute Abweichung, auf `[0,1]` beschnitten, strikt größer — und der Hinweis, dass sie bei zwei Läufen schwach belegt ist und nach fünf neu bestimmt wird. |

---

## Abschluss: drei Runden, **kein** APPROVED

Der Durchgang endet auf `REVISE`. Das wird nicht als Zustimmung ausgegeben.

**Einordnung:** keine Pattsituation — ich habe alle 26 Befunde aus drei Runden angenommen.
Aber: **die eingearbeitete Fassung wurde nicht erneut geprüft.** Ob die sieben Korrekturen
der letzten Runde tragen, ist ungeprüfte Behauptung von mir, und der Verlauf legt nahe,
dass eine vierte Runde wieder Trümmer der dritten fände.

**Von Codex ausdrücklich als tragfähig bestätigt** (Runde 3, vorletzter Absatz): das
Bestimmtheitsmaß als gedeckeltes Konsistenzsignal — *nicht* als Wahrheitsprüfung —, und
die benannten Grenzen des Schattenbetriebs.

**Restrisiko:**

1. ⚠️ Codex hat in **keiner** Runde eine Repo-Datei gelesen; sein Sandbox weist unter
   Windows jeden Zugriff ab. Geprüft wurde der Plantext plus die eingebetteten Messungen.
2. Alle Zahlen im Plan stammen aus **meinen** Messungen. Sie sind mit Datei und Zeile
   belegt, aber niemand hat sie unabhängig nachgerechnet.
3. Nicht geöffnet: `evaluation_scoring.py` selbst, `main.py`, die fünf Leser, die
   Ergebnisrouten, die Testinfrastruktur.
4. Die sieben Korrekturen aus Runde 3 sind ungeprüft.

**Empfehlung:** Der Plan ist umsetzbar — aber sein wertvollster Teil ist Schritt 1 und 2
(Fehlersichtbarkeit, Referenzmenge), und die stehen **vor** jeder Codeänderung am Bewerter.
Wer dort anfängt, kann nach Schritt 3 mit einer gemessenen Zahl in der Hand neu
entscheiden, ob sich der Rest lohnt.
