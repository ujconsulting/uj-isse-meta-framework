# Plan Review Log: Model refresh + parameter/cost defects

Started 2026-09-02 (session start). MAX_ROUNDS=5.
Reviewer: codex gpt-5.6-terra / effort=high / sandbox=read-only (role `plan-review`).
Plan: `docs/plans/2026-09-02-modell-refresh.md`


## Round 1 — Codex (gpt-5.6-terra/high, read-only)

Plan reviewed: sha256 `258840d8dc1228860bf220ca6281fc3ae65084eb550e40f41fa015a14014686b`

Material problems:

- `validate_expanded_config.py` validates `globant_enterprise_config.json`, requires exactly 15 models, loads `.env`, and prints a key prefix/organization ID; it cannot validate this 14-model OpenRouter change and violates secret-handling policy.  
  Fix: replace it with an offline OpenRouter-config schema test that never reads or prints credentials.

- The proposed command omits `--config openrouter_config.json`; `main.py` then has no model configs and falls back to simulated responses, so it cannot prove a real run.  
  Fix: pass the OpenRouter config explicitly and assert every result is non-simulated.

- “11 calls” and “all 14 models answer” are mutually impossible; additionally the command supplies neither a domain/template restriction nor `--max-combinations 11`, so defaults produce far more combinations and guardrails may reject it.  
  Fix: use a 14-call, one-template/one-domain/zero-variation smoke test for all models, plus a separate bounded 11-call validation test.

- `main.py:_generate_model_response` converts *any* client failure or detected API-error text into a simulated response, including a 400 caused by unsupported sampling parameters; reports then look successful.  
  Fix: permit simulation only with explicit `--simulate`; otherwise persist an explicit failed result with provider, HTTP status, and model ID.

- Step 1 omits `ui_priority` despite acknowledging it; `app.py:_filter_strategic_models` selects only entries with `ui_priority == "strategic"`, so Smart Auto-Pilot can become empty.  
  Fix: define the intended strategic subset with `ui_priority: "strategic"` and add a Web-UI selection regression test.

- `app.py:_get_fallback_models` pads a config smaller than 20 with stale hard-coded model IDs; replacing the config with 14 entries therefore still exposes obsolete models in the UI.  
  Fix: remove/update that padding and test the returned manual and strategic portfolios contain only supported IDs.

- The plan changes OpenRouter IDs but leaves `provider_manager.py`’s bidirectional mappings stale; worse, `main.py` creates clients directly from each config’s `provider`, so `--provider hybrid`/`globant` does not control actual execution.  
  Fix: either make execution route through `ProviderManager` with explicit mappings and parameter translation, or reject unsupported provider modes for this portfolio visibly.

- “Use the existing 300-second cache” is not an implementation path: it is an instance field on `OpenRouterClient`, while `CostEstimator` neither owns nor receives that client.  
  Fix: inject one pricing provider into `CostEstimator`, define cache lifetime/failure semantics, and unit-test cache hit, expiry, and fetch failure.

- The planned pricing fix still does not repair the displayed pre-run estimate: CLI guardrails use hard-coded `$0.08` per combination, while `CostEstimator._get_available_models_for_params()` ignores `selected_models` and estimates arbitrary first-loaded config entries.  
  Fix: make CLI and Web estimates use one model-aware estimator driven by the final selected IDs and final combination cap.

- The plan does not specify conversion of OpenRouter endpoint pricing to the table’s “USD per million tokens” unit; a missing `×1,000,000` creates a six-order-of-magnitude estimate error.  
  Fix: parse prompt/completion prices as `Decimal`, convert units explicitly, and test an exact known-price fixture.

- The static fallback remains unsafe: an unknown OpenRouter model falls through to Anthropic-like pricing, merely labelled stale.  
  Fix: fall back only to an exact static match; otherwise return “price unavailable” and block cost-sensitive execution unless the user explicitly accepts it.

- The proposed 2,500-token ceiling is unmeasured and actual response usage is discarded by `OpenRouterClient.generate`; retries in Web parallel mode can make up to three billable requests per logical call.  
  Fix: retain and record API usage/attempt counts, price retries, and label estimates as ranges until measured data exists.

- No tests cover the changed contract: omitted sampling fields, exact request payloads, no-simulation-on-400, OpenRouter config loading, strategic UI selection, pricing conversion, or cache fallback.  
  Fix: add mocked unit/integration tests for each path before any paid validation.

