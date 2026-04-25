| Metadata | Value |
|---|---|
| created | 2026-04-23 07:34:14 BST |
| last_updated | 2026-04-25 BST |
| owner | QA/Validation Agent |
| source_agent | Backend/Data Agent |

# Backend Validation Handoff

## Purpose

Record the lightweight validation checks prepared and run during the initial Backend/Data scaffolding work so the QA/Validation Agent can review, extend, and formalize them later.

## Scope Validated

The checks cover initial scaffolding for:

- Python package importability under `/app`.
- CoinGecko token and market-chart normalization.
- Local JSON workflow/session state creation and deterministic validation.
- Public package exports from `app.storage`.
- Export manifest creation, missing placeholder handling, individual download metadata, zip bundle creation, and export exclusion checks.

The checks do not validate live CoinGecko connectivity, Streamlit integration, full modelling integration, or full workflow acceptance criteria.

## Verification Passed

The Backend/Data Agent has run and passed these checks:

- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -m compileall app`
- Export bundle smoke test with a dummy Modelling-produced CSV.
- Package export smoke test.

For task `063`, the Backend/Data Agent also completed these documentation-only validation steps:

- Pulled latest `main` successfully.
- Ran `git status --short --branch`.
- Ran conflict-marker scan with `rg -n '(<{7}|={7}|>{7})' .`; no conflict markers were found.
- Did not run a compile check because task `063` changed documentation only and no production code changed.

For task `092`, the Backend/Data Agent also completed deterministic configuration validation checks for:

- Unsupported model IDs.
- Duplicate model IDs.
- Impossible allocation sums.
- Contradictory min/max percentage constraints.
- Impossible min/max asset-count constraints.
- Selected-asset constraints that reference assets outside the current selection.

For task `082`, the Backend/Data Agent added and passed a repeatable deterministic smoke script:

- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/backend_smoke.py`
- The default smoke path uses local fixture data only and does not require `COINGECKO_API_KEY`.
- The script restores the prior `storage/cache` tree after it runs.

Task `082` validation commands run:

- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/storage app/ingestion scripts/backend_smoke.py`: passed.
- `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/backend_smoke.py`: printed `backend smoke ok`.
- `uv lock --check`: passed after sandbox escalation so `uv` could read its local cache.
- `rg -n '(<{7}|={7}|>{7})' .`: no conflict markers were found.

For task `103`, the Backend/Data Agent added and passed a repeatable Modelling-to-export handoff smoke:

- `uv run python scripts/backend_modelling_handoff_smoke.py`
- The smoke calls `app.processing.run_active_modelling(...)` with fresh local cached price CSVs, then passes returned `artifacts`, `failed_models`, and `missing_artifacts` directly to `prepare_review_export_bundle(...)`.
- The smoke verifies root export artifacts, model-specific `models/{model_id}/` artifacts, missing placeholders, failed-model reasons, frontend-safe download metadata, raw CoinGecko/cache exclusion, and Review readiness after export preparation.
- No Backend/Data adapter gap was found for the current `run_active_modelling(...)` handoff.

For task `064`, `COINGECKO_API_KEY` was not available in the shell environment and no repo-root `.env` was present, so live CoinGecko freshness validation was not run. The deterministic handoff smoke verifies the current freshness boundary: latest cached date exactly 2 days behind UTC today is usable, while 3 days behind is stale.

## Verification Commands

### Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -m compileall app
```

Purpose:

- Confirms every Python file under `/app` parses and compiles.
- Uses `/tmp/allocadabra-pycache` because macOS system Python attempted to write bytecode under `~/Library/Caches`, which is blocked in the local sandbox.

Expected result:

- Command exits with status `0`.

