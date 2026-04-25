| Metadata | Value |
|---|---|
| created | 2026-04-25 BST |
| last_updated | 2026-04-25 BST |
| owner | QA/Validation Agent |
| source_agent | QA/Validation Agent |

# Validation Gap Report 1

## Purpose

Structured gap analysis for Orchestrator review following QA/Validation Agent Brief 1
(tasks `117`, `118`, `129`). Each proposed task includes an owner agent assignment,
rationale, and blocking dependencies.

---

## Agent Gap Summaries

### Backend/Data Agent

**Covered by existing scripts:** `scripts/backend_smoke.py` and
`scripts/backend_modelling_handoff_smoke.py` cover deterministic storage, normalisation,
configuration validation, export bundle creation, manifest shape, and the modelling-to-export
handoff. Both pass in the current codebase.

**Remaining gaps:**

- **Live CoinGecko freshness.** Task `064` (live price-cache freshness validation) has never
  run because `COINGECKO_API_KEY` is not present in the `qa01` worktree `.env`. Once the key
  is placed in `qa01`, this check can be unblocked. The current deterministic handoff smoke
  verifies the 2-day freshness boundary without a live call.
- **No formal test framework.** All existing backend coverage is a lightweight smoke script.
  No fixture-backed unit tests exist for token-list normalisation edge cases, duplicate tokens,
  malformed price points, or cache merge behaviour.
- **Export edge cases.** The smoke uses a single dummy CSV. There is no test for all required
  artifact types, model-specific `models/{model_id}/` path layout under multi-model runs,
  disabled `Download All` state when zip creation fails, or exhaustive missing-placeholder
  handling.
- **Session lifecycle edge cases.** Reconfigure, interrupted modelling, review-to-configure
  return, and start-new-model transitions are exercised in the backend smoke but not with
  fixture-backed coverage for every state combination.
- **Asset-constraint cross-check.** `validate_configuration_inputs` now covers
  `constraint_asset_id_not_selected` but there is no repeatable test for the full range of
  asset-count and percentage constraint combinations beyond the backend smoke.

---

### Modelling Agent

**Covered by existing script:** `scripts/modelling_smoke.py` covers dataset failure for too
few assets and insufficient history, unsupported model selection, partial failure shape,
missing artifact shape, metric consistency, unavailable metric reasons, and cooperative
cancellation. Passes in the current codebase.

**Remaining gaps:**

- **No live price data integration.** All modelling checks use synthetic local data. There
  is no test that exercises the full path from live CoinGecko price cache through dataset
  building to model outputs.
- **PNG chart generation.** `png_count 16` was observed in the Modelling Agent's synthetic
  run, but chart PNGs have never been validated for aesthetic correctness. The smoke only
  checks file existence.
- **Visual efficient frontier.** No check that `efficient-frontier.csv` contains the
  expected columns (`frontier_point`, `annualized_return`, `annualized_volatility`) across all
  solver outcomes, including cases where the frontier cannot be produced.
- **Missing placeholder exhaustiveness.** Optional artifact missing-state placeholders were
  observed in the smoke but are not tested for every possible computation failure code.
- **Solver fallback.** ECOS and CVXOPT are not installed. The smoke does not verify that all
  three models fall back gracefully when the first solver in Riskfolio's preference list is
  unavailable.
- **No formal test framework.** Coverage is a lightweight smoke script. Metric accuracy
  (volatility, Sharpe, Sortino, Omega, CVaR, CDaR) is not checked beyond the deterministic
  edge case in `_check_metric_consistency`.

---

### AI/Perplexity Agent

**Covered by existing commands and new script:** `scripts/ai_smoke_extended.py` (task `129`)
now covers missing-key handling, Configuration readiness intercept, financial advice
guardrail, unsupported-model intercept, metadata shape (plan and review), and context
selection. All prior subprocess-based smoke commands from `ai-validation.md` remain valid.

**Remaining gaps:**

- **Live Perplexity provider.** No live provider call has run in the `qa01` worktree because
  `PERPLEXITY_API_KEY` is not in the local `.env`. The optional live provider check pattern
  is documented in `ai-validation.md` but has not been run here.
- **Synthetic Review chat with real AI.** RM-1, RM-2, RM-3 from the live UI pass were
  validated in the `8fe0` worktree but not re-verified here. Re-running them requires
  `PERPLEXITY_API_KEY` and a running Streamlit instance.
- **Plan generation end-to-end.** `generate_modelling_plan(...)` is tested at the UI level
  but has no repeatable offline test. The provider call path, metadata extraction, and
  `store_generated_plan` handoff are not covered without a live key or a fake provider.
- **Fake provider contract.** There is no injectable fake provider that exercises the full
  `send_configuration_chat` / `send_review_chat` / `generate_modelling_plan` flow with
  controllable response shapes. This blocks testing of metadata rejection, `invalid_metadata`
  code, and long-transcript behaviour without live credentials.
- **Metadata fixture tests.** Fenced `allocadabra-metadata`, HTML-comment metadata, invalid
  JSON, missing metadata, and malformed Markdown heading edge cases are noted in the suggested
  follow-ups but have no script coverage.
- **Plan-import path.** `import_modelling_plan(...)` is not exercised in any repeatable
  script.

---

### Frontend Agent

