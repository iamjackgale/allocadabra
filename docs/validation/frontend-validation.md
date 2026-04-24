| Metadata | Value |
|---|---|
| created | 2026-04-24 07:15:35 BST |
| last_updated | 2026-04-24 13:15:53 BST |
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
