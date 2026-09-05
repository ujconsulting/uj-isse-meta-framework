# Session Summary — 2026-09-05 (overnight, autonomous)

Branch `fix/honest-failure-reporting`. 14 commits, 33 files, +3,192 / −831.
Test suite: **151 passed / 9 failed → 260 passed / 0 failed.**

Worked unattended at the owner's request, with five parallel subagents on disjoint
files. No paid model calls were made. Every subagent result was verified against the
code before it was committed, and two of them turned out to need correcting.

---

## What this night was actually about

The audit of 03.09.2026 (`docs/audit/2026-09-03-baseline.md`) had listed the findings.
This session worked them off. But the more useful outcome is a pattern that showed up
again and again, in code written by the original author, by earlier sessions, and by me
in this one:

**Something goes wrong, and the result looks exactly like success.**

Nine separate instances were found and closed tonight. They are listed below not to
pad the report but because the shape repeats, and recognising it is worth more than any
individual fix.

---

## The findings, by how they hid

### A scorer error that looked like a low score
`evaluation_scoring.score_text` caught every exception per criterion and substituted
`0.0`. That is the path every real run takes. A broken scorer looked exactly like a
genuinely poor answer and silently changed which responses won. Now recorded as a
structured error, reported as `None`, excluded from the weighted average — and the run
prints which criterion failed and why.

⚠️ A subagent proposed `NaN` as the marker. Rejected after measuring: `sorted([0.9,
nan, 0.1])` returns the list unchanged, `nan > 0.5` and `nan <= 0.5` are **both** False,
and `json.dumps` writes a bare `NaN`, which is not valid JSON. Run results are written
as JSON and ranked by sorting. `None` serialises as `null` and makes comparisons raise
where they happen. Two tests pin the reasoning.

### An answer about failure, discarded as a failure
`main.py:1480` runs every response through `APIErrorDetector.is_api_error`, and a
flagged response is recorded as a failed call — gone from scoring, synthesis and the
deliverable. It counted error vocabulary by substring and treated two hits under 500
characters as proof. Measured:

> "A blameless post-mortem culture reduces repeat failures. When an error occurs, the
> team documents the timeout and the failed request without assigning blame."

was reported as an API error on three keywords. That is not an error — it is the
answer. The critical and contrarian frameworks exist to commission exactly this. The
vocabulary count now applies only to text that does not read as prose, matches whole
words, and no longer treats "organization" and "enterprise" as error terms.

*And the correction of the correction:* removing those two words hid a real Globant
refusal, which the Globant test caught within the minute. Its phrasing is now a
pattern, which is what identified it all along.

### A report that could not be written at all
`"response" in result` is a key-presence test, and `_failed_model_response` sets
`"response": None`. Six sites then ran `len(None)`. **A run containing a single failed
model call could not produce a report.** Verified against the previous revision rather
than argued. It stayed latent because the other failure shape carries no `response` key
at all, and that is the one the run of 02.09. happened to hit.

The trigger was ours: `8137f49` replaced simulated text with `response=None`, which was
right, and nothing downstream was checked against it.

### A run that changed what it asked, and said nothing
Two commits of mine claimed more than the code did, found by a subagent asked to check
commits against code — the single most valuable instruction given tonight.

`0f5497e` said the query-degradation flag "reaches the run's own output, not just a log
nobody tails". It reached nothing: the flag is spread into `template.format(...)`, which
silently drops unused keys. Written in one place, read in none. Now made true — the
metadata header of `isee_result.md` names the degradation and its reason.

### Winners credited to models that do not exist
`run_summary.md` read `**or_claude with Sonnet Instruction**`. Both report writers split
the combination id on `_` and assumed a two-part model name; every model in the
portfolio has more. Worse, entries 1 and 3 were byte-identical — two different
frameworks on the same model collapsed into one line, so the report flattened exactly
the diversity the tool exists to reveal.

