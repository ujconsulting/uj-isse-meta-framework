# Session Summary — 2026-09-02 (Session 01)

**Objective on entry**: run a `/claudex-loop:audit` on this repository.
**Objective on exit**: the audit has *not* run. Preparing for it surfaced blockers that
had to be cleared first, and clearing them was the session's actual work.

---

## Why the audit did not happen

The repository turned out not to be in a state where an audit produces anything usable:

1. **No `.env` existed** — the project had never been executed on this machine.
2. **5 of 17 configured OpenRouter models are dead**, the surviving 12 date from 2024/25.
   The first run would have failed on model IDs, not on anything an audit would find.
3. **Upstream has an unmerged refactoring line** that demolishes the very structures the
   audit's check catalogue targets. Auditing `main` without knowing that means auditing
   code the author already replaced.

Auditing first would have burned several hours of reviewer budget on findings that a
config update or a branch decision invalidates.

---

## Accomplishments

### Repository identity and licensing

- **Renamed** `ujconsulting/ISEE_Meta_Framework` → **`ujconsulting/uj-isse-meta-framework`**
  so the GitHub name matches the working directory. Local `origin` updated and verified
  with `git ls-remote`. GitHub keeps a redirect from the old name.
- **Fixed two inherited licence defects** (commit `163b07f`). Both came verbatim from
  upstream — the fork was byte-identical at the time (`compare` → `identical`, 0 ahead /
  0 behind), so these were the author's defects, not ours, but we were republishing them
  under our own org name:
  - README declared **MIT** (badge + licence section) while `LICENSE` invoked
    **Apache-2.0**. Resolved in favour of `LICENSE`, which is the operative grant.
  - `LICENSE` contained only the 19-line Apache **appendix boilerplate**, not the licence
    text. Apache-2.0 §4(a) requires giving recipients *a copy of this License*; a stub
    pointing at a URL is not one. Replaced with the canonical 202-line text
    (SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
    from apache.org), original `Copyright 2025 Joseph Fajen` preserved verbatim.
  - Added README "About This Fork": upstream attribution plus the §4(b) notice listing
    the files this fork modifies. Clone instructions now point at this fork.
  - **Verification**: GitHub's classifier went from `NOASSERTION` → `Apache-2.0`.
  - No relicensing intended or claimed.

### Cross-model review workflow (commit `ed1595f`)

`claudex-loop` wired in per the `setup` skill:

- `tools/codex_ro.py` — canonical wrapper **2.3.0**, installed via
  `wrapper_drift.py --update` rather than hand-written, so upstream security fixes
  propagate. (Repo was not previously on the drift list.)
- `AGENTS.md` — reviewer + acceptance roles with **11 check points derived from this
  codebase**, not generic ones. Plus the taboo scope (what Codex must not read, since
  everything it reads goes to OpenAI).
- `.codex/README.md` + `knowledge.md` — memory substitute; Codex has no session memory.
- `CLAUDE.md` pointer, `.gitignore` entries, Codex trust entry in `~/.codex/config.toml`.
- **Verified with a live read-only call**: exit 0, `THREAD_ID`, `PING-OK`, no trust prompt.
- The plugin's PreToolUse hook **demonstrated itself** by rejecting a chained wrapper
  invocation (`… && cat …`). The wrapper therefore stays *off* the permission allowlist.
- Step 0 check: this repo has **no** `.claude/settings.local.json`, so there were no
  interpreter wildcards to close.

### Security hygiene

- **Secret pre-commit hook installed** (`_claude/vault/install_precommit_hook.ps1`) and
  tested in **both** directions — a staged fake AWS key was blocked with HEAD unchanged;
  harmless content returned exit 0. A hook that never rejects is indistinguishable from
  no hook.
- Local absolute paths containing the Windows username were removed from `AGENTS.md` and
  `.codex/knowledge.md` **before** committing — this is a public repository.

### Environment

- `.env` created by the operator with a working OpenRouter key. The assistant cannot read
  or write `.env*` here (deny rule in the harness settings) — this is deliberate and was
  not worked around. The prepared file content lives in the session scratchpad.
- **No OpenRouter key exists in Vaultwarden** (all 381 entries checked). Per the
  `credential-vault` rules it belongs there; not yet done.

---

## Key findings (research complete, not yet acted on)

### Upstream divergence

`main` is identical to upstream. But upstream carries
**`claude/refactor-codebase-plan-…`** — 15 commits, Dec 3–6 2025, +6,156/−5,016 lines —
which this fork had never seen. Fetched in as **`upstream-refactor-codebase-plan`**.