### Storage/Session Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -c "from app.storage.data_api import get_active_workflow, validate_active_configuration; state = get_active_workflow(); result = validate_active_configuration(); assert state['phase'] == 'configuration'; assert result['valid'] is False; print('storage smoke ok')"
```

Purpose:

- Confirms `get_active_workflow()` creates or loads the single active workflow state.
- Confirms the default phase is `configuration`.
- Confirms deterministic validation rejects an empty/default configuration.

Expected result:

- Prints `storage smoke ok`.
- Runtime file `storage/cache/user-inputs/active_workflow.json` may be created and is intentionally ignored by `storage/cache/.gitignore`.

### Normalizer Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -c "from app.ingestion.coingecko import normalize_token_list, normalize_market_chart; assert normalize_token_list([{'id':'bitcoin','symbol':'btc','name':'Bitcoin'}, {'id':'','symbol':'x','name':'Bad'}])[0].id == 'bitcoin'; assert normalize_market_chart('bitcoin', {'prices': [[0, 1.0], [172800000, 3.0]]})[1].price == 1.0; print('normalizer smoke ok')"
```

Purpose:

- Confirms token normalization omits rows missing required `id`, `symbol`, or `name`.
- Confirms market-chart normalization converts timestamps to UTC dates and forward-fills missing daily prices after the first valid price.

Expected result:

- Prints `normalizer smoke ok`.

### Package Export Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -c "import app.storage as s; assert callable(s.prepare_review_export_bundle); assert callable(s.get_review_download_all); print('package exports ok')"
```

Purpose:

- Confirms public storage package exports include frontend-facing export bundle and Download All helpers.

Expected result:

- Prints `package exports ok`.

### Configuration Validation Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 - <<'PY'
from dataclasses import asdict
from app.storage.validation import validate_configuration_inputs

assets = [
    {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'},
    {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'},
    {'id': 'solana', 'symbol': 'sol', 'name': 'Solana'},
]
base = {
    'selected_assets': assets,
    'treasury_objective': 'Best risk-adjusted returns',
    'risk_appetite': 'Medium',
    'selected_models': ['mean_variance'],
}

def codes(inputs):
    return [asdict(issue) for issue in validate_configuration_inputs(inputs).issues]

unsupported = codes({**base, 'selected_models': ['mean_variance', 'future_model']})
assert any(issue['code'] == 'unsupported_model_id' and issue['context']['model_id'] == 'future_model' for issue in unsupported)

duplicate = codes({**base, 'selected_models': ['mean_variance', 'mean_variance']})
assert any(issue['code'] == 'duplicate_model_ids' and issue['field'] == 'selected_models' for issue in duplicate)

unknown_key = codes({**base, 'constraints': {'unsupported_constraint': 1}})
assert any(issue['code'] == 'unknown_constraint_key' and issue['field'] == 'constraints' for issue in unknown_key)

bad_percent = codes({**base, 'constraints': {'global_min_allocation_percent': 101}})
assert any(issue['code'] == 'constraint_percent_invalid' and issue['field'] == 'constraints.global_min_allocation_percent' for issue in bad_percent)

impossible_min = codes({**base, 'selected_assets': assets * 2, 'constraints': {'global_min_allocation_percent': 20}})
assert any(issue['code'] == 'global_min_allocation_sum_exceeds_100' and issue['field'] == 'constraints.global_min_allocation_percent' for issue in impossible_min)

impossible_max = codes({**base, 'constraints': {'global_max_allocation_percent': 30}})
assert any(issue['code'] == 'global_max_allocation_sum_below_100' and issue['field'] == 'constraints.global_max_allocation_percent' for issue in impossible_max)

contradictory = codes({**base, 'constraints': {'global_min_allocation_percent': 60, 'global_max_allocation_percent': 50}})
assert any(issue['code'] == 'constraint_min_greater_than_max' for issue in contradictory)

asset_count = codes({**base, 'constraints': {'min_assets_in_portfolio': 4, 'max_assets_in_portfolio': 2}})
assert any(issue['code'] == 'min_assets_constraint_exceeds_selected_assets' for issue in asset_count)
assert any(issue['code'] == 'min_assets_constraint_greater_than_max_assets_constraint' for issue in asset_count)

frontend_defaults = codes({**base, 'constraints': {'global_min_allocation_percent': 0, 'global_max_allocation_percent': 100, 'min_assets_in_portfolio': 0, 'max_assets_in_portfolio': 3}})
assert not frontend_defaults, frontend_defaults

loose_max = codes({**base, 'selected_assets': assets[:2], 'constraints': {'max_assets_in_portfolio': 3}})
assert not any(issue['field'] == 'constraints.max_assets_in_portfolio' for issue in loose_max)

unknown_asset = codes({**base, 'constraints': {'selected_asset_min_allocation': {'asset_ids': ['dogecoin'], 'percent': 10}}})
assert any(issue['code'] == 'constraint_asset_id_not_selected' and issue['context']['asset_id'] == 'dogecoin' for issue in unknown_asset)

print('configuration validation smoke ok')
PY
```