### Domains that never reached a domain
`app.py` read `if identifier.startswith('dynamic_domain_') or not
identifier.startswith('domain_')` — meaning anything not already an id is used
unchanged, so the resolution ladder underneath was reachable only for ids. "Education"
became `KeyError: No domain with ID 'Education' exists`, a 500 from
`/api/preview-queries`.

### A pipeline that died after paying for the models
Found by running the whole thing end to end after the night's changes, which is the
only way it could have been found: `analysis.py` picked its scoring columns by
excluding ten named ones, so a `status` column added earlier in the night counted as a
score. `TypeError: Cannot perform reduction 'mean' with string dtype` — in the analysis
step, after every model had been called and billed.

### A database write lost to a lock, and a chart backend that would have crashed
Both preparatory items from the engine-seam plan. Twelve sqlite connections now carry a
busy timeout; `analysis.py` selects Agg before importing pyplot. The latter is
demonstrated rather than assumed: drawing from a non-main thread without it dies with
`Tcl_AsyncDelete: async handler deleted by the wrong thread`.

### A pointer nobody could write and nobody read
`data/output/latest` was a symlink needing a Windows privilege an ordinary account does
not have. WinError 1314 on every run, a warning nobody could act on, and the file never
existed. Now `latest.txt`, written atomically.

---

## Also done

- **453 lines of dead configuration removed.** Five of eleven top-level blocks in
  `openrouter_config.json` had no reader. `cognitive_diversity` referenced model ids
  with **zero** overlap against the fourteen actually configured — the signature of a
  block that drifted out of use. A test now guards against the drift returning.
- **The estimate learns.** `TYPICAL_RESPONSE_TOKENS = 2500` was one measurement of one
  query on one day and said so. It now prefers the tokens recent runs were actually
  billed, with two guards: below twenty calls on record the constant stands, and only
  the last ten runs count.
- **`CLAUDE.md` agrees with the code.** It carried **three** different answers to what
  the scoring weights are, none matching each other or the code, and four different
  model counts. One table now, plus the note that changing weights means changing it in
  the same commit.
- **Both run databases untracked.** They carry the full text of every research question
  ever asked, and the repository is public.
- **Deployment set to one gunicorn worker**, because `execution_status` is per-process
  memory and two workers make run status a coin flip.

---

## Still open — do not mistake this for finished

1. ⛔ **The quality gate is still dead code.** `main.py` scores with `score_text()`. A
   response of pure placeholders scores 0.292 against a good one's 0.298. The repair
   plan (`docs/plans/2026-09-03-bewertung-reparieren.md`) ended three Codex rounds on
   `VERDICT: REVISE`, not `APPROVED` — it is not even an agreed plan yet. **Do not
   enable it before repairing it**; the gate as written discards good answers.
2. **The engine seam** (`docs/plans/2026-09-03-engine-naht.md`) — only preparatory steps
   0a–0e are partly done. Also ended on REVISE.
3. **No authentication.** The interface binds `0.0.0.0`.
4. **The run archive** the owner asked for on 02.09. is still not built.
5. **Cost figures still do not appear in the interface** — deliberately behind the
   engine seam.
6. **~23,000 lines have never been audited.** The audit covered four files.

## Two things a future session should not have to rediscover

- **`tests/command_wizard/` is dead.** It imports a module that exists only under
  `archive/`. Plain `pytest tests/` fails with twelve collection errors; every command
  in this repository's docs now carries `--ignore=tests/command_wizard`. Deleting it is
  the real fix.
- **A subagent reported the suite's pass count varying run to run (231/241/248) with
  "identical code" and blamed property-based tests.** Measured afterwards on a stable
  tree: three consecutive runs gave 253, 253, 253. The variation was other agents adding
  test files during those runs. A separate agent did observe two flaky runs out of eight
  in `TestWebUIParameterValidation`; that one is unexplained and worth watching.

## Budget

No paid calls tonight. Remaining OpenRouter credit unchanged at **$17.89**.
The end-to-end verification used `--simulate` throughout.
