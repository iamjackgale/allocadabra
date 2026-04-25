| Metadata | Value |
|---|---|
| created | 2026-04-25 BST |
| last_updated | 2026-04-25 BST |
| prompt_used | 2026-04-25 BST |

# QA/Validation Agent Brief 1

You are the QA/Validation Agent for Allocadabra.

Before starting:

1. Fill in the `prompt_used` timestamp above as the first edit.
2. Pull latest `main` into your branch at `/Users/iamjackgale/.codex/worktrees/qa01/allocadabra`.
3. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/prompts/agents/qa-validation-agent.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md` (especially the Orchestrator Integration Review section at the bottom)
   - `/docs/validation/general-validation.md`
   - `/docs/validation/backend-validation.md`
   - `/docs/validation/modelling-validation.md`
   - `/docs/validation/ai-validation.md`
   - `/docs/validation/frontend-validation.md`
4. Run the standard validation checks from `docs/validation/general-validation.md` before making any changes, to confirm the current baseline passes.
5. Do not edit production code in `/app/**` or `/frontend/**`. If you find a gap that requires a production fix, return a mini spec (see Boundaries below).

## Tasks In This Brief

| Task | Description |
|---|---|
| `117` | Convert the existing frontend manual checks into a repeatable smoke script. |
| `118` | Write a fixture-backed Review rendering validation script. |
| `129` | Formalise AI fixture and missing-key checks into a repeatable script. |
| Review | Read all `/docs/validation/` docs, identify gaps, and produce a structured gap report for the Orchestrator. |

Complete tasks `117`, `118`, and `129` first, then write the gap report. The gap report is the final deliverable of this brief.

---

## Task 117 — Repeatable Frontend Smoke Script

**File to create:** `scripts/frontend_smoke.py`

**Goal:** produce a single script the Orchestrator or any agent can run without Streamlit active to confirm the frontend package is importable and consistent.

### What to include

**Step 1 — compile check.** Run a `compileall` check covering both `frontend/` and `app/` from within the script using `subprocess` or `compileall` module. Fail loudly if any file fails.

**Step 2 — import check.** Without starting a Streamlit session, verify that the key frontend modules import without errors. Because most of `frontend/` imports `streamlit` at the top level, the import check must be run as a subprocess to avoid contaminating the runner. Example pattern:

```bash
uv run python -c "import frontend.app, frontend.chat, frontend.review, frontend.configuration, frontend.data, frontend.runtime, frontend.modelling, frontend.theme, frontend.constants, frontend.dev_tools; print('frontend imports ok')"
```

Capture and assert a `0` exit code and the expected print string.

**Step 3 — constants integrity check.** Import `frontend.constants` directly (it has no `st` calls at module level) and assert:

- `METRIC_SPECS` is a non-empty list.
- `MODEL_LABELS` contains at minimum `mean_variance`, `risk_parity`, and `hierarchical_risk_parity` as keys.
- `REVIEW_SECTIONS` is a non-empty list.
- `PER_MODEL_REVIEW_SECTIONS` is a non-empty list.

**Step 4 — dev-flag path documentation.** At the bottom of the script, print a clear summary of the manual check paths that cannot be automated without browser tooling, with exact URLs:

```
MANUAL CHECKS REQUIRED (need Streamlit running):
  http://localhost:8501/?alloca_dev_no_ai_env=1           — missing-key Configuration error
  http://localhost:8501/?alloca_dev_review_fixture=brief3 — synthetic Review fixture
  http://localhost:8501/?alloca_dev_review_fixture=brief3&alloca_dev_no_ai_env=1 — fixture + missing-key
```

### Acceptance criteria

- `uv run python scripts/frontend_smoke.py` exits with status `0`.
- Final line prints `frontend smoke ok`.
- Any import or compile failure prints a clear error and exits non-zero.

### Update `docs/validation/frontend-validation.md`

Add a new "Repeatable Smoke Script" section documenting the script, how to run it, and what it covers vs. what remains manual.

---

## Task 118 — Fixture-Backed Review Rendering Validation

**File to create:** `scripts/review_fixture_smoke.py`

**Goal:** confirm that the synthetic Review fixture can be materialised through the real export bundle path, and that the resulting manifest and artifact files are structurally correct — all without running Streamlit.

### What to include

The `frontend/dev_tools.py` fixture uses `streamlit` at the top level and can't be imported directly. Re-implement the fixture setup inline in the script using the same underlying callables (`prepare_review_export_bundle`, `get_review_export_manifest`).

**Step 1 — write synthetic artifact files.** Write the same three synthetic CSVs that `dev_tools.py` uses to a temp directory. This is pure file I/O — no Streamlit required:

```python
# summary-metrics.csv: two model rows (mean_variance, risk_parity), all V1 metric columns
# mean-variance-allocation-weights.csv: asset, weight for BTC/ETH
# risk-parity-allocation-weights.csv: asset, weight for BTC/ETH
```

**Step 2 — call `prepare_review_export_bundle(...)`.** Pass the three synthetic artifact descriptors (matching the `dev_tools.py` structure) to `prepare_review_export_bundle` from `app.storage`. This exercises the full export manifest path.

**Step 3 — read and validate the manifest.** Call `get_review_export_manifest()` and assert:

- Manifest is a non-empty dict.
- Manifest contains `artifacts` key with a list of entries.
- Exactly three artifact entries are present with IDs `synthetic_summary_metrics`, `synthetic_mean_variance_allocation_weights`, and `synthetic_risk_parity_allocation_weights`.
- Both model IDs (`mean_variance` and `risk_parity`) appear in at least one artifact entry each.
- All artifact `path` values point to files that exist on disk.
- `summary_metrics` entry has `output_type == "summary_metrics"` and `category == "general"`.
- Both `allocation_weights` entries have `output_type == "allocation_weights"` and `category == "model"`.

**Step 4 — validate summary metrics CSV content.** Read the `summary-metrics.csv` from the path in the manifest and assert:

- File is readable as a CSV with pandas.
- Two rows present (one per model).
- `model_id` column contains `mean_variance` and `risk_parity`.
- No literal `nan` or `NaN` strings in any cell (numeric unavailability should be blank).
- All V1 metric columns present: `total_return_pct`, `max_drawdown_pct`, `sharpe_ratio`, `calmar_ratio`, `omega_ratio`, `sortino_ratio`, `annualized_return_pct`, `annualized_volatility_pct`, `30d_volatility_pct`, `avg_drawdown_pct`, `skewness`, `kurtosis`, `cvar_pct`, `cdar_pct`.

**Step 5 — validate allocation weights CSVs.** For each allocation weights artifact, read the CSV and assert:

- `asset` and `weight` columns present.
- Two rows (Bitcoin and Ethereum).
- `weight` values are numeric, each between 0 and 1.
- Weights sum to approximately 1.0 (within 0.001 tolerance).

**Step 6 — cleanup.** After assertions, reset the storage state so the script does not leave a synthetic manifest in the real storage path. Use `reset_configuration()` from `app.storage.session_state` to clear model outputs state, and remove the synthetic temp directory.

### Acceptance criteria

- `uv run python scripts/review_fixture_smoke.py` exits with status `0`.
- Final line prints `review fixture smoke ok`.
- Manifest structure, artifact paths, CSV content, and allocation weight shapes all pass.

### Update `docs/validation/frontend-validation.md`

Add a new "Fixture-Backed Review Rendering" section documenting the script, what it validates, and the remaining gap (visual rendering requires Streamlit).

---

## Task 129 — Repeatable AI Fixture and Missing-Key Checks

**File to create:** `scripts/ai_smoke_extended.py`

**Goal:** convert the existing deterministic AI validation paths from `docs/validation/ai-validation.md` into a single repeatable script covering missing-key handling, guardrail intercepts, and metadata shape — all without a live Perplexity connection.

### What to include

**Step 1 — missing-key handling.** Test what happens at the `app.ai.data_api` layer when `PERPLEXITY_API_KEY` is absent:

```python
import os
os.environ.pop("PERPLEXITY_API_KEY", None)
# Suppress dotenv loader to ensure key stays absent
```

Then call `send_configuration_chat(...)` (with a minimal configured workflow state set up via `reset_configuration()`, `update_active_inputs(...)`, and no confirmed plan) and assert:

- Return value has `ok == False`.
- Return value has a non-empty `message` string.
- No Python exception propagates uncaught.
- `message` does not contain raw Python traceback text.

**Step 2 — Configuration readiness intercept.** Without a live key, call `send_configuration_chat(...)` using the deterministic intercept that fires before any provider call:

```python
reset_configuration()
update_active_inputs({
    "selected_assets": [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}],
    "selected_models": ["mean_variance", "risk_parity"],
    # treasury_objective and risk_appetite intentionally absent
})
result = send_configuration_chat("What do I still need to fill in?")
```

Assert:

- `result["ok"] is True` (deterministic intercept, no provider call).
- `result["metadata"]["kind"] == "configuration_suggestion"`.
- `result["metadata"]["missing_required_fields"]` contains `treasury_objective` and `risk_appetite`.
- `result["message"]` is a non-empty string.

**Step 3 — financial advice guardrail intercept.** Set up a minimal review-ready state, then test:

```python
mark_review_ready({"manifest_path": "storage/cache/model-outputs/manifest.json"})
result = send_review_chat("Should I buy Bitcoin based on these results?")
assert result["ok"] is True
assert result["message"] == get_fixed_financial_advice_refusal()
```

**Step 4 — unsupported-model intercept.** Test that a direct request for a model outside the supported set is deflected:

```python
result = send_configuration_chat("Run Black-Litterman for me.")
assert result["ok"] is True
assert "black" not in result["message"].lower() or "not supported" in result["message"].lower() or result["message"] == get_generic_safe_error()
# Accept either a deflection or safe-error, but not an instruction to use an unsupported model
```

The exact assertion depends on the implemented intercept. Check `app/ai/data_api.py` to understand what the unsupported-model intercept returns, and assert accordingly.

**Step 5 — metadata shape validation.** Run the existing metadata smoke commands from `ai-validation.md` as in-process assertions rather than subprocess calls:

- `validate_modelling_plan(md, {"selected_model_ids": ["mean_variance"]}).valid is True`
- `validate_modelling_plan(md, {"selected_model_ids": ["black_litterman"]}).valid is False`
- `validate_modelling_plan(md, {"selected_model_ids": ["worst_case"]}).valid is False`
- `validate_review_metadata({"referenced_model_ids": ["mean_variance"]}).valid is True`
- `validate_review_metadata({"referenced_model_ids": ["hierarchical_equal_risk"]}).valid is False`
- `looks_like_financial_advice("I recommend buying Bitcoin.")` is True.
- `looks_like_financial_advice("I recommend buying Bitcoin.") == False` for a neutral string.

**Step 6 — context-selection smoke.** Run the Review detailed-context narrowing assertions from `ai-validation.md` as in-process assertions.

**Step 7 — cleanup.** Call `reset_configuration()` after the guardrail tests to leave storage in a clean state.

### Notes

- Steps 1, 2, 3, and 4 depend on `app.storage` state. Use `reset_configuration()` between steps that modify workflow state to keep them independent.
- Do not attempt any live Perplexity provider call. If any step would require a live key to get past a guard check, skip that step with a clear `# BLOCKED: requires PERPLEXITY_API_KEY` comment and a printed note.

### Acceptance criteria

- `uv run python scripts/ai_smoke_extended.py` exits with status `0`.
- Final line prints `ai smoke extended ok`.
- Deterministic intercept, guardrail, and metadata shape checks all pass.
- Missing-key handling returns a clean `ok=False` result without an uncaught exception.

### Update `docs/validation/ai-validation.md`

Add a new "Repeatable Extended Smoke Script" section documenting the script, what it covers, and the remaining live-key-dependent gaps.

---

## Validation Gap Review — All Agents

After completing `117`, `118`, and `129`, do the following:

### Read every validation doc

For each of these files, read the full "Suggested QA Follow-Ups" and "Known Validation Gaps" sections:

- `docs/validation/backend-validation.md`
- `docs/validation/modelling-validation.md`
- `docs/validation/ai-validation.md`
- `docs/validation/frontend-validation.md`
- `docs/validation/general-validation.md`

Also cross-check against the integration spec review notes in `docs/specs/app/frontend-backend-modelling-integration.md`.

### Write a validation gap report

Create a new file: `docs/validation/validation-gap-report-1.md`

Structure it as follows:

```markdown
| Metadata | Value |
|---|---|
| created | <timestamp> |
| last_updated | <timestamp> |
| owner | QA/Validation Agent |
| source_agent | QA/Validation Agent |

# Validation Gap Report 1

## Purpose

Structured gap analysis for Orchestrator review. Each proposed task includes
an owner agent assignment, rationale, and blocking dependencies.

## Agent Gap Summaries

### Backend/Data Agent

[Summary of remaining gaps from backend-validation.md + any new gaps found.]

### Modelling Agent

[Summary of remaining gaps from modelling-validation.md + any new gaps found.]

### AI/Perplexity Agent

[Summary of remaining gaps from ai-validation.md + any new gaps found.]

### Frontend Agent

[Summary of remaining gaps from frontend-validation.md + any new gaps found.]

### QA/Validation Agent (Self)

[Summary of gaps that QA owns directly, including what this brief did not cover.]

## Proposed New Tasks

| Proposed ID | Owner | Description | Depends On |
|---|---|---|---|
| ... | ... | ... | ... |

Use placeholder IDs like `NEW-QA-001`, `NEW-MODELLING-001`, etc. The Orchestrator
will assign final task IDs from docs/tasks.md.
```

**Important:** Do not edit `docs/tasks.md` directly. The gap report is a proposal for the Orchestrator to review and incorporate.

---

## Boundaries

Own:

- `/docs/validation/**`
- `/scripts/frontend_smoke.py` (new)
- `/scripts/review_fixture_smoke.py` (new)
- `/scripts/ai_smoke_extended.py` (new)

Do not edit:

- `/app/**` — owned by Backend/Data, Modelling, and AI agents.
- `/frontend/**` — owned by the Frontend Agent.
- `/docs/tasks.md` — owned by the Orchestrator; submit proposed tasks in the gap report instead.
- `pyproject.toml` / `uv.lock` — shared dependencies; do not add or remove without a mini spec.

**If a validation check reveals a production code gap**, do not fix it directly. Return a mini spec with:

- Target file(s) and owning agent.
- Reproduction path (exact script or URL).
- Observed behaviour.
- Expected behaviour.
- Risk or dependency notes.

Include mini specs in the gap report or as a separate section of your closing report.

---

## Standard Validation

Run these before starting work and again after completing each script:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app frontend scripts
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

---

## Reporting Back

When complete, report:

- tasks completed (`117`, `118`, `129`);
- files created or modified;
- validation commands and outcomes for each script;
- any mini specs needed for other owner agents;
- location of the gap report and a brief summary of the highest-priority proposed tasks.
