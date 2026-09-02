# Plan: Make ISEE runnable — and make its failures and costs visible

_Round 1 — revised by Claude after Codex review_

## What Round 1 changed

The original plan assumed the only blocker was stale model IDs, and that a validation run
would prove the fix. Codex showed that assumption is false in a way that invalidates the
plan's own verification step, and I confirmed each claim in the code:

- **`main.py:1369-1371` turns a detected API error into a *simulated* response** and
  prints "Falling back to simulation". A run in which all 14 models return HTTP 400 would
  be reported as a complete, successful run. The planned validation could not have proven
  anything.
- **The cost figure users see is a hardcoded constant** — `main.py:2264` and `app.py:648`
  both use `0.08` per combination. `cost_estimation.py`, whose output-token heuristic the
  original plan set out to fix, does not feed that display at all. There are two
  independent cost paths and I had planned to fix the one nobody sees.
- **`validate_expanded_config.py` validates the *Globant* config**, requires 15 models,
  and prints `api_key[:20]` plus the full org ID to stdout (line 118). The original plan
  named it as the verification step for an OpenRouter change.
- **`app.py:216` selects only entries with `ui_priority == "strategic"`**; the original
  schema omitted that field, which would have emptied the Web UI's curated portfolio.
- **`app.py:_get_fallback_models` pads any config under 20 entries** with a hardcoded list
  containing `google/gemini-2.0-flash` and `anthropic/claude-3.7-sonnet` — so a 14-model
  config still surfaces obsolete IDs in the UI.
- **`main.py:242` retries three times**, so one logical call can bill three times, and
  `model_api_integration.py` never reads `usage` from the response, so real consumption is
  discarded.

The goal is therefore larger than "swap the model list": **the instrument has to stop
lying before it is worth measuring.** Scope grew accordingly, and the phases are ordered so
that nothing is verified with a tool that cannot detect its own failure.

## Goal

Produce a run of ISEE that we have *observed*, whose failures are visible as failures, and
whose reported cost bears a defined relationship to the actual invoice. Everything else —
the audit, porting upstream's refactor, any redesign — depends on having that.

## Approach

### Phase A — Make failure visible (prerequisite for every later verification)

**A1.** `main.py:1369-1375` and `main.py:1249-1257`: a detected API error or a missing
client must no longer silently become a simulated response. Simulation becomes opt-in via
an explicit `--simulate` flag. Without it, the combination is persisted as an explicit
failure carrying model ID, provider, HTTP status and the error text, and the run summary
reports the failure count. A run where every call failed must be impossible to mistake for
a successful one.

**A2.** `main.py:242-306`: the three-tier retry stays, but the attempt count is recorded on
each result so that billing and success rates can be read afterwards.

**A3.** `model_api_integration.py`: read `usage` (`prompt_tokens`, `completion_tokens`)
from the OpenRouter response and return it alongside the text, instead of discarding it.
This is what makes any cost claim checkable rather than asserted.

**A4.** `validate_expanded_config.py:118`: stop printing `api_key[:20]`. This is a public
repository; a validator that prints 20 characters of a live key is a defect regardless of
this plan. One-line fix, taken here because it is in a file the plan touches.

### Phase B — Replace the model portfolio

**B1.** Replace all 17 `models.api_models` entries with the 14 below, one per house. All
IDs verified against a live fetch of `https://openrouter.ai/api/v1/models` (421 models,
2026-09-02).

| # | Model ID | House | $/Mtok in/out | cost_tier | ui_priority |
| --- | --- | --- | --- | --- | --- |
| 1 | `anthropic/claude-sonnet-5` | Anthropic | 2.00 / 10.00 | premium | strategic |
| 2 | `openai/gpt-5.6-luna` | OpenAI | 0.20 / 1.20 | standard | strategic |
| 3 | `google/gemini-3.5-flash-lite` | Google | 0.30 / 2.50 | standard | strategic |
| 4 | `x-ai/grok-4.3` | xAI | 1.25 / 2.50 | standard | strategic |
| 5 | `deepseek/deepseek-v4-flash-0731` | DeepSeek | 0.07 / 0.18 | budget | strategic |
| 6 | `qwen/qwen3.7-plus` | Alibaba | 0.32 / 1.28 | standard | strategic |
| 7 | `z-ai/glm-5.3-flash` | Zhipu | 0.07 / 0.25 | budget | strategic |
| 8 | `moonshotai/kimi-k2.6` | Moonshot | 0.95 / 4.00 | standard | strategic |
| 9 | `mistralai/mistral-small-2603` | Mistral | 0.15 / 0.60 | budget | standard |
| 10 | `meta/muse-glimmer-30b` | Meta | 0.30 / 1.20 | standard | standard |
| 11 | `nvidia/nemotron-3.5-lightning` | NVIDIA | 0.08 / 0.20 | budget | standard |
| 12 | `minimax/minimax-m3` | MiniMax | 0.30 / 1.20 | standard | standard |
| 13 | `upstage/solar-pro4` | Upstage | 0.03 / 0.12 | budget | standard |
| 14 | `tencent/hy3` | Tencent | 0.13 / 0.53 | budget | standard |

