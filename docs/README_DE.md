# ISEE Meta Framework Dokumentation

**Deutsch** · [English](README.md)

*Zuletzt aktualisiert: 17. Juli 2025*

Willkommen zur Dokumentation des ISEE Meta Frameworks. Dieser Leitfaden hilft Ihnen, sich in unserer umfassenden Dokumentation zurechtzufinden, die nach Themen und Nutzerwegen gegliedert ist.

## 🚀 Schnellstart

**Neu bei ISEE?** Beginnen Sie hier:

1. **[Schnellstart-Anleitung](getting-started/QUICKSTART.md)** - In 5 Minuten startklar
2. **[Warum ISEE?](getting-started/WHY_ISEE.md)** - Philosophie und Ansatz verstehen
3. **[Beispiele für Anwendungsfälle](getting-started/EXAMPLE_USE_CASES.md)** - ISEE in der Praxis erleben

**Web-UI-Nutzer** (empfohlen): Rufen Sie http://localhost:5001/isee-ui auf, nachdem Sie `./scripts/dev-server.sh start` ausgeführt haben

**CLI-Nutzer**: Springen Sie zum [Konfigurationsleitfaden](configuration/CONFIG_GUIDE.md) für die OpenRouter-Einrichtung

## 📚 Aufbau der Dokumentation

### 🌱 Erste Schritte
*Ideal für neue Nutzer und die Einarbeitung*

| Dokument | Beschreibung | Lesezeit |
|----------|-------------|----------|
| [**QUICKSTART.md**](getting-started/QUICKSTART.md) | Schnellstart-Anleitung mit Web-UI im Mittelpunkt | 5 Min. |
| [**WHY_ISEE.md**](getting-started/WHY_ISEE.md) | Philosophie und Nutzenversprechen | 3 Min. |
| [**EXAMPLE_USE_CASES.md**](getting-started/EXAMPLE_USE_CASES.md) | Praxisnahe Anwendungen und Beispiele | 10 Min. |

### ⚙️ Konfiguration
*Anleitungen zu Einrichtung und Anpassung*

| Dokument | Beschreibung | Einsatzzweck |
|----------|-------------|--------------|
| [**CONFIG_GUIDE.md**](configuration/CONFIG_GUIDE.md) | Vollständige Konfiguration im OpenRouter-Zeitalter | Alle Nutzer |
| [**OPENROUTER_INTEGRATION_SUMMARY.md**](configuration/OPENROUTER_INTEGRATION_SUMMARY.md) | Details zur OpenRouter-Integration | Entwickler |

### 🚀 Erweiterte Funktionen
*Möglichkeiten für Power-User und Forschungswerkzeuge*

| Dokument | Beschreibung | Zielgruppe |
|----------|-------------|------------|
| [**REPORTING_GUIDE.md**](advanced/REPORTING_GUIDE.md) | Analyse, CSV-Exporte, Visualisierungen | Forschende |
| [**ISEE_Scoring_and_Filtering_Process.md**](advanced/ISEE_Scoring_and_Filtering_Process.md) | Vollständige Bewertungsmethodik | Wissenschaftler |
| [**isee-sampling-algorithm.md**](advanced/isee-sampling-algorithm.md) | Details zur fairen geschichteten Stichprobenziehung | Forschende |
| [**isee-idea-selection-process.md**](advanced/isee-idea-selection-process.md) | Synthese- und Auswahlprozess | Technische Nutzer |
| [**ANALYSIS_AND_OPTIMIZATION.md**](advanced/ANALYSIS_AND_OPTIMIZATION.md) | System zur Selbstanalyse und Optimierung | Alle Nutzer |
| [**performance_tracking_database.md**](advanced/performance_tracking_database.md) | System zur Leistungsanalyse | Datenanalysten |
| [**session-handoff-procedure-short.md**](advanced/session-handoff-procedure-short.md) | Bewährte Vorgehensweisen für die Sitzungsverwaltung | Alle Nutzer |
| [**next-session-startup.md**](advanced/next-session-startup.md) | Hinweise zur Sitzungskontinuität | Regelmäßige Nutzer |

### 🛠️ Entwicklung
*Technische Architektur und Entwicklungsressourcen*

