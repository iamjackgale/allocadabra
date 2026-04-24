| Metadata | Value |
|---|---|
| created | 2026-04-23 12:02:46 BST |
| last_updated | 2026-04-23 19:38:40 BST |
| owner | QA/Validation Agent |
| source_agent | AI/Perplexity Agent |

# AI Validation Handoff

## Purpose

Record the lightweight validation checks prepared and run during the initial AI/Perplexity scaffolding work so the QA/Validation Agent can review, extend, and formalize them later.

## Scope Validated

The checks cover initial scaffolding for:

- Python package importability under `/app/ai`.
- AI prompt, guardrail, and public helper imports.
- Markdown plus structured metadata parsing.
- Modelling-plan parsing and metadata validation for objective, risk appetite, selected assets, constraints, selected models, and data window.
- Pasted modelling-plan import error handling.
- Rejection of unsupported model metadata, future-only model text, and text/metadata conflicts.
- Fixed financial-advice detection used before safe refusal replacement.
- Review Mode detailed-context narrowing by referenced or visible model/output type.
- Review response metadata validation for referenced models, metrics, artifacts, output tables, and detailed-context requests.

The checks do not validate live Perplexity connectivity, Streamlit integration, frontend rendering, model execution, or full workflow acceptance criteria.

## Verification Commands

### Conflict Marker Scan

Command:

```bash
rg -n '(<{7}|={7}|>{7})' .
```

Purpose:

- Confirms the AI branch does not contain unresolved merge-conflict markers after pulling latest `main`.

Expected result:

- No output.
- Command exits with status `1` because `rg` found no matches.

### Full App Compile Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app
```

Purpose:

- Confirms all Python files under `/app` parse and compile after the AI changes and the latest `main` merge.
- Uses `/tmp/allocadabra-pycache-main` to avoid blocked macOS bytecode cache writes outside the workspace.

Expected result:

- Command exits with status `0`.

### AI Compile Check

Command:

```bash
env PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -m compileall app/ai
```

Purpose:

- Confirms every Python file under `/app/ai` parses and compiles.
- Uses `/tmp/allocadabra-pycache` because macOS system Python attempted to write bytecode under `~/Library/Caches`, which is blocked in the local sandbox.

Expected result:

- Command exits with status `0`.

### Dependency Lock Check

Command:

```bash
uv lock --check
```

Purpose:

- Confirms `uv.lock` is consistent with `pyproject.toml` after `perplexityai` was added by the dependency owner.

Expected result:

- Command exits with status `0`.
- In the local sandbox, this required escalation because `uv` needed to read its cache under `~/.cache/uv`.

### Processing Runtime Import Check

Command:

```bash
uv run python -c "from app.processing.dataset import build_canonical_price_dataframe; from app.processing.runner import generate_modelling_outputs; import pandas, riskfolio, cvxpy; print('processing imports ok')"
```

Purpose:

- Confirms the latest `main` processing/runtime imports still work after the AI branch was fast-forwarded.
- Confirms the shared project environment can import modelling dependencies.

Expected result:

- Prints `processing imports ok`.
- In the local sandbox, this required escalation because `uv` needed to read its cache under `~/.cache/uv`.

### Storage Export Import Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "import app.storage as s; assert callable(s.prepare_review_export_bundle); assert callable(s.get_review_download_all); print('storage export imports ok')"
```

Purpose:

- Confirms the latest `main` storage/export public imports remain available after the AI branch was updated.
- Confirms AI changes did not break package-level storage imports used by Review/export flow.

Expected result:

- Prints `storage export imports ok`.

### Parser Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.parsing import split_visible_text_and_metadata; text='## Objective\nTest\n<!-- allocadabra_metadata: {\"selected_model_ids\":[\"mean_variance\"]} -->'; visible, metadata = split_visible_text_and_metadata(text); assert metadata['selected_model_ids'] == ['mean_variance']; assert 'allocadabra_metadata' not in visible"
```

Purpose:

- Confirms AI-visible Markdown can be separated from app-readable metadata.
- Confirms valid JSON metadata is parsed into a dictionary.
- Confirms metadata is removed from the user-visible text before storage/display.

Expected result:

- Command exits with status `0`.

### Metadata Validation Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nMean Variance\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['mean_variance']}); assert result.valid"
```

Purpose:

- Confirms a complete modelling plan with all required V1 headings validates.
- Confirms supported model ID metadata is accepted.
- Confirms Markdown model names and metadata can coexist without rejection.

Expected result:

- Command exits with status `0`.