**Covered by new scripts:** `scripts/frontend_smoke.py` (task `117`) covers compile, import,
and constants integrity checks. `scripts/review_fixture_smoke.py` (task `118`) covers the
full export bundle path for the synthetic Review fixture, manifest structure, and CSV content.

**Remaining gaps:**

- **No browser automation.** All UI-level checks from the Frontend Agent's validation pass —
  phase routing, mobile holding screen, confirmation dialogs, one-open-section Review
  behaviour, download disabled states, and chat rendering — remain manual. There is no
  Playwright or equivalent setup.
- **Live CoinGecko token list.** Configuration asset search calls the token-list interface.
  No repeatable test covers live CoinGecko token loading because `COINGECKO_API_KEY` is
  absent from the `qa01` worktree.
- **Full real-data end-to-end.** Task `119` (full live Streamlit validation with both keys)
  has not been run in the `qa01` worktree. This requires copying `.env` from another worktree.
  Keys are confirmed available.
- **Cooperative cancellation in the UI.** The frontend `Cancel` button abandons the workflow
  but cannot stop the underlying modelling thread mid-run. No browser test verifies the exact
  UI state after cancellation (no crash, no orphaned spinner, correct copy).
- **Review metrics NaN display.** The current modelling artifact output can produce `NaN`
  unavailable values. The Review page renders these per the `GENERIC_MISSING_ARTIFACT_MESSAGE`
  pattern, but no repeatable test confirms the display behaviour for missing metric cells
  (Modelling task `069` still owns stronger unavailable-reason output).
- **`_render_run_result` retry for non-retryable errors.** The Orchestrator noted a V1 gap:
  `_render_run_result` always shows Retry even for validation/config errors where retry is
  not meaningful. QA should verify the cancel path returns to Configuration correctly. This
  is manual until browser automation exists.

---

### QA/Validation Agent (Self)

**Completed in this brief:**

- Task `117`: `scripts/frontend_smoke.py` — compile, import, constants.
- Task `118`: `scripts/review_fixture_smoke.py` — fixture bundle, manifest, CSV validation.
- Task `129`: `scripts/ai_smoke_extended.py` — missing key, intercepts, guardrails, metadata,
  context selection.

**Gaps not covered by this brief:**

- **Task `119` (full live end-to-end).** Blocked on `.env` placement in `qa01` worktree.
  Both keys are confirmed available — copy from another worktree to unblock.
- **No project test framework.** All QA coverage is Python scripts. There is no `pytest`
  setup, no fixtures directory, and no CI integration. All three new scripts are standalone
  and self-cleaning; converting them to a test framework is a future task.
- **No browser automation.** Playwright or similar has not been approved by the Orchestrator.
  UI-level checks remain manual.
- **Missing live-provider script.** Task `129` covers only deterministic intercepts. A live
  AI smoke (with `PERPLEXITY_API_KEY`) covering provider response shape, metadata extraction
  from a real response, and financial-advice detection on live output is not yet written.
- **Dataset-building validation spec coverage.** The brief lists coverage requirements from
  `docs/specs/data-backend/dataset-building.md`: asset count limits, minimum 90 price
  observations, empty transformed datasets, and excessive missing data. These are covered in
  `scripts/modelling_smoke.py` (owned by Modelling Agent) but QA has not written independent
  acceptance-criteria checks.

---

## Proposed New Tasks

| Proposed ID | Owner | Description | Depends On |
|---|---|---|---|
| `NEW-QA-001` | QA/Validation Agent | Run task `119` full live Streamlit validation in `qa01` once `.env` is placed (both keys available). | `.env` placement in `qa01` worktree |
| `NEW-QA-002` | QA/Validation Agent | Write a fake AI provider and use it to test `send_configuration_chat`, `send_review_chat`, and `generate_modelling_plan` with controllable response shapes — covering metadata rejection, `invalid_metadata` code, and long-transcript behaviour without live credentials. | None |
| `NEW-QA-003` | QA/Validation Agent | Set up `pytest` (or equivalent) framework and convert the three new smoke scripts into formal fixture-backed tests. | Orchestrator approval of test framework choice |
| `NEW-FRONTEND-001` | Frontend Agent | Investigate or document the `_render_run_result` always-shows-Retry V1 gap identified by the Orchestrator. Confirm the cancel path returns to Configuration correctly and document expected UX for non-retryable errors. Return mini spec to QA for acceptance criteria if a code change is needed. | None |
| `NEW-BACKEND-001` | Backend/Data Agent | Add live CoinGecko freshness validation behind an opt-in `COINGECKO_API_KEY` flag so it can run in the `qa01` worktree once the key is present. | `COINGECKO_API_KEY` in `qa01` `.env` |
| `NEW-MODELLING-001` | Modelling Agent | Add fixture-backed tests for solver fallback behaviour when CLARABEL and OSQP are both unavailable, and for efficient frontier column shape validation across all three model paths. | None |
| `NEW-AI-001` | AI/Perplexity Agent | Write a repeatable live-provider smoke script (gated on `PERPLEXITY_API_KEY`) covering response shape, metadata extraction, and financial-advice detection on live output. | `PERPLEXITY_API_KEY` in `qa01` `.env` |
| `NEW-AI-002` | AI/Perplexity Agent | Add repeatable offline tests for `import_modelling_plan(...)`: pasted plan with valid metadata, invalid JSON metadata, missing required headings, future-only model names, and text/metadata conflicts. | None |
