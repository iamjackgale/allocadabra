| Metadata | Value |
|---|---|
| created | 2026-04-23 12:01:48 BST |
| last_updated | 2026-04-23 19:36:15 BST |
| owner | QA/Validation Agent |
| source_agent | Modelling Agent |

# Modelling Validation Handoff

## Purpose

Record the lightweight validation checks prepared and run during the initial Modelling Agent work so the QA/Validation Agent can review, extend, and formalize them later.

## Scope Validated

The checks cover initial modelling work for:

- Local Python runtime feasibility for `riskfolio-lib`, `cvxpy`, and default solver availability.
- The three initial supported model paths:
  - Mean Variance.
  - Risk Parity.
  - Hierarchical Risk Parity.
- Dataset-to-output artifact generation under `/app/processing`.
- Export-spec-aligned CSV, PNG, failed-model, and artifact metadata generation.

The checks do not validate live CoinGecko ingestion, Streamlit integration, final zip bundle creation, frontend download controls, or the complete end-to-end user workflow.

## Solver Stock Feasibility

### Environment Sync

Command:

```bash
uv sync
```

Purpose:

- Creates the project environment from the approved root `pyproject.toml`.
- Confirms Python `3.11` can be selected for the first modelling runtime spike.
- Installs `riskfolio-lib`, `cvxpy`, and approved modelling dependencies without adding extra solver packages directly.

Observed result:

- Used CPython `3.11.14`.
- Installed `riskfolio-lib==7.2.1`.
- Installed `cvxpy==1.8.2`.
- Installed default solver packages including `clarabel`, `osqp`, `scs`, and `highspy`.
- Command exited with status `0`.

### Import And Solver Discovery

Command:

```bash
uv run python -c 'import cvxpy as cp, riskfolio as rp, pandas as pd, numpy as np; print("python", __import__("sys").version.split()[0]); print("riskfolio", getattr(rp, "__version__", "unknown")); print("cvxpy", cp.__version__); print("solvers", sorted(cp.installed_solvers()))'
```

Purpose:

- Confirms the project runtime can import modelling dependencies.
- Records available default `cvxpy` solvers.

Observed result:

```text
python 3.11.14
riskfolio 7.2.1
cvxpy 1.8.2
solvers ['CLARABEL', 'HIGHS', 'OSQP', 'SCIPY', 'SCS']
```

### Riskfolio Default Solver Configuration

Command:

```bash
uv run python -c 'import riskfolio as rp, pandas as pd, numpy as np; Y=pd.DataFrame(np.random.default_rng(1).normal(0,0.01,(100,3)), columns=["A","B","C"]); p=rp.Portfolio(returns=Y); print(getattr(p, "solvers", None)); print(getattr(p, "sol_params", None))'
```

Purpose:

- Confirms Riskfolio's default solver preference list and solver parameter state.

Observed result:

```text
['CLARABEL', 'ECOS', 'SCS', 'OSQP', 'CVXOPT']
{}
```

Notes:

- `ECOS` and `CVXOPT` were not installed by the approved dependency set.
- The installed default stack still includes `CLARABEL`, `SCS`, and `OSQP`, which are enough for the initial model paths tested below.

### Initial Model Path Feasibility

Command:

```bash
uv run python -c '<synthetic daily returns script running direct cvxpy, Mean Variance, Risk Parity, and HRP>'
```

Purpose:

- Runs a deterministic synthetic 365-day returns dataset through:
  - a direct default `cvxpy` quadratic program.
  - Mean Variance via `Portfolio.optimization(...)`.
  - Risk Parity via `Portfolio.rp_optimization(...)`.
  - HRP via `HCPortfolio.optimization(...)`.
- Confirms each model returns finite, non-negative weights summing to `1.0`.

Observed result:

```text
python 3.11.14
riskfolio 7.2.1
cvxpy 1.8.2
installed_solvers CLARABEL,HIGHS,OSQP,SCIPY,SCS
cvxpy_default status=optimal solver=OSQP objective=0.2000000000 elapsed=0.019s
mean_variance ok sum=1.00000000
risk_parity ok sum=1.00000000
hrp ok sum=1.00000000
```

Conclusion:

- The approved dependency set is sufficient for the first supported model paths.
- No additional solver dependency mini spec is needed at this stage.

## Export Bundling Verification

