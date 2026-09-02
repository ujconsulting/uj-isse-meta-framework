# `.codex/` — Arbeitskontext für den Codex-Reviewer

Dieser Ordner ergänzt `AGENTS.md` im Repo-Root, die Codex beim Start **automatisch**
lädt. Was hier liegt, muss Codex dagegen gezielt gesagt oder gelesen werden.

## Warum es diesen Ordner gibt

Codex hat **kein Gedächtnis zwischen Sitzungen**. Claude hat eines (den Memory-Store),
Codex nicht — jede Review-Sitzung beginnt bei null. `knowledge.md` ist das manuell
gepflegte Substitut dafür: die Handvoll Dinge, die man in diesem Repo schon einmal
schmerzhaft gelernt hat und die ein frischer Leser nicht aus dem Code ableiten kann.

⚠️ **Diese Datei veraltet still.** Es gibt keinen Abgleich mit dem Claude-Memory-Store.
Wer eine der beiden Seiten deutlich ändert, zieht die andere nach.

## Inhalt

| Datei | Zweck |
| --- | --- |
| `knowledge.md` | verdichtete Projekterfahrung — Fallstricke, die sich wiederholt haben |

## Wo der Prüfkatalog steht

Nicht hier, sondern in `AGENTS.md` → **„Rolle: Plan-Reviewer"** (Prüfkatalog und
Tabu-Scope) bzw. **„Rolle: Abnahme-Prüfer"**. Zwei Quellen für dieselbe Sache driften
auseinander; deshalb steht sie nur an einer Stelle.