### Import And Safe Text Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "import app.ai; from app.ai.data_api import get_fixed_financial_advice_refusal, get_generic_safe_error; assert get_fixed_financial_advice_refusal(); assert get_generic_safe_error(); print('ai exports ok')"
```

Purpose:

- Confirms the public `app.ai` package imports.
- Confirms frontend-callable fixed financial-advice refusal text is available.
- Confirms frontend-callable generic safe-error text is available.

Expected result:

- Prints `ai exports ok`.

### Perplexity SDK Import Check

Command:

```bash
uv run python -c "import perplexity; from perplexity import Perplexity; print('perplexity sdk import ok')"
```

Purpose:

- Confirms the `perplexityai` dependency is installed through the project environment.
- Confirms the SDK import path used by `app.ai.provider` is available.
- Does not make a live Perplexity API call and does not require `PERPLEXITY_API_KEY`.

Expected result:

- Prints `perplexity sdk import ok`.

### `.env` Loader Smoke Check

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "import os; os.environ.pop('PERPLEXITY_API_KEY', None); from app.ai.provider import PerplexityProvider; provider = PerplexityProvider(); assert provider.api_key; print('dotenv loader ok')"
```

Purpose:

- Confirms `app.ai.provider.PerplexityProvider` loads `PERPLEXITY_API_KEY` from the local repo `.env` when the key is not already present in the process environment.
- Confirms AI runtime setup does not require a separate dotenv dependency.

Expected result:

- Prints `dotenv loader ok`.

### Review Detailed-Context Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.context_selection import select_review_detailed_context as s; ctx={'models': {'mean_variance': {'allocations':[1], 'drawdown':[2]}, 'risk_parity': {'allocations':[3]}}}; out=s(user_message='Why do Mean Variance weights differ?', visible_context=None, available_detailed_context=ctx); assert out == {'models': {'mean_variance': {'allocations': [1]}}}; print('review context smoke ok')"
```

Purpose:

- Confirms Review Mode does not inject all detailed model outputs by default.
- Confirms a user message referencing Mean Variance and weights selects only the Mean Variance allocation context.
- Confirms unrelated model payloads and unrelated output types are omitted.

Expected result:

- Prints `review context smoke ok`.

### Unsupported Metadata Rejection Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nMean Variance\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['worst_case']}); assert not result.valid; assert any('Unsupported model IDs' in issue or 'Future-only model IDs' in issue for issue in result.issues); print('unsupported metadata rejection ok')"
```

Purpose:

- Confirms unsupported or future-only model IDs in app-actable metadata are rejected.
- Confirms rejected metadata does not become executable plan metadata.

Expected result:

- Prints `unsupported metadata rejection ok`.

### Future-Only Text Rejection Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nWorst Case\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['mean_variance']}); assert not result.valid; assert any('Future-only models' in issue for issue in result.issues); print('future-only text rejection ok')"
```

Purpose:

- Confirms future-only model names in user-facing plan text are rejected even when metadata contains a supported model ID.
- Confirms the AI layer does not accept text/metadata combinations that could mislead the user about executable models.

Expected result:

- Prints `future-only text rejection ok`.

### Text/Metadata Conflict Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nMean Variance\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['risk_parity']}); assert not result.valid; assert any('text and metadata' in issue for issue in result.issues); print('text metadata conflict rejection ok')"
```

Purpose:

- Confirms visible plan text and app-actable metadata must agree on selected model IDs.
- Confirms conflicting metadata is rejected rather than silently adopted.

Expected result:

- Prints `text metadata conflict rejection ok`.

### Financial-Advice Detection Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import looks_like_financial_advice; assert looks_like_financial_advice('I recommend buying Bitcoin.'); assert looks_like_financial_advice('You should hold ETH.'); print('financial advice detection ok')"
```

Purpose:

- Confirms obvious buy/sell/hold/trade recommendation phrasing is detected before storage/display.
- Supports fixed refusal replacement for unsafe AI responses.

Expected result:

- Prints `financial advice detection ok`.

### Multi-Model Review Context Smoke Test

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.context_selection import select_review_detailed_context as s; ctx={'models': {'mean_variance': {'summary_metrics':[1], 'allocations':[2], 'transformation_metadata':[3], 'drawdown':[4]}, 'risk_parity': {'summary_metrics':[5], 'allocations':[6], 'transformation_metadata':[7]}}}; out=s(user_message='Why do Mean Variance and Risk Parity differ?', visible_context=None, available_detailed_context=ctx); assert set(out['models']) == {'mean_variance', 'risk_parity'}; assert set(out['models']['mean_variance']) == {'summary_metrics', 'allocations', 'transformation_metadata'}; print('multi-model context selection ok')"
```

