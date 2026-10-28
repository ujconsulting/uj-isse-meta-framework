# ISEE Meta Framework - Entwicklungsskripte

**Deutsch** · [English](README.md)

Dieses Verzeichnis enthält robuste Entwicklungsskripte, mit denen Sie Ihre Flask-Anwendung auf localhost:5001 verwalten – mit sauberer Prozess-Lebenszyklusverwaltung und Werkzeugen zum Freigeben belegter Ports.

## 📁 Übersicht der Skripte

| Skript | Zweck | Verwendung |
|--------|-------|------------|
| `dev-server.sh` | 🚀 **Zentrale Verwaltung des Entwicklungsservers** | `./dev-server.sh {start\|stop\|restart\|status\|logs}` |
| `kill-port.sh` | 💀 Prozesse auf einem bestimmten Port beenden | `./kill-port.sh <port> [--force]` |
| `check-ports.sh` | 🔍 Status der Entwicklungsports prüfen | `./check-ports.sh [port1] [port2] ...` |
| `kill-dev-ports.sh` | 🧹 Alle gängigen Entwicklungsports freiräumen | `./kill-dev-ports.sh [--force]` |
| `dev-aliases.sh` | ⚡ Shell-Aliase und -Funktionen | `source dev-aliases.sh` |
| `install-aliases.sh` | 🔧 Aliase in die Shell-Konfiguration einbauen | `./install-aliases.sh [--shell bash\|zsh]` |

## 🚀 Schnellstart - So verändern Sie Ihren Arbeitsalltag

**🔄 Schluss mit `python app.py` - arbeiten Sie mit diesen Skripten und genießen Sie eine bessere Entwicklungserfahrung!**

### Warum von `python app.py` wechseln?

**❌ Probleme mit `python app.py`:**
- Der Prozess geht verloren, sobald das Terminal geschlossen wird
- Kein sauberes Beenden (Strg+C funktioniert manchmal nicht)
- Port-Konflikte durch hängengebliebene Prozesse
- Keine dauerhafte Protokollierung
- Manuelles Aufräumen nötig

**✅ Vorteile des skriptbasierten Ablaufs:**
- Betrieb im Hintergrund (unabhängig vom Terminal)
- PID-Verfolgung und sauberes Beenden
- Automatische Auflösung von Port-Konflikten
- Dauerhafte Protokollierung in `dev-server.log`
- Statusüberwachung und Prozessverwaltung

### 1. Aliase installieren (DRINGEND EMPFOHLEN - zuerst erledigen!)

```bash
# Einmalige Einrichtung (dauert 30 Sekunden)
./scripts/install-aliases.sh
source ~/.zshrc  # oder ~/.bashrc, oder einfach das Terminal neu starten

# Installation testen
isee-help       # Sollte alle verfügbaren Befehle anzeigen
```

### 2. Ihr neuer Arbeitsalltag

**🎯 Einfache Alltagsbefehle (nach der Alias-Installation):**
```bash
# Entwicklungssitzung starten
isee-start      # Ersetzt: python app.py

# Browser öffnen (optional - in Ihren Ablauf aufnehmen)
open http://localhost:5001/isee-ui/isee-ui

# Serverstatus jederzeit prüfen
isee-status     # Zeigt laufend/gestoppt + letzte Logeinträge

# Logs zur Fehlersuche ansehen (ein echter Gewinn!)
isee-logs       # Logs in Echtzeit verfolgen

# Sauber beenden, wenn Sie fertig sind
isee-stop       # Immer ein sauberes Herunterfahren
```

**🔧 Alternative: Skripte direkt verwenden (wenn Sie keine Aliase möchten):**
```bash
./scripts/dev-server.sh start    # Ersetzt: python app.py
./scripts/dev-server.sh status   # Status prüfen
./scripts/dev-server.sh logs     # Logs ansehen
./scripts/dev-server.sh stop     # Sauber beenden
```

### 3. Port-Konflikte lösen (wenn etwas schiefgeht)

