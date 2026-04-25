| Metadata | Value |
|---|---|
| created | 2026-04-24 07:15:35 BST |
| last_updated | 2026-04-25 BST (tasks 117, 118 — smoke scripts added) |
| owner | QA/Validation Agent |
| source_agent | Frontend Agent |

# Frontend Validation Handoff

## Purpose

Record the lightweight validation checks prepared and run during the first Frontend Agent implementation pass so the QA/Validation Agent can review, extend, and formalize them later.

## Scope Validated

The checks cover initial frontend work for:

- Streamlit app entrypoint under `/frontend/app.py`.
- Single-base-url phase routing for Configuration, Modelling, and Review.
- Reusable Configuration and Review chat component wiring.
- Configuration parameter controls, generated-plan actions, and reset/reconfigure flows.
- Modelling progress screen, progress event rendering, retry, interrupted state, and Review Results gate.
- Review output sections, frontend-controlled one-open-section behavior, manifest-driven downloads, and Review chat context exposure.
- Frontend package importability and basic Streamlit runtime startup.

The checks do not validate live CoinGecko token loading, live Perplexity responses, full model execution with real market data, browser interaction coverage, or full end-to-end workflow acceptance criteria.

## Latest Validation Run

Frontend Agent Brief 3 validation:

- `git pull origin main`: already up to date.
- Credential availability check: repo-root `.env` absent; `COINGECKO_API_KEY` unavailable in shell; `PERPLEXITY_API_KEY` unavailable in shell.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app`: passed.
- `rg -n '(<{7}|={7}|>{7})' .`: no conflict markers.
- `uv lock --check`: passed.
- `uv run streamlit run frontend/app.py --server.headless true --server.port 8501`: started at `http://localhost:8501`.
- Configuration missing-key path: opened `http://localhost:8501/?alloca_dev_no_ai_env=1`, sent a Configuration chat message, and observed the user message rendered, `Perplexity is not configured...`, `Retry last message`, no traceback, and Configuration state still visible.
- Configuration repeated-failure path: clicked `Retry last message` until three consecutive failures and observed `Repeated failures stopped automatic retries...`, disabled chat input, disabled retry button, and no traceback.
- Review fixture/context path: opened `http://localhost:8501/?alloca_dev_review_fixture=brief3&alloca_dev_no_ai_env=1` and observed Review open with `Ranked for: Stable performance · Medium risk appetite`, Allocation weights active, Risk Parity selected, and no exposed `visible_context`, `detailed_context`, `chart_table_headers`, `visible_table_data`, or `open_expander_ids` strings.
- Review missing-key chat path: sent `What does the allocation look like for Risk Parity?` in Review chat and observed the user message rendered, retry available, recoverable missing-key copy, no traceback, and no exposed context payload names.
- Task `119` full live end-to-end Streamlit validation was not run because both required API keys are unavailable.
- Destructive reset checks such as confirming `Start New Model` were not executed in this pass because they clear local workflow/output state and require explicit action-time approval.

Synthetic Review fixture implementation validation:

- `git pull origin main`: already up to date.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app`: passed.
- `rg -n '(<{7}|={7}|>{7})' .`: no conflict markers.
- `uv lock --check`: passed.
- `uv run streamlit run frontend/app.py --server.headless true --server.port 8501`: started at `http://localhost:8501`.
- Open `http://localhost:8501/?alloca_dev_review_fixture=1` to materialize the fixed synthetic Review fixture and enter Review Mode without CoinGecko ingestion or modelling. This path runs the normal Review opening call when AI credentials are available.
- For frontend-only verification without a live Perplexity call, open `http://localhost:8501/?alloca_dev_review_fixture=frontend-check&alloca_dev_no_ai_env=1`.
- Observed fixture result: Review pane opened with `REVIEW`, `Ranked for: Stable performance · Medium risk appetite`, Summary/Allocation controls, Risk Parity selected, and synthetic model outputs available for Mean Variance and Risk Parity.
- For Review Mode AI tests `RM-1`, `RM-2`, and `RM-3`, keep the app on `?alloca_dev_review_fixture=1`, use the Review chat, and select or keep the allocation weights context when asking the Risk Parity allocation question.
- Open `http://localhost:8501/?alloca_dev_no_ai_env=1` in a separate app process or clean browser session to suppress AI `.env` loading for that process. Send any Configuration Mode chat message and confirm the UI shows a recoverable missing-key error with retry available, without a Python traceback and without clearing active inputs.
- Observed missing-key result: Configuration Mode showed `Perplexity is not configured...`, displayed `Retry last message`, and preserved active inputs.
- The missing-key hook removes `PERPLEXITY_API_KEY` only from the current Streamlit process environment and monkeypatches dotenv loading in memory. It does not edit or delete `.env` and does not print secrets.

