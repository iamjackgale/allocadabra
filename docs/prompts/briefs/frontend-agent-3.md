| Metadata | Value |
|---|---|
| created | 2026-04-24 13:48:34 BST |
| last_updated | 2026-04-24 13:48:34 BST |
| prompt_used |  |

# Frontend Agent Brief 3

You are the Frontend Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Confirm whether `COINGECKO_API_KEY` and `PERPLEXITY_API_KEY` are available through repo-root `.env` or shell environment before running full live tests.
5. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/specs/app/ai-live-integration.md`
   - `/docs/specs/frontend/ui-design-build.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/specs/frontend/model-parameters.md`
   - `/docs/specs/frontend/model-review.md`
   - `/docs/specs/frontend/modelling-page.md`
   - `/docs/validation/frontend-validation.md`
   - `/docs/validation/general-validation.md`

## Primary Tasks

- `112`: Verify AI chat UI wiring in Configuration and Review, including loading states, recoverable failures, and safe-error display.
- `113`: Verify visible Review context is correctly passed into Review Mode without exposing internal context payloads to the user.
- `105`: Run an end-to-end local smoke test covering happy path, validation failure, modelling failure, partial model success, and export/download availability.
- `119`: Run full live end-to-end Streamlit validation once `COINGECKO_API_KEY` and `PERPLEXITY_API_KEY` are configured.

## Current Runtime Paths

Start the app:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Standard app:

```text
http://localhost:8501
```

Synthetic Review fixture:

```text
http://localhost:8501/?alloca_dev_review_fixture=1
```

Frontend-only Review fixture without live Perplexity:

```text
http://localhost:8501/?alloca_dev_review_fixture=frontend-check&alloca_dev_no_ai_env=1
```

Missing-key Configuration path:

```text
http://localhost:8501/?alloca_dev_no_ai_env=1
```

The synthetic Review fixture intentionally writes synthetic outputs through the existing local workflow/export path. It avoids CoinGecko and modelling, but it replaces the active local workflow for that app session.

## Task 112 Requirements

Verify the chat UI in both Configuration and Review modes.

Check at minimum:

- User messages render immediately after send.
- Assistant loading state is visible while the request is pending.
- Recoverable AI errors render as user-facing errors, not Python tracebacks.
- `Retry last message` is visible and preserves the original user message after a failed call.
- Three consecutive failures disable chat input and prompt refresh, if that path is reachable without code changes.
- Safe-error display uses the AI layer's fixed safe messages where applicable.
- Configuration and Review chat histories remain separate.
- Configuration chat survives modelling failure/return-to-configuration where the current app supports that path.
- Review chat resets when `Start New Model` is confirmed.

Use the missing-key path for a deterministic no-secret failure check:

```text
http://localhost:8501/?alloca_dev_no_ai_env=1
```

## Task 113 Requirements

Verify visible Review context handoff.

Use the synthetic Review fixture:

```text
http://localhost:8501/?alloca_dev_review_fixture=1
```

Check at minimum:

- The Review screen opens with the expected synthetic outputs.
- The selected Review section and selected model are reflected in the context passed to Review Mode.
- Risk Parity allocation weights context is available when that synthetic section/model is selected.
- The user does not see raw context payloads, JSON metadata, hidden prompt contents, or internal context-selection labels.
- The Review chat response can refer to the visible output naturally, without exposing implementation details.

If you find that Frontend is not passing enough context into the AI layer, return a mini spec for the relevant owner instead of editing AI code directly.

## Task 105 Requirements

Run a local end-to-end smoke test matrix through the Streamlit app.

Cover at minimum:

- happy path from Configuration -> Generate Plan -> Run Models -> Review Results
- deterministic validation failure before AI plan generation
- modelling failure state
- partial model success state
- export/download availability in Review
- `Download All` behavior
- individual artifact download behavior
- `Return To Configure`
- `Start New Model`
- page refresh behavior after Review is ready

Prefer real app callables and local cached data where practical. If live CoinGecko or Perplexity is unavailable, use the clearest available local/dev fixture path and document exactly what was and was not covered.

If you uncover Backend/Data, Modelling, or AI contract gaps, do not patch other agents' folders. Return mini specs with:

- target files or folders
- requested owner agent
- reproduction path
- observed behavior
- expected behavior
- risk or dependency notes

## Task 119 Requirements

Run full live end-to-end Streamlit validation only when both credentials are configured:

- `COINGECKO_API_KEY`
- `PERPLEXITY_API_KEY`

Cover the full user flow:

1. Load app.
2. Load/search CoinGecko token list.
3. Select 2-10 assets.
4. Set objective, risk appetite, model selection, and optional constraints.
5. Generate and accept a Perplexity modelling plan.
6. Run models using live/cached CoinGecko price data.
7. Enter Review.
8. Inspect summary metrics and at least one per-model output.
9. Ask one Review Mode question.
10. Download one individual artifact and `Download All`.

Do not mark `119` complete if either credential is missing or if the live run is replaced entirely by fixtures. In that case, report `119` as blocked with the exact missing prerequisite.

## Boundaries

Own:

- `/frontend/**`
- Frontend-owned validation docs

Do not edit:

- `/app/ai/**`
- `/app/storage/**`
- `/app/processing/**`
- shared dependencies

If the UI needs a callable shape changed, produce a mini spec for the owner agent.

## Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

Start the app and record the exact URL paths used:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Update `/docs/validation/frontend-validation.md` with:

- task `112` chat UI results;
- task `113` visible Review context results;
- task `105` smoke matrix results;
- task `119` live validation results or explicit blocker;
- any mini specs needed for other owner agents.

## Reporting Back

When complete, report:

- tasks completed;
- files changed;
- validation commands and outcomes;
- URLs tested;
- screenshots or observations if relevant;
- unresolved gaps by owner agent;
- whether Orchestrator can proceed with task `106`.