Fields per entry: `id`, `name`, `provider`, `requires`, `parameters`, `features`,
`cost_tier`, `ui_priority`, `strategic_order`. `nate_semantic` / `nate_use_case` dropped
(referenced nowhere in active code — a claim to be re-checked against the readers listed as
unopened in the Round 1 review). `features` restricted to the vocabulary the code filters
on. `parameters.max_tokens = 16000`; `temperature`/`top_p` present for 12 entries, absent
for `anthropic/claude-sonnet-5` and `openai/gpt-5.6-luna` (see D3).

**B2.** `app.py:_get_fallback_models`: remove the `len(models) < 20` padding with hardcoded
model IDs. A configuration of 14 models means 14 models; padding with stale IDs presents
models the framework cannot call.

**B3.** `models.ollama_models`: set `"disabled": true` with a `disabled_reason` on all four
entries. `main.py:462-464` loads them into the same selection pool as `api_models`, and
`main.py:469-473` already honours the flag.

**B4.** `model_api_integration.py:535-537,559`: send `temperature` and `top_p` only when
the config supplies them, matching how `presence_penalty` / `frequency_penalty` / `stop`
are already handled at lines 562-564. `max_tokens` keeps its default.

**B5.** `--provider globant` and `--provider hybrid` must fail with a clear message when no
Globant credentials are present, instead of proceeding. Note the limitation Codex
identified: `main.py` builds clients from each config entry's own `provider` field, so
`--provider` does not actually route execution. Repairing that is Route A item 2 and is
**out of scope here**; making the unsupported modes fail loudly is the cheap containment.

### Phase C — One cost path, honest about what it does not know

**C1.** Remove the hardcoded `0.08` per combination from `main.py:2264` and `app.py:648`.
Both call the same estimator, driven by the actually selected model IDs and the final
combination count.

**C2.** `cost_estimation.py`: introduce an explicit pricing provider injected into
`CostEstimator` rather than relying on `OpenRouterClient`'s private `_models_cache`, which
the estimator neither owns nor receives. Defined semantics: TTL, behaviour on fetch
failure, and behaviour on an unknown model.

**C3.** Prices from OpenRouter's `/models` endpoint are **per token, as decimal strings**.
Parse with `Decimal` and convert to per-million explicitly. A missing factor of 1,000,000
is a six-order-of-magnitude error that would look like a working feature. Covered by a
fixture test with a known price.

**C4.** Seed the static table from a live fetch so it starts correct, and change the
unknown-model path: exact match or **"price unavailable"**. The current fallback prices
unknown OpenRouter models as Anthropic models — for `upstage/solar-pro4` that is wrong by
roughly 60×. A missing number is honest; a confident wrong one is not.

**C5.** `_estimate_response_tokens` (line 487) returns `0.85 * max_tokens`. At
`max_tokens = 16000` that predicts 13,600 output tokens per call. Replace with
`min(0.85 * max_tokens, TYPICAL_RESPONSE_TOKENS)`, `TYPICAL_RESPONSE_TOKENS = 2500`,
labelled in the output as an unmeasured assumption. Phase A3 produces the data to replace
it; until then the estimate is presented as a range, not a figure.

**C6.** Estimates must account for retries (up to 3 attempts per call, A2) — otherwise the
estimate is a floor being presented as a total.

### Phase D — Tests before any paid run

Mocked, no network, no credentials:

1. Request payload contains no `temperature` / `top_p` for the two models that omit them,
   and does contain them for one that supplies them.
2. An HTTP 400 produces a persisted failure, **not** a simulated response, when
   `--simulate` is absent.