```bash
# Port-Probleme diagnostizieren
isee-ports      # oder: ./scripts/check-ports.sh

# Bestimmte Port-Konflikte beheben
isee-kill-port 5001    # oder: ./scripts/kill-port.sh 5001

# Radikallösung - alles aufräumen
isee-kill-dev-ports    # oder: ./scripts/kill-dev-ports.sh
```

## 🔧 Ausführliche Anwendung

### Verwaltung des Entwicklungsservers (`dev-server.sh`)

Das Hauptskript verwaltet den Lebenszyklus der Flask-Anwendung zuverlässig:

**Server starten:**
```bash
./scripts/dev-server.sh start
```
- ✅ Prüft auf bestehende Prozesse und räumt Port 5001 auf
- ✅ Startet den Server im Hintergrund mit PID-Verfolgung
- ✅ Prüft, ob der Start erfolgreich war
- ✅ Zeigt Server-URL und Speicherort der Logdatei an

**Status prüfen:**
```bash
./scripts/dev-server.sh status
```
- ✅ Zeigt den Status laufend/gestoppt an
- ✅ Zeigt Prozessdetails an (PID, Port, URL)
- ✅ Zeigt die letzten Logeinträge an
- ✅ Erkennt Port-Konflikte mit anderen Prozessen

**Logs ansehen:**
```bash
./scripts/dev-server.sh logs
```
- ✅ Logs in Echtzeit verfolgen (wie `tail -f`)
- ✅ Mit Strg+C beenden

**Server stoppen:**
```bash
./scripts/dev-server.sh stop
```
- ✅ Versuch eines sauberen Herunterfahrens (SIGTERM)
- ✅ Erzwungenes Beenden, falls das saubere Herunterfahren scheitert (SIGKILL)
- ✅ Aufräumen von PID-Dateien und Port-Konflikten
- ✅ 10 Sekunden Zeitlimit für das saubere Herunterfahren

### Skripte zur Port-Verwaltung

**Ports prüfen (`check-ports.sh`):**
```bash
# Standard-Entwicklungsports prüfen (3000, 5000, 5001, 8000, 8080, 8888, 9000)
./scripts/check-ports.sh

# Bestimmte Ports prüfen
./scripts/check-ports.sh 5001 3000 8080
```

**Bestimmten Port freigeben (`kill-port.sh`):**
```bash
# Sauberes Beenden
./scripts/kill-port.sh 5001

# Erzwungenes Beenden (sofort)
./scripts/kill-port.sh 5001 --force
```

**Alle Entwicklungsports aufräumen (`kill-dev-ports.sh`):**
```bash
# Alle gängigen Entwicklungsports aufräumen
./scripts/kill-dev-ports.sh

# Alle Ports erzwungen aufräumen
./scripts/kill-dev-ports.sh --force
```

### Shell-Aliase (`dev-aliases.sh`)

Bietet nach der Installation über 25 praktische Befehle:

**Navigation:**
- `isee-cd` - In das Projektverzeichnis wechseln
- `isee-scripts` - In das Skriptverzeichnis wechseln

**Serververwaltung:**
- `isee-start` - Entwicklungsserver starten
- `isee-stop` - Entwicklungsserver stoppen
- `isee-restart` - Entwicklungsserver neu starten
- `isee-status` - Serverstatus anzeigen
- `isee-logs` - Server-Logs verfolgen

**Port-Verwaltung:**
- `isee-ports` - Gängige Entwicklungsports prüfen
- `isee-kill-port <port>` - Prozesse auf einem bestimmten Port beenden
- `isee-kill-dev-ports` - Prozesse auf allen Entwicklungsports beenden

**Entwicklungsablauf:**
- `isee-setup` - Vollständige Einrichtung der Entwicklungsumgebung
- `isee-clean` - Alle Entwicklungsprozesse aufräumen
- `isee-reset` - Entwicklungsumgebung zurücksetzen
- `isee-dev` - Schnelle Prüfung des Entwicklungsstatus

**Tests & Konfiguration:**
- `isee-test` - Schnelle Parameter-Validierungstests ausführen
- `isee-config` - Konfigurationsstatus prüfen
- `isee-deps` - Abhängigkeiten installieren/aktualisieren

## 🎯 Täglicher Entwicklungsalltag - Praxisszenarien