### Mainline Integration Validation

Validation run:

- `git pull origin main`: passed.
- conflict marker scan: passed, no output.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app`: passed.
- `uv lock --check`: passed.
- processing runtime import check: passed.
- storage export import check: passed.
- active modelling smoke test: passed.
- unsupported model smoke test: passed.

Purpose:

- Confirms the branch rebased or merged cleanly from `main`.
- Confirms no unresolved conflict markers remained in the worktree.
- Confirms the full `/app` package compiled after modelling changes landed.
- Confirms the committed `uv.lock` remained in sync with `pyproject.toml`.
- Confirms processing-layer imports and storage/export-facing imports still resolve after modelling work.
- Confirms the active modelling interface and unsupported-model validation paths still pass after mainline integration.

### Compile Check

Command:

```bash
uv run python -m compileall app/processing
```

Purpose:

- Confirms the processing package parses and compiles in the project Python environment.

Expected result:

- Command exits with status `0`.

Observed result:

- Passed.

### Full App Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app
```

Purpose:

- Confirms every Python file under `/app` parses and compiles after the modelling work and subsequent mainline integration.
- Uses `/tmp/allocadabra-pycache-main` to avoid writing bytecode to a user cache location during validation.

Observed result:

- Passed.

### Lockfile Check

Command:

```bash
uv lock --check
```

Purpose:

- Confirms `uv.lock` is consistent with the approved dependency state in `pyproject.toml`.

Observed result:

- Passed.

### Processing Runtime Import Check

Command:

```bash
./.venv/bin/python -c 'import app.processing as p; assert callable(p.run_active_modelling); assert callable(p.modelling_contract); print("processing runtime import check: passed")'
```

Observed result:

- Passed.

Purpose:

- Confirms the processing runtime imports still resolve correctly after the modelling package additions and mainline integration.

### Storage Export Import Check

Command:

```bash
./.venv/bin/python -c 'from app.storage.data_api import prepare_review_export_bundle, get_review_export_manifest, get_review_artifact_download, get_review_download_all; assert callable(prepare_review_export_bundle); assert callable(get_review_export_manifest); assert callable(get_review_artifact_download); assert callable(get_review_download_all); print("storage export import check: passed")'
```

Observed result:

- Passed.

Purpose:

- Confirms storage-layer import paths used for export and review handoff still resolve correctly after the modelling changes.

### Full Synthetic Artifact Smoke Test

Command:

```bash
uv run python -c '<synthetic selected assets and price histories script calling generate_modelling_outputs(...) for all three supported models>'
```

Purpose:

- Builds canonical price data from deterministic synthetic CoinGecko-shaped price histories.
- Runs `mean_variance`, `risk_parity`, and `hierarchical_risk_parity`.
- Writes model-owned artifacts to `/tmp/allocadabra-processing-smoke`.
- Confirms CSV and PNG artifact generation aligns with `docs/specs/app/export-bundling.md`.

Observed result:

```text
ok True
successful ['mean_variance', 'risk_parity', 'hierarchical_risk_parity']
failed []
artifact_count 37
png_count 16
missing_count 0
```

Additional observed file checks:

- `canonical-modelling-dataset.csv` existed and was non-empty.
- `summary-metrics.csv` existed and was non-empty.
- `models/mean_variance/allocation-weights.csv` existed and was non-empty.
- `models/risk_parity/risk-contribution.csv` existed and was non-empty.
- `models/hierarchical_risk_parity/dendrogram.csv` existed and was non-empty.
- `models/mean_variance/efficient-frontier.csv` included `frontier_point`, `annualized_return`, `annualized_volatility`, and asset weight columns.

Expected result:

- Command exits with status `0`.
- All three supported model IDs appear in `successful_models`.
- No failed model reasons are produced.
- Chart PNGs are paired with underlying CSV data.

### Partial-Success Failure Artifact Smoke Test

Command:

```bash
uv run python -c '<synthetic selected assets and price histories script calling generate_modelling_outputs(...) with one supported model and one unsupported model ID>'
```

Purpose:

- Confirms a partial-success modelling run still returns usable artifacts for successful models.
- Confirms failed model reasons are written to `failed-models.json`.

Observed result:

```text
ok True
successful ['mean_variance']
failed_count 1
failed_file True
```

Expected result:

