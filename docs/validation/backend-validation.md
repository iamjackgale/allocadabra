| Metadata | Value |
|---|---|
| created | 2026-04-23 07:34:14 BST |
| last_updated | 2026-04-23 07:34:14 BST |
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

The checks do not validate live CoinGecko connectivity, Streamlit integration, modelling integration, export bundle generation, or full workflow acceptance criteria.

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
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -c "import app.storage as s; assert callable(s.list_token_options); assert callable(s.return_to_configure_from_review); print('package exports ok')"
```

Purpose:

- Confirms public storage package exports include frontend-facing token functions and review-to-configuration lifecycle helpers.

Expected result:

- Prints `package exports ok`.

## Known Validation Gaps

- No live CoinGecko API request was run because that requires a real `COINGECKO_API_KEY` in `.env`.
- No automated test suite or fixture-based unit tests exist yet.
- No Streamlit/frontend integration checks exist yet.
- No modelling-agent integration checks exist yet for consuming cached price history.
- Export bundle creation, artifact packaging, unavailable-artifact handling, and download bundle manifests are intentionally deferred until the dedicated export/download spec is complete.

## Suggested QA Follow-Ups

- Convert the smoke commands into repeatable tests once the project test framework is chosen.
- Add fixture tests for token-list normalization, duplicate token IDs, malformed rows, price forward-fill, malformed price points, and empty price responses.
- Add filesystem tests for JSON schema fields, CSV columns, cache merge behaviour, ignored runtime cache files, and reset behaviour that preserves CoinGecko cache.
- Add session lifecycle tests for generated plan, confirmed plan, reconfigure, modelling started, interrupted modelling, review-ready reload, return to configure, reset configuration, and start new model.
- Add live API checks behind an opt-in environment flag so CI/local validation can skip them when `COINGECKO_API_KEY` is unavailable.