- The plan changes the supported portfolio, execution cost, and validation procedure but names no documentation updates.  
  Fix: update the measured model/cost guidance in `README.md`, `README_DE.md`, `CLAUDE.md`, and relevant `docs/configuration/` pages.

Shared-resource audit:

| Resource | Writers found | Plan leaves unfixed |
|---|---|---|
| `openrouter_config.json` | This plan; `archive/rich-cli-phase/update_config_domains.py` is a writer candidate | UI strategic filtering, stale UI padding, config-selection parity, and active-reader tests |
| OpenRouter in-memory `_models_cache` | `model_api_integration.py:OpenRouterClient.get_available_models` | No estimator integration, no cache observability, no defined stale/failure result |
| Run directory / `data/output/latest` | `main.py`; `app.py` creates a different flat run directory before launching `main.py` | No Web-UI regression; `main.py:update_latest_symlink` deletes then recreates the link without a lock, so concurrent runs can leave it absent or stale |
| `data/performance_tracking.db` | `performance_tracker.py`; indirectly `app.py` after a successful subprocess | CLI validation does not ingest it, and it has no actual token/cost column to support the promised measurement |

I opened the active relevant files: `main.py`, `app.py`, `model_api_integration.py`, `provider_manager.py`, `cost_estimation.py`, `validate_expanded_config.py`, `performance_tracker.py`, `tests/test_globant_integration.py`, and the relevant portions of both provider configs.

I did not open `archive/rich-cli-phase/update_config_domains.py` (archive is prohibited), nor `openrouter_model_collections.py`, `openrouter_rankings_service.py`, `openrouter_categorization.py`, `isee-ui.html`, `reporting.py`, `query_export.py`, `analysis.py`, `organize_runs.py`, `undo_organization.py`, `launch_cognitive_explorer.py`, or any protected `data/output/**`, report, database, `.env`, or archive contents. Those unreviewed readers/writers are an additional reason not to treat the plan’s “referenced nowhere” claims as established.

VERDICT: REVISE

### Claude's response — Round 1

Every checkable claim was verified in the code before acting on it. All held.

**Accepted (13 of 13 material findings), with what changed:**

| Finding | Verified at | Change |
| --- | --- | --- |
| Simulation masks API errors | `main.py:1369-1371` — prints "Falling back to simulation", returns `_simulate_model_response` | New **Phase A1**: simulation becomes opt-in `--simulate`; otherwise a persisted failure with model, provider, status. Promoted to prerequisite — without it the plan's own verification step proves nothing. |
| `validate_expanded_config.py` wrong target + secret print | line 29/101 open `globant_enterprise_config.json`; line 118 prints `api_key[:20]`, line 119 the full org ID | Removed from verification. Replaced by Phase D mocked tests. Secret print fixed in **A4** — public repo. |
| Missing `--config` → simulation | `main.py` arg default | Explicit `--config openrouter_config.json` in **Phase E**. |
| "11 calls" and "all 14 models" contradictory | plan's own text | Split: 14-call smoke test, then a bounded validation run. |
| `ui_priority` omitted | `app.py:216` filters `== 'strategic'` | Added to the schema with the strategic subset defined (**B1**). |
| Stale hardcoded UI padding | `app.py:_get_fallback_models`, `if len(models) < 20` pads `google/gemini-2.0-flash`, `anthropic/claude-3.7-sonnet` | **B2**: padding removed. |
| Cache is not reachable by the estimator | `_models_cache` is an `OpenRouterClient` instance field | **C2**: explicit injected pricing provider with defined TTL/failure semantics. |
| Displayed cost is a hardcoded constant | `main.py:2264` and `app.py:648` both `0.08` per combination | **C1**: both paths unified onto the estimator. This is the real cost defect; the original plan fixed the invisible path. |
| Missing unit conversion | OpenRouter returns per-token decimal strings | **C3**: `Decimal` + explicit ×1e6 + fixture test. |
| Unsafe static fallback | unknown OpenRouter model → `_get_base_provider_cost(..., "anthropic")` | **C4**: exact match or "price unavailable". Static table seeded from a live fetch. |
| Retries billable, usage discarded | `main.py:242` three-tier retry; `model_api_integration.py` reads only `choices[0].message.content` | **A2** records attempts, **A3** captures `usage`, **C6** prices retries. |
| No tests | — | **Phase D**, six mocked tests, before any paid run. |
| No documentation updates named | — | Named: `README.md`, `README_DE.md`, `CLAUDE.md`, `docs/configuration/`. |

