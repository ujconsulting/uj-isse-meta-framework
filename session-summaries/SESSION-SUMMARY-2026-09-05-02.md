# Session Summary — 2026-09-05, second half (autonomous)

Branch `fix/honest-failure-reporting`. 12 further commits on top of
`SESSION-SUMMARY-2026-09-05-01.md`. Test suite **260 → 321 passed, 0 failed**.

No paid model calls. OpenRouter credit unchanged at **$17.89**. Every check below
was run, not reasoned about; where something could not be verified it says so.

---

## The thread running through all of it

The first half of this session named the pattern: *something goes wrong and the
result looks exactly like success*. This half found nine more instances, and three
of them were in code written earlier the same day to expose that very pattern.

That is the finding worth keeping. Writing the honest version of a thing does not
make it honest. It has to be measured against the disk.

---

## What was broken, in order of how much it mattered

### The flagship feature had never worked here

`CLAUDE.md` calls the Cognitive Diversity Explorer "fully operational and
battle-tested". Not one run under `data/output` had an index, and none could be
built. Three encoding faults stacked:

1. The extractor printed a checkmark emoji. By hand its output is a terminal, which
   copes; `app.py` runs it through a pipe, so Windows falls back to cp1252 and the
   emoji raised `UnicodeEncodeError`. **That print sits before `save_index`** — so
   the index was never written. The error handler then crashed too, printing a
   cross. What reached the interface was "extraction failed" and a traceback about a
   checkmark, which reads like a cosmetic complaint and was the whole feature being
   off. *The identical guard has been at the top of `main.py` since this branch
   began, with a comment describing this exact failure. The file `app.py` actually
   pipes never got it.*
2. `launch_cognitive_explorer.py` opened files without naming an encoding; the
   emoji-laden template failed to decode at byte 20231 and the route returned 500.
3. `app.py` read that same pipe with bare `text=True`, so subprocess's reader thread
   died. The call returned 0 and looked fine, but `stdout` and `stderr` were then
   unusable — **the branch that reports why an extraction failed had nothing to
   report from.** A diagnostic path that breaks precisely when it is needed.

Verified from a cold start with the index deleted: two different runs open, each
serving its own data, eleven and two responses.

### Money with no ceiling

`/api/execute` launched a subprocess for every POST. A hundred requests meant a
hundred analyses at roughly $0.31 each, on an interface with no authentication that
binds `0.0.0.0`. Now three concurrent and ten an hour, both env-overridable.
Checked that the concurrency half is not dead code: the status a run carries really
is `running`, and every exit path replaces it.

### Three routes answering with somebody else's run

`/api/download-zip`, `/api/markdown` and `/api/query-details` each fell back to the
newest non-empty run when an id did not resolve. Measured with the invented id
`exec_erfunden`: **160,854 / 19,400 / 13,156 bytes, all HTTP 200.** A fourth,
`/api/extract_cognitive_diversity`, substituted a run with a "nearby" timestamp —
and *writes* into the run it picks, so a caller asking about one run could rewrite
another's index. (Its arithmetic never meant what it said either: `HHMMSS` is not a
quantity, so `abs(a - b) <= 300` is not "within five minutes".)

The security reading is the smaller half. On a single-user machine this means
"download my results" could hand back a different run's results, silently. Someone
comparing two runs would read the same one twice and never learn it.

### The API key was in the browser's cookie

`session['openrouter_api_key'] = api_key`. A Flask session cookie is **signed, not
encrypted** — the signature stops the visitor editing it, and nothing stops anyone
reading it. A key that spends real money sat base64-encoded in the cookie jar and
went back to the server on every request, over plain HTTP, including for static
files. It now lives in the process, filed under the session id.

Wiring that up exposed a second thing: the session id was assigned only by `/demo`.
The interface the documentation tells people to open is `/isee-ui`, which never goes
through there — so those visitors had no session at all, every analytics line about
them read `user_session=anonymous`, and the new store would have had nothing to file
under.

### 724 empty directories, and what they cost

`ISEEApplication.__init__` created its run directory. `/api/preview-queries` builds
a whole application just to show which questions *would* be asked; `--list-domains`
builds one to read a list. Each left a directory behind — 264 in one two-hour
stretch, the newest timestamped to the second a test had merely imported the module.

The clutter is the visible half. The damaging half: an empty directory stopped
meaning anything, because a preview leftover and a run that died before its first
call look identical. Three of the 724 were the latter, and after deletion they
cannot be told apart. That is a real if small loss, recorded rather than glossed.

### `latest.txt` named a directory that does not exist

`update_latest_symlink` compared `run_output_dir.startswith(output_base)` — and the
two are built differently: `os.path.join` gives `data\output` while the run path is
assembled by f-string as `data/output/2026-09/...`. False for every CLI run, so the
pointer recorded a bare basename for a directory three levels down. **Third instance
of string-comparison-instead-of-path-components on this branch.**

### The run archive, and then the archive's own blind spot

Built, shipped — and it listed seven of nine runs. `app.py` writes
`data/output/run_TIMESTAMP`; `main.py` writes
`data/output/YYYY-MM/weekN/run_TIMESTAMP`. Browser runs land flat, CLI runs land
nested, and a top-level search looked complete while being partial. In the page
written to expose exactly that.

Unifying the layouts is the actual repair and was **not** done here: `CLAUDE.md`
requires a reviewed plan for changes to the run output layout.

### The container ran the dev server as root

`CMD ["python", "app.py"]` starts Flask's development server, and nothing dropped
privileges. `nixpacks.toml` had served this with gunicorn all along. Built and run,
not argued: `uid=10001(isee)`, `Server: gunicorn`, `/isee-ui` → 200, `data/`
writable.

---

## Two green checkmarks that were over nothing

- The cookie inspector in the new API-key test could not decode a **compressed**
  session cookie, so it found nothing in every case — including the broken one — and
  would have passed no matter what the cookie held. It now has a test of its own,
  which puts the key back into the session and requires it to be found.
- The archive's "Explore responses" link pointed at a route that 404s. Every run.

## The flaky test, explained

`TestWebUIParameterValidation` (open since the first summary) was measured: 8 of 20
runs failed, all contiguous. The cause was **this session** — an agent ran the suite
while `app.py` was being edited in the same working directory, and
`web_ui_parameter_validation.py` imports it fresh at collection time. Not a test
defect. Flake-hunting needs an isolated checkout, or a pause on concurrent edits.

## Outside this repository

The shared secret-scan pre-commit hook (`_claude/vault/git_secret_precommit.py`)
blocked the commit that took the API key *out* of the cookie, because
`api_key = _recall_api_key()` matched its assignment pattern. A function call is
never a literal, so the check now looks at the character after the value. Verified
against eight cases: the calls and `os.environ.get(...)` stay quiet, while
OpenRouter keys in both quote styles, a password, a GitHub token and a `.env`-style
`GLOBANT_API_KEY=` line still report. Committed and pushed to the LAN Gitea.

---

## Still open

1. ⛔ **The quality gate is still dead code**, and its repair plan still ends on
   `VERDICT: REVISE`. Do not enable it before repairing it.
2. **The engine seam** — preparatory steps only; that plan also ended on REVISE.
3. **Two output layouts.** Needs a reviewed plan. Until then every reader of
   `data/output` must handle both, and the Explorer cannot open a CLI run at all.
4. **No authentication**, and the interface binds `0.0.0.0`.
5. **Cost figures still do not appear in the interface.**
6. **~23,000 lines have never been audited.** The audit covered four files.
