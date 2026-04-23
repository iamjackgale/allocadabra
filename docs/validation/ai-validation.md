| Metadata | Value |
|---|---|
| created | 2026-04-23 12:02:46 BST |
| last_updated | 2026-04-23 12:02:46 BST |
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
- Modelling-plan metadata validation for supported model IDs.
- Pasted modelling-plan import error handling.
- Review Mode detailed-context narrowing by referenced or visible model/output type.

The checks do not validate live Perplexity connectivity, Streamlit integration, frontend rendering, model execution, or full workflow acceptance criteria.

## Verification Commands

### Compile Check

Command:

```bash
env PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache python3 -m compileall app/ai
```

Purpose:

- Confirms every Python file under `/app/ai` parses and compiles.
- Uses `/tmp/allocadabra-pycache` because macOS system Python attempted to write bytecode under `~/Library/Caches`, which is blocked in the local sandbox.

Expected result:

- Command exits with status `0`.

### Parser Smoke Test

Command:

```bash
python3 -c "from app.ai.parsing import split_visible_text_and_metadata; text='## Objective\nTest\n<!-- allocadabra_metadata: {\"selected_model_ids\":[\"mean_variance\"]} -->'; visible, metadata = split_visible_text_and_metadata(text); assert metadata['selected_model_ids'] == ['mean_variance']; assert 'allocadabra_metadata' not in visible"
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
python3 -c "from app.ai.validation import validate_modelling_plan; md='## Objective\nStable performance\n## Risk Appetite\nMedium\n## Selected Assets\nBTC, ETH\n## Constraints\nNone\n## Selected Models\nMean Variance\n## Data Window\nLast 365 daily observations'; result=validate_modelling_plan(md, {'selected_model_ids':['mean_variance']}); assert result.valid"
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
python3 -c "import app.ai; from app.ai.data_api import get_fixed_financial_advice_refusal, get_generic_safe_error; assert get_fixed_financial_advice_refusal(); assert get_generic_safe_error()"
```

Purpose:

- Confirms the public `app.ai` package imports.
- Confirms frontend-callable fixed financial-advice refusal text is available.
- Confirms frontend-callable generic safe-error text is available.

Expected result:

- Command exits with status `0`.

### Review Detailed-Context Smoke Test

Command:

```bash
python3 -c "from app.ai.context_selection import select_review_detailed_context as s; ctx={'models': {'mean_variance': {'allocations':[1], 'drawdown':[2]}, 'risk_parity': {'allocations':[3]}}}; out=s(user_message='Why do Mean Variance weights differ?', visible_context=None, available_detailed_context=ctx); assert out == {'models': {'mean_variance': {'allocations': [1]}}}"
```

Purpose:

- Confirms Review Mode does not inject all detailed model outputs by default.
- Confirms a user message referencing Mean Variance and weights selects only the Mean Variance allocation context.
- Confirms unrelated model payloads and unrelated output types are omitted.

Expected result:

- Command exits with status `0`.

## Known Validation Gaps

- No live Perplexity API request was run because that requires `PERPLEXITY_API_KEY` and the `perplexityai` dependency to be installed.
- The provider wrapper is implemented against the Perplexity SDK, but `pyproject.toml` and `uv.lock` still need a dependency-owner update to add `perplexityai`.
- No automated test suite or fixture-based unit tests exist yet.
- No Streamlit/frontend integration checks exist yet.
- No QA checks exist yet for actual Perplexity response shape drift.
- No end-to-end checks exist yet for generated plan confirmation, modelling handoff, Review opening generation, or chat lifecycle across phase transitions.

## Suggested QA Follow-Ups

- Convert the smoke commands into repeatable tests once the project test framework is chosen.
- Add fixture tests for fenced `allocadabra-metadata`, HTML-comment metadata, invalid JSON metadata, missing metadata, and malformed Markdown headings.
- Add metadata rejection tests for unsupported model IDs, future-only model names, missing required headings, and conflicts between AI text and metadata.
- Add guardrail tests for obvious buy/sell/hold/trade advice and fixed refusal replacement.
- Add Review context-selection tests for visible model/output state, HRP aliases, multiple referenced models, failed-model warnings, and no-detail default behaviour.
- Add provider contract tests with a fake Perplexity client before running any live API checks.