- Command exits with status `0`.
- Successful model artifacts remain available.
- `failed-models.json` is written with structured failed-model details.

## Active Modelling Interface Verification

### Frontend-Callable Contract

Callable:

```python
from app.processing import run_active_modelling, modelling_contract
```

Contract purpose:

- Read active workflow inputs from Backend/Data APIs.
- Validate the active configuration.
- Load cached/fetched price histories through Backend/Data APIs.
- Run Modelling-owned dataset building, model execution, metrics, and artifact generation.
- Return frontend-safe output descriptors without creating zip bundles or storing the final export manifest.

Return shape:

```text
ok: bool
successful_models: list[str]
failed_models: list[dict]
artifacts: list[dict]
missing_artifacts: list[dict]
errors: list[dict]
user_message: str
progress_events: list[dict]
dataset_metadata: dict
output_dir: str | null
```

Progress phases:

```text
validation
ingestion
datasets
modelling
analysis
outputs
```

Backend/Data handoff:

- Pass `artifacts` as `modelling_artifacts`.
- Pass `failed_models` as `failed_models`.
- Pass `missing_artifacts` as `missing_artifacts`.
- Backend/Data remains owner of `prepare_review_export_bundle(...)`, final manifest storage, and zip creation.

### Active Workflow Smoke Test

Command:

```bash
uv run python -c '<monkeypatched active workflow and cached price history script calling run_active_modelling(...)>'
```

Purpose:

- Confirms `run_active_modelling(...)` can consume active workflow-shaped inputs.
- Confirms price-history loading is delegated through the imported Backend/Data API boundary.
- Confirms the frontend-safe return shape includes successful models, artifacts, missing artifacts, errors, user message, and progress events.
- Confirms all six progress checkpoint phases are emitted.
- Avoids mutating real workflow/session files by monkeypatching the imported Backend/Data functions in the smoke script.

Observed result:

```text
active modelling smoke ok 24 0 12
phases ['validation', 'validation', 'ingestion', 'ingestion', 'datasets', 'datasets', 'modelling', 'modelling', 'analysis', 'analysis', 'outputs', 'outputs']
contract fields ['ok', 'successful_models', 'failed_models', 'artifacts', 'missing_artifacts', 'errors', 'user_message']
```

Expected result:

- Command exits with status `0`.
- `ok` is `True`.
- `successful_models` contains the requested supported model IDs.
- `errors` is empty.
- `artifacts` excludes Backend-owned `failed_models` materialization.
- Progress events include `validation`, `ingestion`, `datasets`, `modelling`, `analysis`, and `outputs`.

### Unsupported Model Smoke Test

Command:

```bash
uv run python -c '<monkeypatched active workflow script calling run_active_modelling(...) with an unsupported selected model ID>'
```

Purpose:

- Confirms unsupported model IDs return a frontend-safe validation error.
- Confirms unsupported IDs are not silently dropped in a way that would default to all supported models.

Observed result:

```text
unsupported model smoke ok
```

Expected result:

- Command exits with status `0`.
- `ok` is `False`.
- First error code is `unsupported_models`.
- `successful_models` is empty.

## Known Validation Gaps

- No live CoinGecko price cache integration was run.
- No Streamlit/frontend integration was run.
- No Backend/Data zip bundle creation was run because Backend/Data owns final package construction.
- Active workflow integration was smoke-tested through monkeypatching rather than real local session state.
- No automated fixture-based test suite exists yet.
- No visual review of generated PNG chart aesthetics was performed beyond file creation.
- Optional artifact missing-state placeholders were implemented but not exhaustively tested against every possible computation failure.

## Suggested QA Follow-Ups

- Convert the synthetic model and artifact smoke checks into repeatable tests once the project test framework is chosen.
- Add fixture tests for duplicate CoinGecko symbols, insufficient price history, missing price cache entries, empty returns, and more than 10 selected assets.
- Add fixture tests for more than 3 selected models and unsupported model IDs.
- Add metric consistency tests for total return, drawdown, volatility, Sharpe, Sortino, Omega, CVaR, and CDaR.
- Add artifact contract tests for required filenames, model IDs, manifest-ready fields, missing optional artifact `.txt` placeholders, and no raw CoinGecko cache leakage.
- Add PNG-generation tests that can gracefully skip or expect missing placeholders if the local renderer is unavailable.