Purpose:

- Confirms multi-model comparison questions inject only comparison-relevant details.
- Confirms summary metrics, allocations, and transformation metadata are included while unrelated output types are omitted.

Expected result:

- Prints `multi-model context selection ok`.

### Review Metadata Validation Smoke Tests

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_review_metadata; result=validate_review_metadata({'referenced_model_ids':['hierarchical_equal_risk']}); assert not result.valid; print('review metadata rejection ok')"
```

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -c "from app.ai.validation import validate_review_metadata; result=validate_review_metadata({'referenced_model_ids':['mean_variance'], 'referenced_metric_names':['Sharpe'], 'needs_detailed_context': True}); assert result.valid; assert result.metadata['needs_detailed_context'] is True; print('review metadata validation ok')"
```

Purpose:

- Confirms Review response metadata rejects unsupported/future-only model references.
- Confirms valid Review metadata is normalized into the typed app-actable shape.

Expected result:

- Prints `review metadata rejection ok`.
- Prints `review metadata validation ok`.

## Known Validation Gaps

- Live Perplexity provider verification now succeeds when `PERPLEXITY_API_KEY` is configured in local `.env`.
- The provider wrapper is implemented against the Perplexity SDK, `perplexityai` is included in `pyproject.toml` and `uv.lock`, and the SDK import path has been validated through `uv run`.
- No automated test suite or fixture-based unit tests exist yet.
- No Streamlit/frontend integration checks exist yet.
- No QA checks exist yet for actual Perplexity response shape drift.
- No end-to-end checks exist yet for generated plan confirmation, modelling handoff, Review opening generation, or chat lifecycle across phase transitions.

## Optional Live Provider Check

Command pattern used for task `076`:

```bash
uv run python - <<'PY'
from app.ai.provider import PerplexityProvider
from app.ai.prompts import configuration_chat_instructions, review_opening_instructions

provider = PerplexityProvider()

config = provider.complete(
    instructions=configuration_chat_instructions(),
    input_text=str({
        "latest_user_message": "What information do I still need before generating a modelling plan?",
        "active_user_inputs": {
            "selected_assets": [
                {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
                {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
            ],
            "treasury_objective": "Stable performance",
            "risk_appetite": "Medium",
            "constraints": {},
            "selected_models": ["mean_variance", "risk_parity"],
        },
    }),
    max_output_tokens=200,
)

review = provider.complete(
    instructions=review_opening_instructions(),
    input_text=str({
        "confirmed_modelling_plan": {
            "status": "confirmed",
            "markdown": "## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBitcoin, Ethereum\n## Constraints\nNone\n## Selected Models\nMean Variance, Risk Parity\n## Data Window\nLast 365 daily observations available from CoinGecko",
        },
        "user_preferences": {
            "treasury_objective": "Stable performance",
            "risk_appetite": "Medium",
        },
        "deterministic_ranking_summary": {
            "best_model_id": "risk_parity",
            "reason": "lower realized volatility in this run",
        },
        "model_output_summary": {
            "successful_models": [
                {"model_id": "mean_variance", "display_name": "Mean Variance"},
                {"model_id": "risk_parity", "display_name": "Risk Parity"},
            ],
            "failed_models": [],
        },
    }),
    max_output_tokens=220,
)

print("config ok")
print(config.text[:400].replace("\n", " "))
print("review ok")
print(review.text[:400].replace("\n", " "))
PY
```

Purpose:

- Confirms the live Perplexity provider path works through the project environment once `PERPLEXITY_API_KEY` is configured.
- Confirms both Configuration-style and Review-style prompts can complete against the live provider.

Observed result:

- Printed `config ok`.
- Printed `review ok`.
- Configuration and Review responses both returned non-empty text.

## Suggested QA Follow-Ups

- Convert the smoke commands into repeatable tests once the project test framework is chosen.
- Add fixture tests for fenced `allocadabra-metadata`, HTML-comment metadata, invalid JSON metadata, missing metadata, and malformed Markdown headings.
- Add metadata rejection tests for unsupported model IDs, future-only model names, missing required headings, unsupported constraints, invalid objective/risk appetite, invalid data windows, and conflicts between AI text and metadata.
- Add guardrail tests for obvious buy/sell/hold/trade advice and fixed refusal replacement.
- Add Review context-selection tests for visible model/output state, selected metric rows, open expanders, artifact/table IDs, HRP aliases, multiple referenced models, failed-model warnings, and no-detail default behaviour.
- Add provider contract tests with a fake Perplexity client before running any live API checks.