| Dokument | Beschreibung | Zielgruppe |
|----------|-------------|------------|
| [**SYSTEM_OVERVIEW.md**](development/SYSTEM_OVERVIEW.md) | Architekturüberblick auf hoher Ebene | Entwickler |
| [**DATA_STRUCTURE.md**](development/DATA_STRUCTURE.md) | Datenmodelle und -strukturen | Entwickler |
| [**ui-rethinking/**](development/ui-rethinking/) | UI/UX-Designspezifikationen | Designer/Entwickler |

### 📦 Archiv
*Historische und veraltete Dokumentation*

| Ordner | Beschreibung | Zweck |
|--------|-------------|-------|
| [**archive/deprecated/**](archive/deprecated/) | Dokumentation aus der CLI-Zeit | Historische Referenz |
| [**archive/historical/**](archive/historical/) | Entwicklungsgeschichte | Kontext und Entwicklung |

## 🎯 Leitfäden nach Nutzerweg

### 👤 Für Erstnutzer

1. **Das Konzept verstehen**: [Warum ISEE?](getting-started/WHY_ISEE.md)
2. **Schnell loslegen**: [Schnellstart-Anleitung](getting-started/QUICKSTART.md)
3. **Es in Aktion sehen**: [Beispiele für Anwendungsfälle](getting-started/EXAMPLE_USE_CASES.md)
4. **Die eigene Umgebung konfigurieren**: [Konfigurationsleitfaden](configuration/CONFIG_GUIDE.md)

### 🔬 Für Forschende

1. **Schnellstart**: [Schnellstart-Anleitung](getting-started/QUICKSTART.md)
2. **Die Methodik verstehen**: [Bewertungs- und Filterprozess](advanced/ISEE_Scoring_and_Filtering_Process.md)
3. **Die Analysewerkzeuge kennenlernen**: [Berichtsleitfaden](advanced/REPORTING_GUIDE.md)
4. **Die Selbstanalyse entdecken**: [Analyse und Optimierung](advanced/ANALYSIS_AND_OPTIMIZATION.md)
5. **Erweiterte Funktionen meistern**: [Stichprobenalgorithmus](advanced/isee-sampling-algorithm.md)

### 💻 Für Entwickler

1. **Systemarchitektur**: [Systemüberblick](development/SYSTEM_OVERVIEW.md)
2. **Datenmodelle**: [Datenstruktur](development/DATA_STRUCTURE.md)
3. **Konfigurationssystem**: [Konfigurationsleitfaden](configuration/CONFIG_GUIDE.md)
4. **UI-Entwicklung**: [UI Rethinking](development/ui-rethinking/)

### 📊 Für Datenanalysten

1. **Mit den Grundlagen beginnen**: [Schnellstart-Anleitung](getting-started/QUICKSTART.md)
2. **Export und Analyse**: [Berichtsleitfaden](advanced/REPORTING_GUIDE.md)
3. **Möglichkeiten der Selbstanalyse**: [Analyse und Optimierung](advanced/ANALYSIS_AND_OPTIMIZATION.md)
4. **Leistungsverfolgung**: [Leistungsdatenbank](advanced/performance_tracking_database.md)
5. **Die Algorithmen verstehen**: [Stichprobenziehung](advanced/isee-sampling-algorithm.md) & [Auswahl](advanced/isee-idea-selection-process.md)

## 🔧 Häufige Aufgaben

### Aufgaben für den Einstieg

| Aufgabe | Dokumentation |
|---------|---------------|
| ISEE installieren und starten | [Schnellstart → Einrichtung](getting-started/QUICKSTART.md#setup-and-launch) |
| OpenRouter-API-Schlüssel einrichten | [Konfigurationsleitfaden → Schnelleinrichtung](configuration/CONFIG_GUIDE.md#quick-setup-recommended) |
| Die erste Analyse durchführen | [Schnellstart → Erste Analyse](getting-started/QUICKSTART.md#your-first-analysis) |
| Das Ergebnisformat verstehen | [Schnellstart → Ergebnisse verstehen](getting-started/QUICKSTART.md#understanding-results) |

### Konfigurationsaufgaben

| Aufgabe | Dokumentation |
|---------|---------------|
| API-Schlüssel konfigurieren | [Konfigurationsleitfaden → Verwaltung von API-Schlüsseln](configuration/CONFIG_GUIDE.md#api-key-management) |
| Modelle und Frameworks auswählen | [Konfigurationsleitfaden → Modellauswahl](configuration/CONFIG_GUIDE.md#model-selection) |
| Eigene Konfigurationen erstellen | [Konfigurationsleitfaden → Erweiterte Konfiguration](configuration/CONFIG_GUIDE.md#advanced-configuration) |
| Konfigurationsprobleme beheben | [Konfigurationsleitfaden → Fehlerbehebung](configuration/CONFIG_GUIDE.md#troubleshooting-configuration) |

### Analyseaufgaben

| Aufgabe | Dokumentation |
|---------|---------------|
| Umfassende Berichte erzeugen | [Berichtsleitfaden → Analysebericht](advanced/REPORTING_GUIDE.md#analysis-report) |
| Daten für die Analyse exportieren | [Berichtsleitfaden → CSV-Datenexporte](advanced/REPORTING_GUIDE.md#csv-data-export-details) |
| Die Bewertungsmethodik verstehen | [Bewertungsprozess → Überblick](advanced/ISEE_Scoring_and_Filtering_Process.md#overview-the-complete-pipeline) |
| Systemleistung analysieren und optimieren | [Analyse und Optimierung → Schnellstart](advanced/ANALYSIS_AND_OPTIMIZATION.md#quick-start) |
| Leistung im Zeitverlauf verfolgen | [Leistungsdatenbank](advanced/performance_tracking_database.md) |

### Fortgeschrittene Aufgaben

| Aufgabe | Dokumentation |
|---------|---------------|
| Den Stichprobenalgorithmus verstehen | [Stichprobenalgorithmus](advanced/isee-sampling-algorithm.md) |
| Die Synthesemethodik kennenlernen | [Ideenauswahlprozess](advanced/isee-idea-selection-process.md) |
| Sitzungen wirksam verwalten | [Sitzungsübergabe](advanced/session-handoff-procedure-short.md) |
| Zur Entwicklung beitragen | [UI Rethinking](development/ui-rethinking/) |

## 🆕 Neuigkeiten

### Dokumentationsupdates Juli 2025

- **✅ Web-UI-first-Ansatz**: Alle Leitfäden wurden auf den Web-UI-Hauptworkflow umgestellt
- **✅ OpenRouter-Zeitalter**: Die Konfigurationsleitfäden spiegeln die aktuelle OpenRouter-Integration wider
- **✅ Neue Struktur**: Themenbasierte Gliederung ersetzt die chronologische Struktur
- **✅ Umfassender Bewertungsleitfaden**: Neue, ausführliche Dokumentation der Methodik
- **✅ Verschlankte Navigation**: Klare Nutzerwege für unterschiedliche Zielgruppen

### Neuerungen

- **[ISEE_Scoring_and_Filtering_Process.md](advanced/ISEE_Scoring_and_Filtering_Process.md)**: Vollständiger Methodikleitfaden für Kolleginnen und Kollegen
- **Aktualisierter [CONFIG_GUIDE.md](configuration/CONFIG_GUIDE.md)**: Berücksichtigt den aktuellen OpenRouter-first-Ansatz
- **Aktualisierter [QUICKSTART.md](getting-started/QUICKSTART.md)**: Einstieg mit Web-UI im Mittelpunkt

## 📖 Dokumentationsstandards

### Inhaltliche Grundsätze

- **Nutzer zuerst**: Gegliedert nach den Bedürfnissen der Nutzer, nicht nach der technischen Struktur
- **Aktueller Fokus**: Spiegelt das ISEE der Web-UI-first- und OpenRouter-Ära wider
- **Umfassende Abdeckung**: Vom Schnellstart bis zur fortgeschrittenen Forschungsmethodik
- **Klare Navigation**: Mehrere Wege je nach Nutzertyp und Zielen

### Hinweise zur Pflege

- **Regelmäßige Updates**: Die Dokumentation wird mit der Weiterentwicklung des Systems aktuell gehalten
- **Archivierungsrichtlinie**: Veraltete Inhalte werden mit klarer Erläuterung ins Archiv verschoben
- **Zeitstempel-Richtlinie**: Alle wichtigen Dokumente enthalten das Datum der letzten Aktualisierung
- **Querverweise**: Umfangreiche Verlinkung zwischen zusammenhängenden Konzepten

## 🆘 Hilfe erhalten

### Probleme mit der Dokumentation

- **Fehlende Informationen**: Sehen Sie im [Archiv](archive/) nach historischen Inhalten
- **Veraltete Inhalte**: Achten Sie auf die Zeitstempel „Last updated“; neuer ist besser
- **Konfigurationsprobleme**: Beginnen Sie mit dem [Abschnitt zur Fehlerbehebung](configuration/CONFIG_GUIDE.md#troubleshooting-configuration)

### Technischer Support

- **Kleinere Probleme**: Siehe die [Fehlerbehebung im Schnellstart](getting-started/QUICKSTART.md#troubleshooting)
- **Hilfe zur Konfiguration**: Ausführliche Hinweise im [Konfigurationsleitfaden](configuration/CONFIG_GUIDE.md)
- **Fortgeschrittene Probleme**: Technische Details in der [Entwicklungsdokumentation](development/)

### Mitwirken

- **Verbesserungen an der Dokumentation**: Halten Sie sich an die bestehende Formatierung und Gliederung
- **Neue Inhalte**: Im passenden themenbasierten Ordner ergänzen
- **Aktualisierungen**: Zeitstempel „Last updated“ und klare Beschreibungen der Änderungen angeben

---

## 🎯 Nächste Schritte

**Wählen Sie Ihren Weg entsprechend Ihren Zielen:**

- **🚀 Schnellstart**: Gehen Sie zu [QUICKSTART.md](getting-started/QUICKSTART.md) und führen Sie in 5 Minuten die ersten Analysen durch
- **🔬 Forschungsschwerpunkt**: Beginnen Sie mit [WHY_ISEE.md](getting-started/WHY_ISEE.md), um die Methodik zu verstehen, und fahren Sie dann mit dem [Bewertungsprozess](advanced/ISEE_Scoring_and_Filtering_Process.md) fort
- **💻 Entwicklung**: Starten Sie mit [SYSTEM_OVERVIEW.md](development/SYSTEM_OVERVIEW.md), um die Architektur zu verstehen
- **📊 Analyse**: Springen Sie zu [REPORTING_GUIDE.md](advanced/REPORTING_GUIDE.md) für Datenexport und Analysemöglichkeiten

*Die Dokumentation des ISEE Meta Frameworks soll Sie auf Ihrem Weg von der ersten Neugier bis zu fortgeschrittenen Forschungsmöglichkeiten unterstützen. Beginnen Sie dort, wo es zu Ihrem aktuellen Bedarf passt, und folgen Sie den Querverweisen, um Ihr Verständnis zu vertiefen.*