3. `openrouter_config.json` loads and yields exactly 14 enabled models; the four
   `ollama_models` are skipped.
4. `_filter_strategic_models` returns a non-empty set, and no returned model ID is outside
   the configured 14.
5. Price conversion against a fixed fixture; unknown model yields "price unavailable"
   rather than a guessed price.
6. Pricing cache: hit, expiry, and fetch failure.

Replaces the original plan's use of `validate_expanded_config.py`, which validates a
different configuration and requires credentials.

### Phase E — The measured run

1. **Smoke test, 14 calls**: one template × one domain × 14 models, explicit
   `--config openrouter_config.json`, `--provider openrouter`. Asserts every model answers
   for real. Expected cost well under $0.10.
2. **Bounded validation run** with an explicit combination cap.
3. Record, in the review log: displayed estimate, attempts made, `usage` totals from A3,
   and the actual OpenRouter dashboard figure. **This is the project's first measurement**
   — every cost number in `CLAUDE.md`, in this plan, and in the tool itself is currently an
   assumption.

## Key decisions & tradeoffs

**D1 — Budget tier.** ~$0.19–0.31 per 66-call run against $0.63–1.03 for the frontier
variant. The immediate goal is an observed run, not the best answer. Upgrading is a table
swap. Counter-argument: if a real research question is run on it, quality is traded for
~$0.70.

**D2 — `max_tokens` 16000 uniformly.** Current 2048–4096 against models allowing
16k–943k; `evaluation_scoring.py` penalises truncation, so the cap distorts scores. 16000
is the lowest ceiling in the portfolio (`meta/muse-glimmer-30b`, 16,384), so one value is
valid everywhere. Per-model values were rejected as asymmetry in an instrument built to
compare models.

**D3 — Capability facts live in the config, not in a lookup table.** Upstream hardcoded a
"reasoning models" set for the Globant o-series; that set goes stale exactly as the model
list did. Counter-argument: OpenRouter drops unsupported parameters anyway, so this may be
unnecessary — but Phase A1 means we would now *see* it if it were not, which is the
point.

**D4 — Scope grew, deliberately.** Phases A and C were not in the original plan. Without A
the verification step is meaningless; without C the plan fixes an invisible number and
leaves the visible one hardcoded. The alternative — ship B alone and call it done — would
produce a run we cannot trust and a cost display that is wrong by roughly 17× on this
portfolio.

**D5 — Deferred, with reasons.** Routing execution through `ProviderManager` (a refactor,
Route A item 2). Removing the Globant paths (same). The unlocked delete-and-recreate in
`main.py:update_latest_symlink` (concurrent runs are not part of this change — recorded as
an audit finding). Adding token/cost columns to `performance_tracking.db` (A3 makes the
data available; persisting it is the next step, not this one).

## Risks / open questions

- **R1** — Phase A1 changes failure semantics; downstream readers (`reporting.py`,
  `evaluation_scoring.py`, the Explorer) may assume every combination has response text. A
  persisted failure must not crash them. Not yet verified.
- **R2** — `TYPICAL_RESPONSE_TOKENS = 2500` remains a guess until Phase E.
- **R3** — `MODEL_ALIASES` matching is a substring test; the 14 new IDs must be checked
  against it for accidental hits.
- **R4** — `features` values feed selection in ~65 places not yet read; wrong values could
  quietly change which models serve which framework.
- **R5** — Codex's Round 1 review did not open `openrouter_model_collections.py`,
  `openrouter_rankings_service.py`, `openrouter_categorization.py`, `isee-ui.html`,
  `reporting.py`, `query_export.py`, `analysis.py`, `organize_runs.py`,
  `undo_organization.py`, `launch_cognitive_explorer.py`. Several are plausible readers of
  the model config. The claim that dropped fields are "referenced nowhere" is therefore
  **not established** and must be checked before B1 lands.
- **R6** — The first run may still fail for reasons unrelated to any of this.
- **R7** — Every cost figure here derives from assumptions, not observation. That is the
  condition Phase E exists to end.

## Out of scope

Upstream's refactoring branch (Route A) · any redesign (Route B), including batch pricing
and long-context synthesis · removing the Globant provider paths · routing execution
through `ProviderManager` · the dead `cognitive_diversity` taxonomy (~200 lines, no
reader) · the UI redesign · EU-resident provider tiering · `SECURITY.md` and private
vulnerability reporting · the key prefix committed in two session summaries (history
rewrite, its own decision).