| Claim in upstream's `docs/refactoring-plan.md` | Measured on the branch |
| --- | --- |
| `main.py` 3,185 → ~500 | 866 ✓ plausible |
| `app.py` −52% (→ ~1,500) | 2,305 (−26%) |
| `isee-ui.html` −35% (→ ~3,000) | **5,670 (+24%)** |
| Core total −48%, "~2,500 lines removed" | **+104 lines (+0.8%)**, 12,465 → 12,569 |

OpenRouter was **archived, not deleted** (`archive/openrouter-provider/`), and Phase 6
added more UI than Phases 1–5 removed. Real gains do exist: the subprocess pattern is
gone, `provider_manager.py` is genuinely clean, `main.py` really did shrink.

**Decision: do not adopt.** It consolidates on Globant Enterprise AI, and Phase 6 is
unfinished ("response loading TBD"). Its architectural wins are provider-independent and
can be cherry-picked later.

### Globant is not an option for this account

Globant is an IT-services company (NYSE: GLOB); `api.saia.ai` is their enterprise
gateway, formerly *GeneXus Enterprise AI* — which is why `CLAUDE.md` points at
`wiki.genexus.com` for API docs. It is **sales-led**: no self-serve signup, no public
price list, waiting list for early access. The per-request costs quoted in `CLAUDE.md`
came from the original author's account, not from a published tariff. This account has no
access, so any Globant-only path makes the project unrunnable here.

### Model portfolio is obsolete on both branches

Queried the live OpenRouter catalogue: **421 models, 156 of them from 2026**. The config
knows none of them.

```
DEAD:  anthropic/claude-3-sonnet · google/gemini-pro · anthropic/claude-3.5-haiku
       cohere/command-r-plus · x-ai/grok-3-mini-beta
STALE: openai/gpt-4 ($30/$60 per Mtok — 12× the price of gpt-5.6-terra, weaker)
       openai/gpt-3.5-turbo · openai/gpt-4-turbo · anthropic/claude-sonnet-4 · …
```

