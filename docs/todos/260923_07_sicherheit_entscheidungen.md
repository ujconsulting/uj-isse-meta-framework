---
id: 2a12c1c7-463c-415d-85ad-94e3f8086e29
status: offen
aufwand: S
angelegt: 2026-09-02
ziele:
  jira: ISSE-15
punkte:
  0b130ed9-97b7-446c-a8f2-6a046bb519c1:
    jira: ISSE-16
  0ef8eff4-fbaf-41b1-9fa6-ce99943afa26:
    jira: ISSE-18
  bd9560a9-0cf6-43ac-8a4c-1f6ae28191d1:
    jira: ISSE-17
---
# T07 — Offene Sicherheits-Entscheidungen (Bündel)

**Status: offen** · angelegt 02.09.2026 · Aufwand S

Drei eng zusammengehörige, kleine Punkte aus dem Sicherheits-Abschnitt. Jeder braucht eine
Entscheidung oder einen kurzen Schritt des Auftraggebers, keiner ist für sich ein größeres
Vorhaben.

- [ ] **Meldeweg — letzte Meile:** Privates Vulnerability Reporting ist seit 02.09.2026 <!-- aufgabe:0b130ed9-97b7-446c-a8f2-6a046bb519c1 -->
      eingeschaltet (per API geprüft), `SECURITY.md` existiert seit `7bda8a4` aber nur auf
      dem Branch `fix/honest-failure-reporting` — auf `main` liefert GitHub 404, weil es
      vom Standardbranch liest. Offen ist nur noch der Merge von PR #1
      (`security/policy-on-default-branch`, laut Stand vom 07.09.2026 byte-identisch zur
      Branch-Fassung, daher konfliktfrei).
- [ ] **Schlüsselpräfix im Verlauf:** In `session-summaries/SESSION-SUMMARY-2025-01-23-01.md` <!-- aufgabe:bd9560a9-0cf6-43ac-8a4c-1f6ae28191d1 -->
      und `-2025-08-22-01.md` steht der Anfang eines OpenRouter-Schlüssels im Klartext
      (Präfix, kein vollständiger Schlüssel) — geerbt vom Original, aber unter dem eigenen
      Org-Namen öffentlich lesbar. Zu entscheiden: stehen lassen, im aktuellen Stand
      entfernen (Verlauf bleibt), oder Verlauf umschreiben (`git filter-repo` — ändert alle
      Commit-IDs, bei öffentlichem Repo mit Fork-Beziehung nicht folgenlos).
- [ ] **OpenRouter-Schlüssel in den Vault:** alle 381 Vaultwarden-Einträge geprüft, kein <!-- aufgabe:0ef8eff4-fbaf-41b1-9fa6-ce99943afa26 -->
      OpenRouter-Eintrag vorhanden. Nach der `credential-vault`-Regel gehört er dorthin,
      etwa als `uj-isse-meta-framework/openrouter_api_key`, mit Round-Trip-Prüfung.

Herkunft: aus `docs/todos/2026-09-02-offene-punkte.md`, Abschnitte 4.1 (Nachtrag
07.09.2026), 4.2, 4.3.