Purpose:

- Confirms `validate_configuration_inputs()` returns stable machine-readable issues for unsupported model IDs, duplicate model IDs, unknown constraint keys, invalid percentage values, impossible allocation sums, contradictory min/max constraints, impossible asset-count constraints, and selected-asset constraints referencing unknown assets.
- Confirms frontend default constraint values of global min `0`, global max `100`, min asset count `0`, and max asset count equal to selected asset count do not create blocking validation issues.
- Confirms a loose maximum asset-count value above the current selected count does not block validation by itself.
- Confirms each issue includes the stable `field`, `code`, `message`, and optional `context` shape used by `validate_active_configuration()`.

Expected result:

- Prints `configuration validation smoke ok`.

### Backend/Data Repeatable Smoke Script

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/backend_smoke.py
```

Purpose:

- Confirms CoinGecko token cache/list read path from local cached JSON without a live API call.
- Confirms CoinGecko price cache read/status path from local CSV fixture data without a live API call.
- Confirms active workflow/session lifecycle for default state, input updates, generated-plan storage, plan confirmation, Review readiness through export preparation, and start-new-model reset.
- Confirms deterministic validation issue shape and task `092` issue codes.
- Confirms export bundle creation from fixture Modelling-produced artifacts, including manifest creation, failed/missing artifact handling, `Download All` metadata, individual artifact metadata, placeholder files, and exclusion of raw CoinGecko cache/chat transcript paths.
- Confirms the V1 CoinGecko client retry/timeout policy shape without making a network call.
- Restores the previous `storage/cache` tree after execution so local active workflow/cache data is not left modified by the smoke.

Expected result:

- Prints `backend smoke ok`.
- Command exits with status `0`.
- Requires no API keys and no live external services.

### Backend/Modelling Export Handoff Smoke Script

Command:

```bash
uv run python scripts/backend_modelling_handoff_smoke.py
```

Purpose:

- Confirms real Modelling-produced artifact descriptors from `app.processing.run_active_modelling(...)` can be passed to `prepare_review_export_bundle(...)` without field-name translation.
- Confirms required root artifacts are exported when modelling succeeds: `user-inputs.json`, `modelling-plan.md`, `canonical-modelling-dataset.csv`, `summary-metrics.csv`, and `manifest.json`.
- Confirms successful model artifacts land under `models/{model_id}/` in `Download All`.
- Confirms failed model reasons and missing optional artifact placeholders are represented in the export manifest and zip bundle.
- Confirms `get_review_export_manifest()`, `get_review_download_all()`, and `get_review_artifact_download(...)` return frontend-safe shapes.
- Confirms active workflow phase is not marked `review` until Backend/Data export preparation completes.
- Confirms raw CoinGecko cache paths and chat transcript paths are excluded from `Download All`.
- Confirms the current 2-day price-cache freshness boundary without making a live CoinGecko request.

Expected result:

- Prints `backend modelling handoff smoke ok`.
- Command exits with status `0`.
- Requires the project `uv` environment for modelling dependencies.
- Requires no API keys and no live external services.

### Export Bundle Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 - <<'PY'
from pathlib import Path
import zipfile

from app.storage.session_state import reset_configuration, store_generated_plan, confirm_generated_plan
from app.storage.data_api import update_active_inputs, prepare_review_export_bundle, get_review_download_all, get_review_artifact_download

reset_configuration()
update_active_inputs({
    'selected_assets': [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}, {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'}],
    'treasury_objective': 'Best risk-adjusted returns',
    'risk_appetite': 'Medium',
    'selected_models': ['mean_variance'],
})
store_generated_plan(markdown='# Plan\n\nRun one model.')
confirm_generated_plan()
source = Path('/tmp/allocadabra-summary-metrics.csv')
source.write_text('metric,mean_variance\nreturn,0.1\n', encoding='utf-8')
result = prepare_review_export_bundle(
    modelling_artifacts=[{
        'artifact_id': 'summary_metrics',
        'label': 'Summary metrics',
        'category': 'general',
        'output_type': 'summary_metrics',
        'format': 'csv',
        'source_path': str(source),
        'bundle_path': 'summary-metrics.csv',
    }],
    missing_artifacts=[{
        'artifact_id': 'efficient_frontier_png',
        'label': 'Efficient frontier chart',
        'output_type': 'efficient_frontier',
        'model_id': 'mean_variance',
        'reason': 'This artifact was not generated for this run.',
    }],
)
assert result['workflow_state']['phase'] == 'review'
assert result['exports']['download_all_enabled'] is True
manifest = result['exports']['manifest']
assert manifest['bundle_filename'].startswith('allocadabra-results-')
assert any(a['artifact_id'] == 'summary_metrics' and a['path'] == 'summary-metrics.csv' for a in manifest['artifacts'])
missing = next(a for a in manifest['artifacts'] if a['artifact_id'] == 'efficient_frontier_png')
assert missing['status'] == 'missing'
assert missing['individual_download_enabled'] is False
assert get_review_artifact_download('summary_metrics')['ok'] is True
assert get_review_artifact_download('efficient_frontier_png')['enabled'] is False
bundle = get_review_download_all()
assert bundle['ok'] is True
with zipfile.ZipFile(bundle['path']) as archive:
    names = set(archive.namelist())
assert 'manifest.json' in names
assert 'user-inputs.json' in names
assert 'modelling-plan.md' in names
assert 'summary-metrics.csv' in names
assert 'missing/efficient_frontier_png.txt' in names
assert not any(name.startswith('coingecko/') for name in names)
assert not any('chat' in name for name in names)
print('export smoke ok')
PY
```