**Partially accepted:**

- *`--provider` does not control execution; `ProviderManager` mappings stale.* Confirmed —
  `main.py` builds clients from each config entry's own `provider`. Repairing this is a
  refactor (Route A item 2) and is **deferred with the limitation written into the plan**;
  **B5** contains it by making unsupported provider modes fail visibly. Rejecting the full
  fix here is a scope decision, not a disagreement.

**Deferred, with reasons recorded in the plan (D5):**

- `main.py:update_latest_symlink` unlocked delete-then-recreate — concurrent runs are not
  part of this change; recorded as an audit finding.
- `performance_tracking.db` has no token/cost column — A3 makes the data available;
  persisting it is the following step.

**Adopted as a risk rather than a fix:** the reviewer's list of unopened files
(`openrouter_model_collections.py`, `openrouter_rankings_service.py`,
`openrouter_categorization.py`, `isee-ui.html`, `reporting.py`, `query_export.py`,
`analysis.py`, `organize_runs.py`, `undo_organization.py`, `launch_cognitive_explorer.py`)
is now **R5**: the claim that dropped config fields are "referenced nowhere" is explicitly
marked not established, to be checked before B1 lands.

**Nothing was rejected.** The plan roughly doubled in scope as a result (Phases A and C did
not exist in Round 0).


## Round 2 — Codex (gpt-5.6-terra/high, read-only, resumed session)

Plan reviewed: sha256 `973842b9a175f62751b42dcfb6c2f3d7b4dfe42c581bb8ba93d01a3a516aebb0`

Material problems remain.

- A1 has no complete failure-result contract. `main.py:evaluate_results()` reads `result["response"]` unconditionally; a persisted failure without response text aborts evaluation, synthesis, reports, and can prevent the run summary A1 relies on.  
  Fix: define `status: succeeded|failed`, skip failed records in evaluation/synthesis, and test an all-failure run through reports and analysis.

- `save_raw_response()` writes missing responses as the literal “Response not available”; `cognitive_diversity_extractor.py` then indexes and ranks that placeholder as a real response.  
  Fix: do not emit a raw-response file for failures, or use a separately marked failure artifact that the Explorer excludes and counts.

- Parallel execution still reports false success: `ParallelExecutionEngine.execute_single_combination()` increments `completed_count` for any returned dict, including `{"error": ...}`, and its final `success_rate` uses that counter.  
  Fix: increment a success counter only for `status == "succeeded"` and emit one normalized terminal event with explicit status/attempts.

- The Web UI has a second false-success path: `app.py:execute_isee_command()` marks the run completed solely when the subprocess exit code is zero. A fully failed but gracefully persisted run can therefore display “Execution completed successfully.”  
  Fix: make `main.py` return a machine-readable run outcome and have `app.py` expose `completed_with_failures`/`failed`, not success, when any combination fails.

- `app.py:_monitor_subprocess_progress()` does not handle `combination_failed_parallel`; it only handles completion event names.  
  Fix: either emit `combination_complete_parallel` with `success: false` for all terminal failures or add explicit handling and failure counters in the monitor.

- A1 promises HTTP status, but `ModelAPIClient._handle_error()` discards the status for JSON error responses and raises an exception containing only the message.  
  Fix: give `APIIntegrationError` structured `status_code`, provider, and retryability fields, with `None` only for failures before an HTTP response exists.

- A3 changes a public return contract without specifying it. Every current `generate()` caller expects a string (`main.py` calls `len()` and error detection on it; `ProviderManager` and examples do likewise). “Return usage alongside text” will break them if implemented as a tuple/dict.  
  Fix: introduce one typed generation-result object and update every client/caller, with `usage=None` for providers that cannot report it.

- A3 still does not state where usage survives after the process exits. Current result metadata, raw-response files, CSV exports, and reports do not persist usage totals.  
  Fix: store usage and attempts in the normalized result record and export them in run summary/CSV before deferring database schema work.

- Phase C does not yet establish one cost path. `ISEEGuardrails.estimate_cost()` remains the CLI pre-run path and is also invoked by Web estimation for warnings; `/api/estimate` additionally logs `estimate.get("estimated_cost", 0)` even though the estimator returns `total_cost`, producing a false zero-cost analytics record.  
  Fix: route guardrails and API analytics through the same estimate object, use `total_cost`, and add a test proving all public estimate endpoints agree.

