| Metadata | Value |
|---|---|
| created | 2026-04-23 12:21:50 BST |
| last_updated | 2026-04-23 12:21:50 BST |
| owner | QA/Validation Agent |
| source_agent | Orchestrator Agent |

# General Validation

## Purpose

Define the repo-level validation checks to run after cross-agent merges, shared dependency updates, and before pushing `main`.

These checks complement the agent-specific validation handoffs:

- `docs/validation/backend-validation.md`
- `docs/validation/modelling-validation.md`
- `docs/validation/ai-validation.md`

## Standard Merge Validation

Run from the repo root.

### Git State

```bash
git status --short
```

Expected:

- No uncommitted tracked changes before merging or pushing, unless they are the intended validation/doc changes.
- Ignored runtime files such as `.venv/`, `.env`, `allocadabra.egg-info/`, and `__pycache__/` may exist locally but must not be committed.

### Conflict Marker Scan

```bash
rg -n '(<{7}|={7}|>{7})' . || true
```

Expected:

- No output.

### Python Compile Check

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app
```

Expected:

- Command exits with status `0`.
- Confirms all Python files under `/app` parse with the local system Python.

### Dependency Lock Check

```bash
uv lock --check
```

Expected:

- Command exits with status `0`.
- Confirms `uv.lock` is consistent with `pyproject.toml`.

### Processing Runtime Import Check

```bash
uv run python -c "from app.processing.dataset import build_canonical_price_dataframe; from app.processing.runner import generate_modelling_outputs; import pandas, riskfolio, cvxpy; print('processing imports ok')"
```

Expected:

- Prints `processing imports ok`.
- Must be run through `uv` because modelling dependencies are project dependencies, not guaranteed in system Python.

### Perplexity SDK Import Check

```bash
uv run python -c "import perplexity; from perplexity import Perplexity; print('perplexity sdk import ok')"
```

Expected:

- Prints `perplexity sdk import ok`.
- Confirms the SDK import path used by `app.ai.provider` is available.
- Does not require `PERPLEXITY_API_KEY` because it does not make a live API request.

### AI Smoke Checks

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.parsing import split_visible_text_and_metadata; text='## Objective\nTest\n<!-- allocadabra_metadata: {\"selected_model_ids\":[\"mean_variance\"]} -->'; visible, metadata = split_visible_text_and_metadata(text); assert metadata['selected_model_ids'] == ['mean_variance']; assert 'allocadabra_metadata' not in visible; from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nMean Variance\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['mean_variance']}); assert result.valid; print('ai smoke ok')"
```

Expected:

- Prints `ai smoke ok`.

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "import app.ai; from app.ai.data_api import get_fixed_financial_advice_refusal, get_generic_safe_error; assert get_fixed_financial_advice_refusal(); assert get_generic_safe_error(); print('ai exports ok')"
```

Expected:

- Prints `ai exports ok`.

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.context_selection import select_review_detailed_context as s; ctx={'models': {'mean_variance': {'allocations':[1], 'drawdown':[2]}, 'risk_parity': {'allocations':[3]}}}; out=s(user_message='Why do Mean Variance weights differ?', visible_context=None, available_detailed_context=ctx); assert out == {'models': {'mean_variance': {'allocations': [1]}}}; print('review context smoke ok')"
```

Expected:

- Prints `review context smoke ok`.

### Storage Export Import Check

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "import app.storage as s; assert callable(s.prepare_review_export_bundle); assert callable(s.get_review_download_all); print('storage export imports ok')"
```

Expected:

- Prints `storage export imports ok`.

## Live Checks

These are not part of the default repo-level validation because they require credentials or external services:

- Live CoinGecko API checks require `COINGECKO_API_KEY`.
- Live Perplexity provider checks require `PERPLEXITY_API_KEY`.

Run live checks only when the relevant key is configured and the owning agent has requested them.

## Known Gaps

- No formal test framework exists yet.
- No Streamlit/frontend integration checks exist yet.
- No end-to-end workflow test exists yet.
- No live API validation is included in the default merge checklist.

## QA Follow-Up

When the QA/Validation Agent is active, convert these smoke commands into repeatable tests or scripts and decide which checks should run locally, in CI, and before releases.