Purpose:

- Confirms export bundle creation consumes a Modelling-produced artifact file instead of generating modelling output itself.
- Confirms Modelling-produced artifact descriptors can use either `source_path` plus `bundle_path`, or a relative `path` under `storage/cache/model-outputs/` for already-generated artifacts.
- Confirms bundle filename prefix, manifest entries, missing placeholder `.txt` handling, and Review phase transition.
- Confirms available artifacts are individually downloadable and missing artifacts disable individual download controls.
- Confirms `Download All` zip includes `manifest.json`, user inputs, modelling plan, copied model output artifacts, and missing placeholders.
- Confirms raw CoinGecko cache paths and chat transcript artifacts are not included in the zip.

Expected result:

- Prints `export smoke ok`.
- Runtime export files under `storage/cache/model-outputs/` are intentionally ignored by `storage/cache/.gitignore`.

### Extended Backend Smoke Script (tasks 135, 136)

For tasks `135` and `136`, `scripts/backend_smoke.py` was extended with five deterministic export/session steps (136) and one opt-in live CoinGecko step (135).

Commands run (task 136 — deterministic steps):

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/storage app/ingestion
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/backend_smoke.py
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

All passed. Script output:

```
step 5 — multi-model layout ok
step 6 — missing placeholder types ok
step 7 — download all exclusions ok
step 8 — reconfigure from review-ready ok
step 9 — re-run after reset ok
live coingecko smoke ok
  latest=2026-04-25, count=365, days_behind=0
backend smoke ok
```