Task `120` revalidation after pulling latest `main`:

- `git pull origin main`: already up to date.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend`: passed.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app`: passed.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app`: passed.
- `rg -n '(<{7}|={7}|>{7})' .`: no conflict markers.
- `uv lock --check`: passed.
- `uv run python -c "import streamlit; print(streamlit.__version__)"`: `1.56.0`.
- `uv run streamlit run frontend/app.py --server.headless true --server.port 8501`: started at `http://localhost:8501`; forced stop produced a Streamlit shutdown traceback after startup.

## Verification Commands

### Git State

Command:

```bash
git status --short
```

Purpose:

- Confirms which frontend implementation files and docs are currently modified or untracked.
- Gives QA and the Orchestrator a quick view of branch scope before merge review.

Expected result:

- Intended frontend files under `/frontend/**` appear.
- Intended frontend-owned docs appear.
- No unrelated app-layer, dependency, or storage cache files should appear.

### Conflict Marker Scan

Command:

```bash
rg -n '(<{7}|={7}|>{7})' .
```

Purpose:

- Confirms no unresolved merge-conflict markers remain in the branch.

Expected result:

- No output.
- Command exits with status `1` because `rg` found no matches.

Observed result during Frontend pass:

- Passed with no output.

### Frontend Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend
```

Purpose:

- Confirms every Python file under `/frontend` parses and compiles with the local system Python.
- Uses `/tmp/allocadabra-pycache-main` to avoid writing bytecode to user cache locations that may be blocked in the local sandbox.

Expected result:

- Command exits with status `0`.

Observed result during Frontend pass:

- Passed.

### Full App Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app
```

Purpose:

- Confirms the new frontend code and existing app-layer imports parse together.
- Catches syntax/import mistakes in the UI and the app-layer contracts it references.

Expected result:

- Command exits with status `0`.

Observed result during Frontend pass:

- Passed.