- C’s tests do not verify the key selection contract: the estimator must use the final `selected_models`, not arbitrary config entries or all root `*config*.json` files.  
  Fix: add a fixture with selected OpenRouter and Globant entries proving only the requested IDs contribute to the estimate.

- R1 is acknowledged but not scheduled before B/E; Phase D lacks the required downstream failure fixture, so D can pass while an actual HTTP 400 crashes the pipeline or produces a deceptive Explorer record.  
  Fix: make an all-failure end-to-end mocked pipeline test a Phase-D gate, including reporting, CSV, analysis, and Explorer extraction.

- R3–R5 are merely risks, not work items, yet B1 removes metadata and installs the portfolio before their readers are checked. This is not a sound phase order.  
  Fix: add a pre-B reader audit and compatibility tests as explicit gates, not prose risks.

- The active UI can still select stale/non-portfolio models through `OpenRouterRankingsService`’s persisted rankings cache, fallback list, and `/api/models-fresh`; `_process_model_params()` then creates dynamic configs with default sampling parameters. B2 only removes one separate padding mechanism.  
  Fix: constrain all UI selection sources to the configured 14, or update and test every rankings/cache/fallback source before B lands.

- B5 is not fail-closed: it rejects Globant/hybrid only when credentials are absent, but when credentials are present the known non-routing behavior remains.  
  Fix: reject `globant` and `hybrid` unconditionally in this release until routing is implemented, and test the CLI/Web boundary.

- The `latest` symlink deferral is defensible for this single non-concurrent CLI smoke test. The database-schema deferral is defensible only after usage/attempt data is durably written to run artifacts; the plan does not yet do that.

- The revised plan says documentation updates were accepted, but it still contains no documentation phase or named files.  
  Fix: add a final documentation step for measured portfolio/cost claims and explicitly update the affected README/CLAUDE/configuration guides.

VERDICT: REVISE

### Claude's response — Round 2: loop paused for a scope decision

Verified in code before responding; every checked claim held:

| Claim | Verified at | Verdict |
| --- | --- | --- |
| `evaluate_results` reads `response` unconditionally | `main.py:1491` — `text = result["response"]` | TRUE — an all-failure run raises `KeyError` |
| Failures written as a placeholder | `main.py:1039` — `f.write(result.get("response", "Response not available"))` | TRUE — the Explorer then indexes and ranks that string |
| Parallel engine counts errors as completed | `main.py:265` `completed_count += 1`; `success` computed at 269 and never gates it; `success_rate` at 184 | TRUE |
| Web UI success from exit code alone | `app.py:957-958`, `994` | TRUE |
| Third cost path | `main.py:2257` `ISEEGuardrails.estimate_cost`, hardcoded `0.08` at 2264 | TRUE |
| `--simulate` needs introducing | `main.py:2620` — **already exists** | Claude's Round-1 wording was imprecise: the flag exists; the defect is that simulation *also* happens implicitly on error |

`main.py:264-265` is the textbook case the review prompt asks for: the comment
`# Success - update counters and return` sits directly above `completed_count += 1`,
while `success` is computed two lines later and never used to gate the counter.

**Why the loop is paused at Round 2 of 5 rather than run to APPROVED:**

The two rounds have converged on a conclusion about **scope**, not about plan details.
The initial task was "5 model IDs are dead, replace them". What the review established is
that **ISEE cannot distinguish a successful run from a completely failed one**, in four
independent places (API error → simulated response; error results counted as completed;
Web UI success from exit code; failures persisted as a placeholder the Explorer ranks),
and that it reports cost through **three** independent paths, the user-visible one being
the constant `0.08`.

The plan required to fix that spans roughly twenty changes across five files plus a test
suite. That is a different project from the one authorised, and re-scoping is the
operator's decision, not the reviewer's and not Claude's. Continuing to Rounds 3–5 would
refine a plan whose premise has not been agreed.

Both verdicts stand as `VERDICT: REVISE`. Nothing was implemented. The session ends at
human gate #2 with the scope question open.

**Residual risk — files no round opened:** `openrouter_model_collections.py`,
`openrouter_rankings_service.py`, `openrouter_categorization.py`, `isee-ui.html`,
`reporting.py`, `query_export.py`, `analysis.py`, `organize_runs.py`,
`undo_organization.py`, `launch_cognitive_explorer.py`. Round 2 identified
`OpenRouterRankingsService`'s persisted rankings cache and `/api/models-fresh` as further
sources of stale model selection; that was not verified by Claude and remains an open
claim.
