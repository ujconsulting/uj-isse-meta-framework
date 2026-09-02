# ISEE Meta Framework

**Die Idea Synthesis and Extraction Engine • Plattform für systematische Mehrperspektiven-Forschung**

[![Lizenz: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

> Deutsche Fassung von [README.md](README.md). Bei Abweichungen gilt das englische Original,
> weil dort zuerst gepflegt wird.

---

## 🚀 Schnellstart

```bash
# 1. Klonen und einrichten
git clone https://github.com/ujconsulting/uj-isse-meta-framework.git
cd uj-isse-meta-framework
pip install -r requirements.txt

# 2. API-Zugang konfigurieren
cp .env.template .env
# In .env den OpenRouter-Schlüssel eintragen

# 3. Server starten
./scripts/dev-server.sh start

# 4. Browser öffnen
http://localhost:5001/isee-ui

# 5. Nach der Analyse
# Die Ergebnisse liegen als isee_result.md im Lauf-Verzeichnis unter data/output/
```

Das war's. Die Oberfläche startet mit 14 kuratierten Modellen und 11 kognitiven Rahmen.
Die Sprache wählen Sie oben rechts (`EN | DE`); beim ersten Besuch entscheidet die
Sprache Ihres Browsers.

---

## 📖 Was ist ISEE?

Statt eine KI einmal zu fragen und die Antwort hinzunehmen, führt ISEE dieselbe Frage
**systematisch durch viele Denkweisen**: verschiedene Modelle, verschiedene kognitive
Rahmen, verschiedene Wissensdomänen. Interessant ist dabei weniger der Konsens als das,
was zwischen den Perspektiven sichtbar wird.

**Herkömmlich:** Frage → Antwort → man nimmt die blinden Flecken des einen Modells mit.
**ISEE:** Frage → **66 Perspektiven systematisch durchgehen** → Erkenntnisse, nach denen
man nicht gesucht hätte.

### Warum kognitive Vielfalt

Komplexe Probleme widersetzen sich einfachen Antworten, und die tragfähigen Einsichten
entstehen oft dort, wo sich widersprechende Perspektiven berühren. ISEE ist als
**Versicherung gegen die Beschränkungen einer einzigen Sichtweise** gedacht — gegen die
eines einzelnen Modells ebenso wie gegen den zu schnellen Konsens.

---

## 🎯 Wie ISEE arbeitet

### Architektur

**🧠 14 Modelle aus 14 verschiedenen Häusern**
Anthropic, OpenAI, Google, xAI, DeepSeek, Alibaba, Zhipu, Moonshot, Mistral, Meta,
NVIDIA, MiniMax, Upstage und Tencent — je eines. Die Vielfalt der *Häuser* ist der Zweck;
vierzehn Varianten derselben Modellfamilie würden ihn verfehlen. Modell-IDs und Preise
sind gegen den Live-Katalog von OpenRouter geprüft und in `openrouter_config.json`
hinterlegt.

**🔍 11 kognitive Rahmen**
Von analytischer Strenge bis zur gegenläufigen Dekonstruktion.

**📊 Dynamische Wissensdomänen**
Die relevanten Fachgebiete werden aus der Frage abgeleitet, nicht fest vorgegeben.

**⚡ Automatische Synthese**
Clusterbasierte Zusammenführung, die Ergänzendes, Widersprüchliches und Neues
auseinanderhält.

### Ablauf

1. **Frage eingeben** — Forschungsfrage oder komplexes Problem.
2. **„Vollanalyse starten"** — keine Parameter nötig.
3. **Fortschritt verfolgen** — live über alle 66 Kombinationen aus Modell, Rahmen und
   Domäne. Fehlgeschlagene Aufrufe werden **als Fehlschläge gemeldet**, nie durch eine
   plausibel aussehende Ersatzantwort verdeckt.
4. **Ergebnisse sichten** — geordnete Befunde, Bewertung, Berichte.
5. **Ansehen oder herunterladen** — mehrere Formate.

---

## 🎨 Die Oberfläche

### Gestaltung
- Ruhige, akademisch orientierte Darstellung
- Fortschritt in Echtzeit, nach kognitiven Rahmen aufgeschlüsselt
- Bewusst schlicht: Frage eingeben, starten
- 14 Modelle vorkonfiguriert, davon 8 in der kuratierten Standardauswahl
- **Deutsch und Englisch**, umschaltbar im Kopf und pro Browser gemerkt

### Was ein Lauf bedeutet
- **66 systematische Aufrufe** über alle Modelle und Rahmen
- **~4 Minuten** für die Vollanalyse, **~1 Minute** für die Validierung mit 11 Aufrufen
- **~$0,31 pro Vollanalyse, ~$0,05 pro Validierung** — aus abgerechneten Token gemessen,
  nicht geschätzt

### Weitere Eigenschaften
- **Kosten je Modell, je Haus und gesamt** nach jedem Lauf, samt Restguthaben
- **Ein API-Schlüssel** (OpenRouter) erreicht alle vierzehn Häuser
- Domänen werden aus dem Kontext der Frage erzeugt
- Mehrere Ergebnisformate, direkt ansehen oder herunterladen

---

## 🛠️ Installation

### Voraussetzungen
- Python 3.8 oder neuer
- OpenRouter-API-Schlüssel (ein Schlüssel für alle konfigurierten Modelle)
- Git

### Schritt für Schritt

```bash
git clone https://github.com/ujconsulting/uj-isse-meta-framework.git
cd uj-isse-meta-framework
pip install -r requirements.txt
cp .env.template .env
```

In `.env` eintragen:

```bash
OPENROUTER_API_KEY=ihr_openrouter_schluessel
```

Schlüssel anlegen: [https://openrouter.ai/keys](https://openrouter.ai/keys)

### Starten

```bash
./scripts/dev-server.sh start   # empfohlen
python app.py                   # oder direkt
```

Oberfläche: http://localhost:5001/isee-ui

⚠️ **Globant Enterprise AI** ist im Code vorgesehen, aber nicht selbst zugänglich: Es gibt
keine Selbstregistrierung und keine öffentliche Preisliste, der Zugang läuft über den
Vertrieb. Ohne Zugangsdaten bricht `--provider globant` mit einer klaren Meldung ab,
statt später in Authentifizierungsfehlern zu enden. Nutzen Sie `--provider openrouter`.

---

## 📋 Nutzung

### Grundlagen

1. http://localhost:5001/isee-ui öffnen
2. Frage eingeben
3. **„Vollanalyse starten"** — 66 Aufrufe, keine Konfiguration nötig
4. Fortschritt live verfolgen
5. Ergebnisse ansehen oder herunterladen

Vor der Vollanalyse lohnt **„Frage validieren"**: 11 gezielte Aufrufe für ~$0,05, um zu
sehen, ob die Frage trägt.

### Kognitive Rahmen

Analytisch, Kreativ, Kritisch, Integrativ, Pragmatisch, Erste Prinzipien, Systemisch,
Gegenläufig, Historisch, Zukunftsgerichtet, Disruptiv.

### Serververwaltung

```bash
./scripts/dev-server.sh start    # starten
./scripts/dev-server.sh status   # Status und letzte Logzeilen
./scripts/dev-server.sh restart  # neu starten
./scripts/dev-server.sh logs     # Logs live verfolgen
./scripts/dev-server.sh stop     # beenden
```

---

## 📥 An die Ergebnisse kommen

Die zentrale Datei ist **`isee_result.md`**. Drei Wege führen dorthin:

**1. Schnell ansehen** — Schaltfläche „Analyse ansehen (schnell)". Öffnet
`isee_result.md` formatiert in einem neuen Tab. Kein Download nötig.

**2. Komplettpaket herunterladen** — Schaltfläche „Komplettpaket herunterladen". ZIP mit
`isee_result.md`, dem vollständigen Abfrageprotokoll (`queries_detailed_*.csv`), den
Rohdaten und allen Begleitdateien.

**3. Direkt im Dateisystem** — unter `data/output/run_JJJJMMTT_HHMMSS/`:

```
data/output/run_JJJJMMTT_HHMMSS/
├── isee_result.md              # ← die Hauptdatei
├── queries_detailed_*.csv      # vollständiges Abfrageprotokoll
├── raw_responses/              # alle erfolgreichen Einzelantworten
├── failed_responses/           # fehlgeschlagene Aufrufe samt HTTP-Status
└── analysis.md                 # Auswertung
```

`failed_responses/` gibt es nur, wenn tatsächlich etwas fehlgeschlagen ist — und
Fehlschläge landen **nie** in `raw_responses/`, weil sie sonst als Antworten bewertet und
gerankt würden.

---

## 🔎 Ehrlich von Haus aus

Drei Verhaltensweisen dieses Forks gibt es, weil ihr Fehlen echte Arbeit gekostet hat.

**Ein fehlgeschlagener Aufruf wird als Fehlschlag gemeldet.** Früher gab jeder Zweig, der
ein Modell nicht erreichte, eine *simulierte* Antwort zurück — ein Lauf, in dem alle 66
Aufrufe mit HTTP 400 scheiterten, erzeugte einen vollständigen, plausiblen, vollständig
erfundenen Bericht und meldete Erfolg. Fehlschläge werden jetzt mit Modell, HTTP-Status
und Fehlertext festgehalten, nach `failed_responses/` geschrieben, von der Bewertung
ausgenommen und in der Zusammenfassung gezählt. Der Exit-Code sagt, was war: `0` alles
erfolgreich, `1` teilweise gescheitert, `2` nichts hat funktioniert.

**Kosten werden abgerechnet, nicht geschätzt.** Nach jedem Lauf:

```
  Model                      calls        in       out       USD
  GPT-5.6 Luna                   3       344     6,265    0.0076
  TOTAL                          3                        0.0076

  By house (the vendor behind the model, not the gateway):
    openai                   1 model(s)    3 calls     0.0076  100.0%

  OpenRouter balance: $18.11 remaining ($113.37 used of $131.48)
```

Die Token-Zahlen stammen aus OpenRouters eigenem `usage`-Block, die Preise aus dem
`pricing`-Eintrag des jeweiligen Modells in `openrouter_config.json`. Ein Modell ohne
hinterlegten Preis wird als *unpriced* ausgewiesen und aus der Summe herausgehalten,
statt stillschweigend einen Standardwert zu bekommen. Erneut ausgeben:
`python run_cost_report.py <lauf-verzeichnis>`, ohne Argument nur das Restguthaben.

**Schätzungen sind überprüfbar.** Vorab-Schätzung und tatsächliche Rechnung stehen beide
da, damit die Prognose an der Wirklichkeit gemessen werden kann statt ungeprüft zu
bleiben. Das ist kein akademischer Punkt: Die frühere Schätzung war eine Konstante von
$0,08 je Kombination, unabhängig von den konfigurierten Modellen — sie überzeichnete
einen Volllauf um das Siebzehnfache.

---

## 🌍 Sprache der Oberfläche

Deutsch und Englisch, umschaltbar im Kopf (`EN | DE`). Die Wahl wird im Browser gemerkt;
beim ersten Besuch entscheidet dessen Spracheinstellung.

Nicht übersetzt sind der Cognitive Diversity Explorer, `/docs`, `/about` und die
Meldungen, die das Backend erzeugt. Das sind eigene Oberflächen.

---

## 🔧 Konfiguration

- **`openrouter_config.json`** — Modelle, Parameter und hinterlegte Preise. Ein
  OpenRouter-Schlüssel genügt; die Auswahl ist auf kognitive Vielfalt hin kuratiert,
  damit niemand über Modellwahl nachdenken muss.
- **`.env`** — Umgebungsvariablen und Schlüssel. Gitignoriert.

### Skripte

- `scripts/dev-server.sh` — Server starten, stoppen, neu starten, Status, Logs
- `scripts/check-ports.sh` — Portkonflikte finden
- `scripts/kill-port.sh` / `kill-dev-ports.sh` — Ports freiräumen
- `scripts/dev-aliases.sh` / `install-aliases.sh` — Kurzbefehle

### Protokolle

`isee-ui.log` (Anwendung) und `dev-server.log` (Serververwaltung), beide gitignoriert.

---

## 🎯 Für wen ISEE gedacht ist

**Forschung und Wissenschaft** — für vielschichtige Fragen, bei denen Annahmen geprüft
und Perspektiven zusammengeführt werden müssen.

**Strategische Entscheidungen** — wo unbeabsichtigte Folgen und alternative Deutungen
mitgedacht werden müssen, bevor entschieden wird.

**Innovationsarbeit** — wo der Durchbruch aus dem Zusammenstoß von Denkweisen kommt und
nicht aus linearem Weiterdenken.

---

## 💡 Beispielfragen

**Forschung**
*„Was hemmt die Verbreitung von Wärmepumpen in älteren deutschen Mehrfamilienhäusern —
technisch, wirtschaftlich, rechtlich und im Zusammenspiel der Eigentümergemeinschaft?"*

**Strategie**
*„Wie sollten mittelständische Unternehmen KI einführen, um Produktivität und
Entscheidungsqualität zu heben, ohne Belegschaft zu verdrängen oder die eigene Kultur zu
beschädigen?"*

**Querschnitt**
*„Was ließe sich aus der Bewirtschaftung von Ökosystemen für die Gestaltung dezentraler
Betreibergemeinschaften lernen, wo langfristiges Denken und wechselseitige Abhängigkeit
Netzwerke tragfähig machen?"*

Jede Frage öffnet mehrere Erkenntniscluster — mehr, als eine einzelne Perspektive
sichtbar machen könnte.

---

## 🔍 Technischer Aufbau

**Steuerung**
- `main.py` (3.473 Zeilen) — Ausführungsmaschine und CLI
- `app.py` (3.031 Zeilen) — Flask-Weboberfläche und REST-API

**KI-Anbindung**
- `model_api_integration.py` — Provider-Gateway. Sendet nur die Sampling-Parameter, die
  ein Modell tatsächlich akzeptiert, und führt bei jedem Fehler den HTTP-Status mit.
- `openrouter_rankings_service.py` — nur Ranking-Metadaten. **Keine** Modellquelle: was
  existiert, entscheidet die Konfiguration; Rankings reichern sie lediglich an.

**Kognitive Vielfalt**
- `cognitive_framework_visualizer.py` (379 Zeilen) — verwaltet die 11 Rahmen
- `domain_manager.py` (410 Zeilen) — Wissensdomänen

**Auswertung**
- `reporting.py` (1.056 Zeilen) — Synthese und Berichte
- `cost_estimation.py` (958 Zeilen) — Vorab-Schätzung, aus den je Modell hinterlegten
  Preisen gerechnet
- `run_cost_report.py` — was ein Lauf tatsächlich gekostet hat, aus abgerechneten Token
- `performance_tracker.py` (413 Zeilen) — SQLite-gestützte Laufhistorie

---

## 🚀 Entwicklung

```bash
./scripts/dev-server.sh start    # Server starten
./scripts/dev-server.sh logs     # Logs live
./scripts/dev-server.sh status   # Status
./scripts/dev-server.sh stop     # beenden

python -m pytest tests/ -q       # Tests
```

⚠️ Der Flask-Auto-Reloader ist **absichtlich aus**. Der Laufstatus liegt im
Prozessspeicher, und Analysen laufen minutenlang als Kindprozesse — ein Neustart mitten
im Lauf verwaist den Kindprozess, und der Status ist unwiederbringlich weg. Wer ihn
braucht: `ISEE_FLASK_DEBUG=1`.

### Verzeichnisse

```
uj-isse-meta-framework/
├── isee-ui.html              # Weboberfläche (inkl. EN/DE-Schalter)
├── app.py                    # Flask-Backend
├── main.py                   # Kernlogik
├── openrouter_config.json    # Modelle, Parameter, hinterlegte Preise
├── run_cost_report.py        # tatsächliche Kosten eines Laufs
├── requirements.txt          # Abhängigkeiten
├── scripts/                  # Werkzeuge
├── tests/                    # Testsuite
├── docs/                     # Dokumentation und Pläne
├── data/                     # Ausgaben und Verlauf
└── archive/                  # Altstände
```

---

## 📄 Lizenz

Lizenziert unter der **Apache License, Version 2.0** — vollständiger Text in
[LICENSE](LICENSE), sonst <https://www.apache.org/licenses/LICENSE-2.0>.

> **Hinweis zu einer vom Original geerbten Unstimmigkeit:** Das ursprüngliche README nannte
> die MIT-Lizenz, während die `LICENSE`-Datei Apache-2.0 anführte — und diese Datei
> enthielt nur den Apache-Anhang, nicht den Lizenztext selbst. Dieser Fork löst den
> Widerspruch zugunsten der `LICENSE`-Datei auf, die der maßgebliche Rechtsakt ist, und
> liefert den vollständigen Apache-2.0-Text mit, wie es Abschnitt 4(a) verlangt. Die
> ursprüngliche Copyright-Zeile bleibt unverändert. Eine Umlizenzierung ist weder
> beabsichtigt noch behauptet.

---

## 🍴 Zu diesem Fork

Dieses Repository ist ein Fork von
**[joseph-fajen/ISEE_Meta_Framework](https://github.com/joseph-fajen/ISEE_Meta_Framework)**,
gepflegt von UJ Consulting für den internen Forschungseinsatz.

Ursprüngliches Werk: Copyright 2025 **Joseph Fajen**, lizenziert unter Apache-2.0. Alle
Copyright-, Zuschreibungs- und Lizenzhinweise des Originals bleiben erhalten.

Die Liste der in diesem Fork geänderten Dateien steht im englischen
[README.md](README.md#-about-this-fork) (Hinweis nach Apache-2.0 §4(b)).

Das Original trägt keine Verantwortung für diese Änderungen und befürwortet sie nicht.

---

## 🏗️ Ursprünglich entwickelt von

**Joseph Fajen** — Senior Technical Writer bei IOHK. Entwickelt mit Claude Code.

---

## 🌟 Der Gedanke dahinter

ISEE verschiebt den Anspruch vom **Abrufen von Informationen** zur **Archäologie der
Perspektiven**: das kognitive Gelände um eine schwierige Frage systematisch freilegen.
Gedacht für die Momente, in denen weder eine Expertenantwort noch schnelle Einigkeit
weiterhilft — wenn man Perspektiven braucht, die man selbst nicht hätte formulieren
können, und Annahmen findet, von denen man nicht wusste, dass man sie hat.