### Required App Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app
```

Purpose:

- Satisfies the Frontend Agent brief requirement.
- Confirms the frontend work did not require or introduce changes under `/app`.

Expected result:

- Command exits with status `0`.

Observed result during Frontend pass:

- Passed.

### Dependency Lock Check

Command:

```bash
uv lock --check
```

Purpose:

- Confirms `uv.lock` is consistent with `pyproject.toml` after `streamlit` was added by the shared dependency owner.
- Confirms the Frontend Agent did not introduce an unapproved dependency change.

Expected result:

- Command exits with status `0`.

Observed result during Frontend pass:

- Passed.
- In the local sandbox this required escalation because `uv` needed to read its cache under `~/.cache/uv`.

### Streamlit Import Check

Command:

```bash
uv run python -c "import streamlit; print(streamlit.__version__)"
```

Purpose:

- Confirms the shared project environment can import the Streamlit runtime.
- Records the installed Streamlit version used for the frontend pass.

Expected result:

- Prints the installed Streamlit version.

Observed result during Frontend pass:

```text
1.56.0
```

Notes:

- In the local sandbox this required escalation because `uv` needed to read its cache under `~/.cache/uv`.

### Streamlit Entrypoint Smoke Test

Command:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Purpose:

- Confirms the new frontend entrypoint starts under Streamlit.
- Confirms Streamlit can resolve the frontend package and app-layer imports at runtime.

Expected result:

- Streamlit starts and prints a local URL.
- Stop the process after startup is confirmed.

Observed result during Frontend pass:

```text
Local URL: http://localhost:8501
```

Notes:

- In the local sandbox this required escalation because `uv` needed to read its cache under `~/.cache/uv`.
- The process was stopped after the startup smoke test completed.

## Manual UI Checks For QA

Run:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Then verify:

- Configuration opens on desktop with chat on the left and the `CONFIGURATION` workflow pane on the right.
- Mobile-width viewport shows the holding screen stating that the app has not yet been optimized for mobile.
- Green accent/backlighting appears in Configuration and Review.
- Red accent/backlighting appears during Modelling.
- Asset search calls the token-list interface and searches only user-facing symbol/name results.
- Asset chips show dominant cashtag symbol, smaller name, and remove controls.
- Asset count communicates the 2 minimum and 10 maximum.
- Objective and risk appetite each allow exactly one selected option.
- Supported model controls show only Mean Variance, Risk Parity, and Hierarchical Risk Parity.
- At least one model remains selected.
- Optional constraints emit the V1 constraint object shape expected by Backend/Data task `092`.
- `Generate Plan` runs deterministic validation before AI plan generation.
- Validation failures surface in the Configuration chat feedback area.
- Generated plan replaces the editable form and exposes exactly `Run`, `Regenerate`, and `Reconfigure`.
- `Reconfigure`, `Reset Configuration`, Modelling `Cancel`, `Return To Configure`, and `Start New Model` all show the required confirmation copy.
- Modelling shows checkpoints for Validation, Ingestion, Datasets, Modelling, Analysis, and Outputs.
- Modelling shows one current micro-log line and approximate elapsed time.
- Confirmed modelling plan is collapsed below the Modelling progress area.
- If Review artifacts are ready, the page shows `Review Results` before opening Review.
- Review opens with chat on the left and the `REVIEW` workflow pane on the right.
- Review shows the comparison cue and `Ranked for: [objective] · [risk appetite]`.
- Review defaults to Summary metrics and uses explicit one-open-section frontend state.
- Per-model sections use the selected-model dropdown, while comparative sections disable it.
- `Download All` and per-section downloads follow manifest availability.
- Missing artifacts disable download controls with `This artifact was not generated for this run.`
- Review chat receives visible context without showing injected context details to the user.

## Repeatable Smoke Script (Task 117)

Script: `scripts/frontend_smoke.py`

Run: `uv run python scripts/frontend_smoke.py`

Expected final line: `frontend smoke ok`

### What it covers

- **Step 1 — compile check.** Runs `compileall` over both `frontend/` and `app/` via
  subprocess with `PYTHONPYCACHEPREFIX` set.
- **Step 2 — import check.** Runs `sys.executable -c "import frontend.app, frontend.chat,
  frontend.review, frontend.configuration, frontend.data, frontend.runtime,
  frontend.modelling, frontend.theme, frontend.constants, frontend.dev_tools"` as a
  subprocess to confirm all key frontend modules import without errors or `st` contamination.
- **Step 3 — constants integrity.** Imports `frontend.constants` directly (no `st` calls at
  module level) and asserts `METRIC_SPECS` is non-empty, `MODEL_LABELS` contains at minimum
  `mean_variance`, `risk_parity`, and `hierarchical_risk_parity`, `REVIEW_SECTIONS` is
  non-empty, and `PER_MODEL_REVIEW_SECTIONS` is non-empty.
- **Step 4 — manual check summary.** Prints exact URLs for dev-flag paths that require
  Streamlit running and cannot be automated without browser tooling.

Note: `frontend` is not included in the project editable install (`pyproject.toml` includes
only `app*`). The script adds the project root to `sys.path` before importing
`frontend.constants` directly.

### What remains manual

All checks requiring a running Streamlit instance:

```
http://localhost:8501/?alloca_dev_no_ai_env=1           — missing-key Configuration error
http://localhost:8501/?alloca_dev_review_fixture=brief3 — synthetic Review fixture
http://localhost:8501/?alloca_dev_review_fixture=brief3&alloca_dev_no_ai_env=1 — fixture + missing-key
```

### Validation run (2026-04-25)