### 💡 Ablaufvergleich: alt und neu

**❌ Ihr bisheriger Ablauf mit `python app.py`:**
```bash
# Start (blockiert das Terminal, kein Hintergrundbetrieb)
cd /Users/josephfajen/git/ISEE_Meta_Framework
python app.py
# Das Terminal ist nun belegt...

# Stoppen (hoffentlich funktioniert Strg+C, oft bleiben Prozesse hängen)
^C

# Probleme suchen (manuelle Detektivarbeit)
lsof -i :5001
kill -9 <pid>  # falls nötig
```

**✅ Ihr neuer skriptbasierter Ablauf:**
```bash
# Start (von überall, läuft im Hintergrund)
isee-start
# ✅ Server started successfully!
# ✅ URL: http://localhost:5001/isee-ui
# ✅ Logs: dev-server.log
# Das Terminal bleibt für andere Aufgaben frei!

# Stoppen (immer sauber, automatisches Aufräumen)
isee-stop
# ✅ Server stopped gracefully
```

### Szenario 1: Typische tägliche Entwicklungssitzung

**🎯 Start am Morgen (empfohlene Routine):**
```bash
# Schnelle Umgebungsprüfung und Start
isee-status                       # Läuft schon etwas?
isee-start                        # Frisch starten
open http://localhost:5001/isee-ui/isee-ui        # Browser öffnen
```

**🔄 Während der Entwicklung:**
```bash
# Serverstatus jederzeit prüfen
isee-status                       # Schneller Gesundheitscheck

# Probleme mit dauerhaften Logs analysieren
isee-logs                         # Logs in Echtzeit ansehen (mit Strg+C beenden)
tail -f dev-server.log           # Alternative zur Log-Ansicht

# Server nach Codeänderungen neu starten (falls nötig)
isee-restart                     # Sauberer Neustart
```

**🌙 Feierabend:**
```bash
isee-stop                        # Sauber herunterfahren
```

### Szenario 2: „Server startet nicht" - Port-Konflikte

**🚨 Problem:** Sie erhalten die Fehlermeldung „port already in use"

**🎯 Lösung:**
```bash
# Diagnostizieren, was Ihre Ports belegt
isee-ports                       # Schneller Überblick
lsof -i :5001                    # Detailansicht für Port 5001

# Den konkreten Konflikt beheben
isee-kill-port 5001              # Nur Port 5001 freigeben
# ODER
isee-kill-dev-ports              # Radikallösung - alle Entwicklungsports aufräumen

# Frisch starten
isee-start
```

### Szenario 3: „Irgendetwas stimmt nicht" - Fehlersuche

**🚨 Problem:** Der Server reagiert nicht oder verhält sich seltsam

**🎯 Ablauf der Fehlersuche:**
```bash
# Prüfen, ob der Server tatsächlich läuft
isee-status                      # Zeigt PID, Port, letzte Logs

# Letzte Aktivität ansehen
isee-logs                        # Logs in Echtzeit verfolgen

# Auf Port-Konflikte prüfen
isee-ports                       # Sehen, was sonst noch stören könnte

# Bei Bedarf sauber neu starten
isee-restart                     # Stoppen + aufräumen + starten
```

### Szenario 4: „Neustart von Grund auf" - Umgebung sauber zurücksetzen

**🎯 Vollständiger Reset (wenn wirklich alles durcheinander ist):**
```bash
# Radikallösung - alles aufräumen
isee-stop                        # Server stoppen
isee-kill-dev-ports              # Alle Entwicklungsports aufräumen
isee-start                       # Frisch starten

# ODER - Reset mit einem Befehl
isee-reset                       # Erledigt alles oben Genannte
```

### Szenario 5: „An mehreren Projekten arbeiten"

**🎯 Ortsunabhängigkeit (mit Aliasen):**
```bash
# Die Serververwaltung funktioniert von überall
cd ~/Documents/some-other-project
isee-status                      # ISEE-Serverstatus prüfen
isee-logs                        # ISEE-Logs ansehen

# Bei Bedarf zurück ins Projekt wechseln
isee-cd                          # Ins ISEE-Projektverzeichnis springen
```

