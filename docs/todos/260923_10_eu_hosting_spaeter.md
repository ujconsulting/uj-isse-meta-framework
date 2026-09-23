---
id: 25a0a220-4a07-4d49-b471-1dce2fa1bb33
status: offen
aufwand: M
angelegt: 2026-09-02
ziele:
  jira: ISSE-25
punkte:
  d937b0b9-9657-4e52-a71b-2c7eb761b55e:
    jira: ISSE-26
---
# T10 — EU-Hosting (später, prägt aber die Provider-Schicht)

**Status: offen** · angelegt 02.09.2026 · Aufwand M

## Idee

Provider-Schicht nach Datenklasse staffeln statt global umschalten: offen über
OpenRouter, vertraulich über EU-Regionen im eigenen Vertrag (AWS Bedrock / Azure — nicht
austauschbar, keiner deckt allein die 14 Häuser), sensibel lokal. Der ungenutzte
`ollama_models`-Block ist die vorhandene Naht dafür.

## Preis

In den unteren Stufen sinkt die kognitive Vielfalt — genau das, wofür ISEE existiert.

## Zu klären

- [ ] Die rechtliche Einordnung ist nicht von der Code-Seite zu entscheiden — braucht eine <!-- aufgabe:d937b0b9-9657-4e52-a71b-2c7eb761b55e -->
      Entscheidung des Auftraggebers, ob und wann dieser Punkt angegangen wird

Bewusst niedrige Priorität: prägt die Provider-Schicht, ist aber kein aktueller Engpass.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitt 5.3.