- `uv run python scripts/frontend_smoke.py`: printed `frontend smoke ok`. Exit code `0`.
- Compile check passed for `frontend/` and `app/`.
- Import check passed for all ten frontend modules.
- Constants integrity passed: `METRIC_SPECS` has 14 keys, `MODEL_LABELS` has 3 keys,
  `REVIEW_SECTIONS` has 10 entries, `PER_MODEL_REVIEW_SECTIONS` has 7 entries.

---

## Fixture-Backed Review Rendering (Task 118)

Script: `scripts/review_fixture_smoke.py`

Run: `uv run python scripts/review_fixture_smoke.py`

Expected final line: `review fixture smoke ok`

### What it covers

- **Step 1 — synthetic artifact files.** Writes three synthetic CSVs to
  `/tmp/allocadabra-synthetic-review-fixture/`: `summary-metrics.csv` (2 model rows, all 14
  V1 metric columns), `mean-variance-allocation-weights.csv`, and
  `risk-parity-allocation-weights.csv` (2 asset rows each).
- **Step 2 — export bundle.** Sets up workflow state (reset → update inputs → store plan →
  confirm plan) and calls `prepare_review_export_bundle(...)` with the three synthetic
  artifact descriptors, matching the structure used by `frontend/dev_tools.py`.
- **Step 3 — manifest validation.** Calls `get_review_export_manifest()` and asserts: non-empty
  dict, `artifacts` list present, all three synthetic IDs present, both model IDs in at least
  one artifact, all available artifact paths exist on disk, `summary_metrics` has
  `category="general"`, both allocation weights have `category="model"` and
  `output_type="allocation_weights"`.
- **Step 4 — summary metrics CSV.** Reads from manifest path and asserts: 2 rows, `model_id`
  column contains `mean_variance` and `risk_parity`, all 14 V1 metric columns present, no
  literal `nan` / `null` strings in any cell.
- **Step 5 — allocation weights CSVs.** For each, asserts: `asset` and `weight` columns
  present, 2 rows, weights numeric and in `[0, 1]`, weights sum within `0.001` of `1.0`.
- **Step 6 — cleanup.** Calls `reset_configuration()` to clear model outputs state and removes
  the synthetic temp directory.

### Remaining gap

Visual rendering of the fixture on the Review page requires Streamlit running. Use
`http://localhost:8501/?alloca_dev_review_fixture=brief3` to confirm the fixture opens the
Review pane correctly in a live session.

### Validation run (2026-04-25)

- `uv run python scripts/review_fixture_smoke.py`: printed `review fixture smoke ok`. Exit code `0`.
- Manifest structure, artifact paths, CSV content, and allocation weight shapes all passed.

---

## Known Validation Gaps

- No Playwright or browser automation exists yet for Streamlit UI flows.
- No live CoinGecko token-list or price-history validation was run because it requires `COINGECKO_API_KEY`.
- No live Perplexity chat or plan-generation validation was run because it requires `PERPLEXITY_API_KEY`.
- No full real-data end-to-end modelling run was validated through the UI.
- Backend/Data task `092` is still required for stronger deterministic issue-code coverage around unsupported model IDs and impossible constraint combinations.
- The current modelling contract has no cooperative cancellation signal, so frontend `Cancel` abandons the workflow/UI and ignores in-flight results but cannot stop the underlying modelling thread mid-run.
- Review metrics currently display `NaN`/unavailable values according to the current modelling artifact output; Modelling task `069` still owns stronger unavailable-reason output.

## Suggested QA Follow-Ups

- Add a repeatable frontend smoke script once the project test framework is chosen.
- Add browser-level checks for phase routing, mobile holding screen, confirmation dialogs, one-open-section Review behavior, and download disabled states.
- Add fixture-backed Review tests using a generated manifest and small CSV artifacts.
- Add a fixture or stub mode for token-list loading so Configuration UI can be validated without live CoinGecko credentials.
- Add a fixture or stub mode for AI calls so chat rendering and plan flow can be validated without live Perplexity credentials.
- Add an end-to-end local smoke once Backend/Data task `092`, Modelling task `069`, and cooperative cancellation follow-up work have landed.