### Szenario 6: „Weitergabe an das Team / Dokumentation"

**🎯 Wenn Sie anderen etwas erklären oder Dokumentation schreiben:**
```bash
# Zur Klarheit die vollständigen Skriptpfade verwenden
./scripts/dev-server.sh start    # Eindeutig und ausdrücklich
./scripts/check-ports.sh         # Leicht verständlich

# Aliase sind für Ihren persönlichen Ablauf gedacht
isee-start                       # Persönlicher Komfort
```

## 🛠 Erweiterte Funktionen

### Funktionen der Serververwaltung

- **PID-Dateiverfolgung:** Die Prozess-ID des Servers wird in `.dev-server.pid` gespeichert
- **Logdatei-Verwaltung:** Die gesamte Ausgabe wird in `dev-server.log` erfasst
- **Sauberes Herunterfahren:** 10 Sekunden Zeitlimit, bevor das Beenden erzwungen wird
- **Erkennung von Port-Konflikten:** Port-Konflikte werden automatisch erkannt und aufgelöst
- **Prüfung der Voraussetzungen:** Prüft auf `app.py` und `requirements.txt`

### Funktionen der Port-Verwaltung

- **Intelligente Prozesserkennung:** Verwendet `lsof` für eine genaue Erkennung der Port-Belegung
- **Sauber oder erzwungen beenden:** Wahl zwischen SIGTERM und SIGKILL
- **Stapelverarbeitung:** Mehrere Ports gleichzeitig aufräumen
- **Sicherheitsprüfungen:** Validiert Portnummern und die Existenz von Prozessen

### Funktionen der Shell-Integration

- **Autovervollständigung:** Tab-Vervollständigung für gängige Portnummern
- **Farbcodierte Ausgabe:** Grüne/rote/gelbe Statusanzeigen
- **Verzeichnisbewusstsein:** Warnt, wenn Sie sich nicht im Projektverzeichnis befinden
- **Kompatibilität mit mehreren Shells:** Funktioniert mit bash und zsh

## 🔍 Fehlerbehebung

### Häufige Probleme

**Problem: „Permission denied" beim Ausführen der Skripte**
```bash
# Lösung: Skripte ausführbar machen
chmod +x scripts/*.sh
```

**Problem: „Port ist nach dem Stoppen des Servers noch belegt"**
```bash
# Lösung: Aufräumen erzwingen
./scripts/kill-port.sh 5001 --force
```

**Problem: „Server startet, aber http://localhost:5001/isee-ui ist nicht erreichbar"**
```bash
# Server-Logs prüfen
./scripts/dev-server.sh logs

# Prüfen, ob der Server tatsächlich auf dem Port läuft
./scripts/check-ports.sh
```

**Problem: „Mehrere Python-Prozesse laufen"**
```bash
# Alle Python-Prozesse anzeigen
ps aux | grep python

# Entwicklungsports aufräumen
./scripts/kill-dev-ports.sh --force
```

### Logdateien

- **Server-Logs:** `dev-server.log` (im Projektstamm)
- **PID-Datei:** `.dev-server.pid` (im Projektstamm)
- **Skriptausgabe:** Alle Skripte liefern farbige Ausgaben mit Zeitstempel

### Validierungsbefehle

```bash
# Testen, ob alle Skripte funktionieren
./scripts/check-ports.sh
./scripts/dev-server.sh status
ls -la scripts/*.sh              # Prüfen, ob alle ausführbar sind

# Aliase testen (nach der Installation)
isee-help                        # Sollte alle verfügbaren Befehle anzeigen
```

## 🔑 Häufige Fragen

### „Was ist der Unterschied zwischen `isee-start` und `./scripts/dev-server.sh start`?"

**Antwort: Beide tun exakt dasselbe!**

| Aspekt | `./scripts/dev-server.sh start` | `isee-start` |
|--------|---------------------------|------------|
| **Funktionalität** | ✅ Identisch | ✅ Identisch |
| **Verzeichnisvoraussetzung** | Muss im Projektstamm sein | Funktioniert von überall |
| **Tipparbeit** | 32 Zeichen | 10 Zeichen |
| **Am besten für** | Dokumentation, Weitergabe | Täglichen persönlichen Ablauf |