Two replacement portfolios were costed, each 14 models from **14 different houses**
(house diversity is ISEE's actual purpose). All 28 IDs verified present in the catalogue.

| | @1,500 tok out | @2,500 | @4,000 | lowest output cap |
| --- | ---: | ---: | ---: | ---: |
| A Frontier-Mix | $0.63 | $1.03 | $1.63 | 32,768 |
| **B Budget-Mix (chosen)** | **$0.19** | **$0.31** | **$0.50** | 16,384 |

B hits the cost targets already documented in `CLAUDE.md` ($0.50/run, $0.07/validation)
while using current-generation models throughout.

### Three code defects that block the config update

1. **`max_tokens` is far too low.** Config caps output at 2,048–4,096; every candidate
   model allows ≥16,384, most 65k–943k. 4,096 is 0.4% of what Sonnet 5 can emit, and
   `evaluation_scoring.py` penalises truncated answers as incomplete.
   `max_tokens` is a **ceiling, not a bill** — raising it costs nothing unless models
   actually use the room.
2. **`model_api_integration.py:536-537` forces `temperature = 0.7`** when the config omits
   it, and always writes it into the payload. **`anthropic/claude-sonnet-5` and
   `openai/gpt-5.6-luna` support neither `temperature` nor `top_p`.** OpenRouter drops
   unsupported parameters rather than erroring, so this may pass — but this is exactly
   the failure class that cost this project six consecutive session handoffs on the
   Globant o-series. Do not rely on the gateway's normalisation.
3. **`cost_estimation.py` estimates output as `0.85 × max_tokens`.** After raising the
   ceiling to 16,000 the pre-run estimate would show **$1.66** where **~$0.31** is real.
   The "economic intelligence" the tool advertises would systematically mislead.

### Dead and wrong documentation (for the audit, not for this session)

- The **`cognitive_diversity` block in `openrouter_config.json` (~200 lines)** is read by
  **no code path** — verified. It also references models absent from `api_models`.
- `CLAUDE.md` promised two branches, `feature/raw-response-analysis-to-csv-pipeline`
  ("87 files, 11,823+ insertions") and `archive-remote-main`. **Neither exists anywhere.**
  Corrected in this session.
- `CLAUDE.md` LOC figures are wrong (`main.py`/`app.py` both listed as 2,304; actually
  3,185 / 3,111) and the scoring weights appear in two mutually exclusive versions.
- `CLAUDE.md`'s model table matches neither branch's actual config: it lists
  "Llama 3.3 70B (`awsbedrock/meta.llama3-2-11b`)" — an 11B model labelled 70B.
- An **OpenRouter key prefix sits in clear text** in two session summaries
  (`SESSION-SUMMARY-2025-01-23-01.md`, `-2025-08-22-01.md`). This repo is **public**.
- Repo is public but has **no `SECURITY.md` and no private vulnerability reporting** —
  per the tree-wide rule, enable reporting *first*, then write the file.

---

## Open strategic decision: port the upstream work, or redesign

Declining upstream's branch **must not mean declining its insights**. Two routes are on
the table; the next session should pick one deliberately rather than drifting into the
first.

### Route A — port the optimisations one at a time, adapted to us, on OpenRouter

Each item is taken **individually**, rewritten for our provider situation, reviewed and
committed on its own. Not a merge — a re-implementation with upstream as the reference.

| # | Upstream phase | Portable? | What it means for us |
| --- | --- | --- | --- |
| 1 | Visualisation bug fix | **Yes, unchanged** | `illuminatedCombinations` never resets between runs; framework-name matching uses 8 fallback strategies; race between `current_calls` and `active_parallel_calls`. Provider-independent, pure win, smallest first step. |
| 2 | Provider consolidation | **Inverted** | Upstream consolidated on Globant. Our version is the mirror image: **consolidate on OpenRouter**, remove the Globant paths and the `hybrid` mode. Same simplification, opposite direction. |
| 3 | Extract `isee_engine.py` | **Yes** | Core logic out of `main.py` into an importable module. Provider-independent. Prerequisite for #4. |
| 4 | Eliminate the subprocess pattern | **Yes — biggest win** | `app.py` imports the engine directly instead of spawning `main.py` and parsing its stdout. Removes the parameter-translation layer that is check point 1 in `AGENTS.md` and the subject of `NEXT_SESSION_WEB_UI_CLI_DISCREPANCY_FIX.md`. |
| 5 | UI: cleanup **and redesign** | **List only** | Upstream stripped 347 lines of provider-switching UI. Ours differs (we keep OpenRouter, they kept Globant), so the *list* of what is dead transfers, the diff does not. **Scope is explicitly larger than upstream's** — see below. |
| 6 | Execution Matrix | **Unfinished upstream** | Phase 6 is mid-work ("response loading TBD"). Either finish it ourselves or skip it. Note it *grew* `isee-ui.html` by 24%. |
| — | Model mislabels | **Do our own** | Upstream fixed three (GPT-4 Turbo → GPT-4.1; "DeepSeek Chat V3" that was actually R1; a Claude path separator). We fix ours against the live OpenRouter catalogue instead. |
| — | Flat output layout | **Decide explicitly** | `data/output/run_TIMESTAMP` is simpler, but the current nested layout is a contract with ~7 readers (check point 5 in `AGENTS.md`). Only worth it if all readers move together. |

**Sequence if Route A is chosen**: 1 → 3 → 4 → 2 → 5. Item 1 is independent and proves the
workflow; 3 must precede 4; 2 is cleanest once the subprocess seam is gone.

#### Item 5 in full: the UI is a redesign, not a tidy-up

Explicit scope decision (operator, 2026-09-02): the interface should be brought up to
current UI standards and be **something a person actually enjoys looking at** — not merely
have its dead code removed. Upstream's Phase 5 is a subset of this, not the goal.

Two things have to be said honestly about the starting point:

- **The real obstacle is structural, not stylistic.** `isee-ui.html` is a **4,558-line
  single file** (5,670 on upstream's branch, where Phase 6 made it *bigger*). Markup,
  styling and behaviour live together. Meaningful design work on a file that size means
  splitting it first; otherwise every visual change risks the execution monitoring, and
  the file grows again. Item 5 therefore depends on item 4 — once the backend seam is
  clean, the frontend can be restructured without also chasing subprocess output parsing.
- **`CLAUDE.md` claims the design is already deliberate** ("glass morphism", "amber/slate
  enterprise scheme", "SF Pro Display", "pixel-perfect alignment"). Given how much else in
  that file this session caught being wrong, treat it as a hypothesis. **Look at the
  running interface before designing anything** — which is another reason the validation
  run (priority 4) comes first.

What the interface actually has to carry, and what should drive the design rather than any
style trend:

1. **A live 66-call execution view** — the current one has known bugs (Phase 1: state that
   never resets, 8 fallback name-matching strategies, a race in call tracking). It is the
   screen a user watches for minutes at a time; it deserves the most attention.
2. **Cost before commitment** — the pre-run estimate is the product's own promise
   ("Economic Intelligence"). Note defect 3 above: it currently would lie.
3. **66 results without drowning the reader** — the Cognitive Diversity Explorer exists
   for this and is a second, separately styled surface. A redesign should decide whether
   these are one interface or two; today they are two pretending to be one.
4. **Long-running work** — minutes, not seconds. Progress, partial results, and failure of
   individual calls need to be legible without a page reload.

When this is picked up, use the `frontend-design` skill for the aesthetic direction rather
than defaulting to whatever a component library ships with — the point of the exercise is
that it should not look templated.

### Later step (either route) — EU-resident hosting for GDPR / EU AI Act

Not for the next session, but it shapes how the provider layer should be built, so it is
recorded here rather than discovered later.

**The concern**: OpenRouter is a US gateway. That is fine for abstract research questions.
It is not the channel for prompts carrying personal data or client-confidential material —
and ISEE writes everything it sends into `queries_detailed_*.csv` and the raw response
files, so whatever goes in is also persisted.

**The observation that matters**: this is exactly what Globant was selling. Its model IDs
are literally `awsbedrock/anthropic.claude-3-5-haiku`, `azure/gpt-4.1`,
`vertex_ai/gemini-2.5-pro`, `azure_ai_foundry/grok-3-mini` — a multi-hyperscaler gateway.
Upstream's instinct was the same one; the difference is reseller versus own contract.
**The routing mechanism therefore already exists in this codebase.** What changes is the
account, the DPA and the region — not the architecture.

**AWS and Azure are not interchangeable**, and neither alone covers the current portfolio:

| | EU regions | Houses available |
| --- | --- | --- |
| AWS Bedrock | Frankfurt (`eu-central-1`), Ireland (`eu-west-1`) | Anthropic, Meta, Mistral, Amazon, Cohere, DeepSeek — **no OpenAI** |
| Azure AI Foundry | Sweden Central, West Europe, Germany West Central | OpenAI, plus Grok, Mistral, Llama — **no Bedrock catalogue** |

**Design consequence — do not replace OpenRouter, tier it.** The provider layer should
route by *data class*, not globally:

1. **Open** — abstract research questions → OpenRouter, full 14-house diversity, cheapest.
2. **Confidential** — client or personal data → EU-resident Bedrock/Azure under our own
   contract, smaller portfolio accepted as the price of residency.
3. **Sensitive** — nothing leaves the machine → local inference. Note that
   `openrouter_config.json` already carries an unused `ollama_models` block (4 entries);
   the seam exists. The claudex-loop fallback reviewer uses the same principle.

Cognitive diversity is reduced in tiers 2 and 3. That is a real trade-off, not a
formality: fewer houses means less of exactly what ISEE exists to produce. It should be a
conscious choice per query, which is why it belongs in the provider layer rather than in a
global switch.

**Prerequisite before any of this**: decide what data actually enters prompts. If ISEE
only ever receives abstract questions, tier 1 suffices and this whole step is optional.

⚖️ **Not legal advice.** Which obligations apply — controller/processor roles, whether a
DPA is required, the deployer-vs-provider classification under the EU AI Act, and any
documentation duties — is a question for whoever handles that, not something to settle
from the code side. What is recorded here is only the technical shape that keeps those
options open.

### Route B — redesign on current technology

The codebase encodes assumptions from early 2025 that have since expired. A redesign
would revisit them rather than porting them:

- **Context windows are now ~1M tokens**, not 8k–128k. The whole architecture of 66
  isolated single-shot calls, each ignorant of the others, was a workaround for small
  contexts. With 1M context a synthesis pass can read *all* perspectives at once instead
  of the current cluster-and-summarise pipeline.
- **`max_tokens` 4,096** (see defect 1) is a relic of the same era.
- **Batch pricing exists**: OpenRouter lists `:batch` variants of most models at roughly
  **half price**. ISEE's 66 independent calls are the textbook batch workload — nothing in
  the current code knows these exist.
- **Reasoning models are now the default class**, and several reject the sampling
  parameters this code hardcodes (defect 2). The parameter layer needs rethinking, not
  patching.
- **Structured outputs / JSON schema** would replace the fragile text parsing in
  `evaluation_scoring.py` and `cognitive_diversity_extractor.py`, including the template
  and placeholder detection built to compensate for it.
- **Dead weight to shed rather than port**: the ~200-line unread `cognitive_diversity`
  taxonomy, the `ollama_models` block, `openrouter_rankings_service.py` (already marked
  obsolete in `CLAUDE.md`), and the ~25 stray Markdown files in the repository root.

### Honest comparison

Route A is incremental, reviewable, and each step is independently valuable — if it is
abandoned halfway the repository is still better off. Route B addresses the fact that the
*premise* of the architecture (small contexts, expensive tokens, non-reasoning models) no
longer holds, but it is a rewrite: no partial value, and it discards a working system for
a hoped-for one.

**Recommendation for the next session**: neither yet. Do priorities 1–4 below first
(config + three code defects + a validation run). They are prerequisites for *both*
routes, they are cheap, and after them we will have something the current repository does
not have — **a run we have actually observed**. Choosing between porting and redesigning
without that is choosing on the strength of documentation this session has repeatedly
caught being wrong.

---

## Next session priorities

- [ ] **1. Rewrite `models.api_models` in `openrouter_config.json`** — Budget-Mix B,
      14 models, `max_tokens` 16000 (bounded by `meta/muse-glimmer-30b` at 16,384).
      Omit `temperature`/`top_p` for Sonnet 5 and GPT-5.6-luna.
      Schema per entry: `id`, `name`, `provider`, `requires`, `parameters`, `features`,
      `cost_tier`, `strategic_order`. Fields actually consumed by code: `cost_tier` (78
      hits), `features` (65), `strategic_order` (validation script), `ui_priority` (3).
      `nate_semantic`/`nate_use_case` are dead — drop them.
      `cost_tier` vocabulary: `budget` / `standard` / `premium` / `premium_plus`.
      Feature vocabulary the code filters on: `reasoning`, `fast`, `balanced`, `analysis`,
      `multimodal`, `coding`, `creative`, `large_context`, `efficient`, `cost_efficient`.
      Old config recoverable from git (`a35f081`) — no separate backup file needed.
- [ ] **2. `model_api_integration.py`** — stop forcing `temperature`; send sampling
      parameters only when the config supplies them.
- [ ] **3. `cost_estimation.py`** — replace the `0.85 × max_tokens` heuristic; the ceiling
      is no longer a usable proxy for actual output.
- [ ] **4. Validation run**, 11 calls (~$0.07), `--provider openrouter`. Confirm the
      framework starts at all before spending reviewer budget on it.
- [ ] **5. Then** `/claudex-loop:audit` on `main`.
- [ ] **6. Decide Route A vs Route B** (see "Open strategic decision" above) — porting
      upstream's optimisations one by one on OpenRouter, or a redesign on current
      technology. Decide *after* 1–4, with an observed run in hand.
- [ ] Optional: store the OpenRouter key in Vaultwarden as
      `uj-isse-meta-framework/openrouter_api_key`, round-trip verified.
- [ ] Optional: enable private vulnerability reporting, then add `SECURITY.md`.

---

## Configuration notes

- **Provider**: OpenRouter only. `--provider globant` and `--provider hybrid` have no
  credentials and will fail.
- **Attribution headers**: `OPENROUTER_SITE_URL` → `HTTP-Referer`, omitted when unset.
  `OPENROUTER_APP_NAME` → `X-Title`, **defaults to "ISEE Meta Framework"** so the header
  is sent even when the variable is absent; set it empty to suppress. Both are optional
  and affect only the public rankings on openrouter.ai. Setting a distinct app name is
  worthwhile for cost attribution in the OpenRouter dashboard.
- **Cost model**: ~350 input tokens/call; output currently estimated at
  `0.85 × max_tokens` (see defect 3). 66 calls per standard run, 11 per validation.
- **Codex quota** at session end: 5-hour window 0% used, weekly 4%.

## Quick-start commands

```bash
./scripts/dev-server.sh start                      # web UI on :5001
python main.py --query "..." --models 3 --provider openrouter   # fast CLI check

# plan review before risky changes (always via the wrapper, never bare `codex exec`)
python tools/codex_ro.py --prompt-file "$SCRATCH_DIR/p.txt" \
  --out-file "$SCRATCH_DIR/verdict-r1.txt" --err-file "$SCRATCH_DIR/err-r1.txt"

# drift check on the wrapper copy
python "<plugin>/scripts/wrapper_drift.py" --repo .
```

## Session assessment

- **Progress**: preparation complete, execution not started. Every decision the next
  session needs has been made and the supporting measurements are recorded above.
- **Momentum**: ready to continue — priorities 1–3 are mechanical, given the schema and
  vocabulary noted above.
- **Confidence**: high for 1–4. The audit itself (5) remains genuinely open work.
- **Caveat**: all cost figures derive from ISEE's own estimation assumptions, not from
  observed runs. Reasoning models are frequently more verbose than assumed. Treat them as
  order-of-magnitude, not as a quote.
