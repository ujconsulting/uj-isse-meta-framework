# Projektwissen ISEE — Digest für Codex

**Live-Quelle zuerst:** Ein Claude-Memory-Store für dieses Projekt existiert bislang
**nicht** (Stand 02.09.2026). Er läge im zentralen Memory-Verzeichnis des Arbeitsplatzes
unter dem Projekt-Slug dieses Repos (Pfad siehe die baumweite `CLAUDE.md`, Abschnitt
„Memory-Store"). Wird dort später einer angelegt, gilt er als aktueller als diese Datei —
dann von dort lesen und diesen Digest nachziehen.

Zweite Live-Quelle sind die **Session-Summaries** in `session-summaries/`
(chronologisch, `SESSION-SUMMARY-JJJJ-MM-TT-NN.md`). Sie sind die eigentliche Historie
dieses Repos; `CLAUDE.md` ist deren verdichtete, teilweise veraltete Zusammenfassung.

## Was hier schon wehgetan hat

- **Der Provider-Wechsel ist die teuerste Fehlerklasse.** Von den letzten ~10 Commits
  drehen sich sechs um Globant Enterprise AI: Modellformat, Endpunktpfad, Header,
  Parameterkompatibilität der o-Serie. Die Erfolgsquote fiel dabei einmal von ~100 %
  auf 15 % und wurde über „revert + gezielte Fixes" auf 67 % zurückgeholt. Jede
  Änderung an Requests trifft mit hoher Wahrscheinlichkeit genau hier.

- **Ein kaputter Lauf sah aus wie ein guter.** Die Fehlerbehandlung meldete
  HTTP-400-Antworten als „provider unavailable" und fiel in einen Simulationsmodus. Das
  Ergebnis war vollständig, plausibel und wertlos. Seitdem gilt: Fehler, die zu einem
  plausiblen Ergebnis führen, sind schlimmer als Abstürze.

- **Nach Konfigurationsänderungen ist ein Server-Neustart nötig** (`./scripts/dev-server.sh
  restart`). Ohne ihn misst man den alten Stand und schließt auf den neuen.

- **Web-UI und CLI driften auseinander.** Beide Wege führen in dieselbe Maschine, aber
  über verschiedene Parameterpfade — die Web-Oberfläche baut eine CLI-Kommandozeile und
  reicht Zusatzinfos über die Prozessumgebung durch. Das Repo trägt eine eigene
  Notizdatei über genau diesen Bruch (`NEXT_SESSION_WEB_UI_CLI_DISCREPANCY_FIX.md`).

- **Die Dokumentation hinkt dem Code hinterher.** LOC-Angaben in `CLAUDE.md` stimmen
  nicht mehr (`main.py`/`app.py` sind je ~3.1k statt der dort genannten 2.304), und die
  Scoring-Gewichte stehen dort in zwei unvereinbaren Fassungen. Im Zweifel gilt der
  Code.

- **Ein Schlüsselpräfix ist im Klartext eingecheckt.** In zwei Session-Summaries steht
  der Anfang eines OpenRouter-Schlüssels. Nicht dramatisch, aber der Beleg dafür, dass
  Protokolle hier Geheimnisse aufsammeln.

## Was jeder Lauf kostet

Standard 66 Calls ≈ 4 min ≈ $0.50 · Validierung 11 Calls ≈ 1 min ≈ $0.07. Das ist kein
Testbudget, sondern echtes Geld — deshalb steht Kostenwirkung im Prüfkatalog.

## Betrieb

```bash
./scripts/dev-server.sh start|status|logs|restart|stop   # Weboberfläche :5001
python main.py --query "…" --models 3 --provider openrouter   # schneller CLI-Test
```

Primäre Oberfläche: `http://localhost:5001/isee-ui`.
Deployment: Railway über `nixpacks.toml` (gunicorn auf `0.0.0.0:$PORT`).