New deterministic steps cover:

- **Step 5 (multi-model layout):** Export bundle with artifacts for `mean_variance` and `risk_parity`. Asserts model artifacts land under `models/{model_id}/` and root artifacts (`summary-metrics.csv`, `manifest.json`) are not nested under a model path.
- **Step 6 (missing placeholder types):** All three optional artifact types (`allocation_weights`, `efficient_frontier`, `chart_png`) absent from modelling output. Asserts each manifest entry has `status=missing`, `individual_download_enabled=False`, and placeholder text matches `MISSING_ARTIFACT_DEFAULT_REASON` imported from `app.storage.export_bundle`.
- **Step 7 (download all exclusions):** Multi-model bundle. Asserts `get_review_download_all()` zip excludes `coingecko/` paths and chat transcripts, and includes all available model-specific artifacts.
- **Step 8 (reconfigure from review-ready):** After `prepare_review_export_bundle`, calls `reset_configuration()`. Asserts phase is no longer `review` and `get_review_export_manifest()` returns `None`.
- **Step 9 (re-run after reset):** Full lifecycle run A → reset → run B with fresh data. Asserts run B manifest contains `run_b_summary` but not `run_a_summary`, confirming independence.

### Live CoinGecko Smoke (tasks 135, 064)

Task `135` adds an opt-in live step gated on `COINGECKO_API_KEY` presence. When the key is absent the script prints `COINGECKO_API_KEY not set — skipping live coingecko smoke` and exits `0`.

Live run result (2026-04-25, worktree `c0c4`):

- `COINGECKO_API_KEY` present in repo-root `.env` (length 27, Demo plan key).
- `client.fetch_market_chart("bitcoin")` returned **365 price points**.
- Latest `PricePoint.date`: **2026-04-25** (today's UTC date).
- `days_behind=0` — latest point is current-day data.

### Task 064 — Freshness Tolerance Conclusion

**Status: DONE — no change required.**

Live evidence (2026-04-25): CoinGecko returned 365 daily points for bitcoin with the latest date equal to today's UTC date (`days_behind=0`). The API publishes prior-UTC-day data approximately 10 minutes after midnight UTC; in edge cases the latest available point may therefore be 1 day behind. The current 2-day tolerance correctly covers this edge case with one day of margin. Tightening to 1 day would leave no margin for the 10-minute publication window or any transient delay. **The 2-day tolerance is confirmed correct for V1.**

## Known Validation Gaps

- No automated test suite or fixture-based unit tests exist yet.
- No Streamlit/frontend integration checks exist yet.
- No full modelling-agent integration checks exist yet for consuming cached price history or handing off the complete output artifact set.
- `scripts/backend_smoke.py` is a smoke script, not a formal test suite; QA should decide whether to convert it to the selected project test pattern.

## Suggested QA Follow-Ups

- Convert the smoke commands into repeatable tests once the project test framework is chosen.
- Add fixture tests for token-list normalization, duplicate token IDs, malformed rows, price forward-fill, malformed price points, and empty price responses.
- Add filesystem tests for JSON schema fields, CSV columns, cache merge behaviour, ignored runtime cache files, and reset behaviour that preserves CoinGecko cache.
- Add session lifecycle tests for generated plan, confirmed plan, reconfigure, modelling started, interrupted modelling, review-ready reload, return to configure, reset configuration, and start new model.
- Add export tests for every required artifact type, failed artifact status, disabled bundle state when zip creation fails, model-specific `models/{model_id}/` paths, and exclusion of raw CoinGecko cache/user chat data.
- Add live API checks behind an opt-in environment flag so CI/local validation can skip them when `COINGECKO_API_KEY` is unavailable.