**Empfehlung:** Installieren Sie die Aliase und verwenden Sie `isee-start` im Alltag - der Komfort wird Sie überzeugen!

### „Sollte ich `python app.py` nicht mehr verwenden?"

**JA! Darum:**

**❌ Probleme mit `python app.py`:**
- Blockiert Ihr Terminal
- Keine dauerhafte Protokollierung
- Schwierige Prozessverwaltung
- Port-Konflikte, wenn etwas schiefgeht
- Kein sauberes Herunterfahren

**✅ Vorteile von `isee-start`:**
- Läuft im Hintergrund (das Terminal bleibt frei)
- Dauerhafte Protokollierung in `dev-server.log`
- Saubere Prozessverwaltung mit PID-Verfolgung
- Automatische Auflösung von Port-Konflikten
- Sauberes Herunterfahren mit Rückfall auf erzwungenes Beenden

### „Wo sind meine Logs und wie nutze ich sie?"

**Speicherort der Logdatei:** `dev-server.log` in Ihrem Projektstamm

**Logs ansehen:**
```bash
# Logs in Echtzeit verfolgen (am besten für die Fehlersuche)
isee-logs                        # Mit Strg+C beenden

# Alternative Möglichkeiten, Logs anzusehen
tail -f dev-server.log          # Direkter Dateizugriff
tail -n 50 dev-server.log       # Letzte 50 Zeilen
less dev-server.log             # Gesamte Logdatei durchblättern
```

**Warum Logs ein echter Gewinn sind:**
- ✅ **Dauerhaft:** Logs überstehen das Schließen des Terminals
- ✅ **Zeitstempel:** Sie sehen genau, wann etwas passiert ist
- ✅ **Vollständig:** Erfasst die gesamte Flask-Ausgabe und die Skriptmeldungen
- ✅ **Fehlersuche:** Unverzichtbar bei der Problemanalyse

## 🎉 Zusammenfassung - Ihre Entwicklungs-Wende

**🔄 CHECKLISTE FÜR DEN UMSTIEG:**

1. **✅ Aliase installieren** (einmalig, 30 Sekunden):
   ```bash
   ./scripts/install-aliases.sh && source ~/.zshrc
   ```

2. **✅ `python app.py` durch `isee-start` ersetzen** in Ihrer täglichen Routine

3. **✅ `isee-logs` verwenden** bei der Fehlersuche (statt zu versuchen, sich an die Konsolenausgabe zu erinnern)

4. **✅ `isee-status` verwenden**, um die Gesundheit des Servers jederzeit zu prüfen

5. **✅ `isee-stop` verwenden** für sauberes Herunterfahren (keine hängenden Prozesse mehr)

**🎯 IHRE TÄGLICHE ROUTINE WIRD ZU:**
```bash
# Morgens
isee-start && open http://localhost:5001/isee-ui/isee-ui

# Während der Entwicklung
isee-status      # Schneller Gesundheitscheck
isee-logs        # Bei Bedarf Fehlersuche
isee-restart     # Bei Bedarf sauberer Neustart

# Feierabend
isee-stop        # Sauber herunterfahren
```

**🎊 DAS WERDEN SIE ERLEBEN:**
- ✅ **Schluss mit dem Ärger über „port already in use"**
- ✅ **Dauerhafte Logs für bessere Fehlersuche**
- ✅ **Freies Terminal** (Server läuft im Hintergrund)
- ✅ **Konsistente, zuverlässige Serververwaltung**
- ✅ **Professioneller Entwicklungsablauf**
- ✅ **Funktioniert aus jedem Verzeichnis** (mit Aliasen)
- ✅ **Automatisches Aufräumen** (keine manuelle Prozesssuche)

---

*Dieses README ist Ihr täglicher Begleiter für die ISEE-Entwicklung. Setzen Sie ein Lesezeichen, schlagen Sie bei Bedarf nach, und erleben Sie, wie sich Ihre Entwicklungserfahrung von frustrierend zu fantastisch wandelt!*
