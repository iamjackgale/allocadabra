| Metadata | Value |
|---|---|
| created | 2026-04-24 13:46:50 BST |
| last_updated | 2026-04-24 13:46:50 BST |
| prompt_used |  |

# AI/Perplexity Agent Brief 3

You are the AI/Perplexity Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Confirm `PERPLEXITY_API_KEY` is available through the repo-root `.env` or shell environment for live tests, except when running the explicit missing-key test path.
5. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/ai-live-integration.md`
   - `/docs/specs/ai/ai-model-integration.md`
   - `/docs/specs/ai/parameters-agent.md`
   - `/docs/specs/ai/review-agent.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/validation/ai-validation.md`
   - `/docs/validation/frontend-validation.md`

## Primary Tasks

- `107`: Run live Configuration Mode verification tests `CM-1` through `CM-4`.
- `108`: Run live Review Mode verification tests `RM-1` through `RM-3` using the synthetic Review fixture.
- `109`: Validate live guardrails `GR-1` through `GR-4`.
- `110`: Refine Configuration Mode prompt behaviour based on live UI usage.
- `111`: Refine Review Mode prompt behaviour based on live UI usage.
- `114`: Run a live transcript-quality review for Configuration and Review modes and prepare the gap list for Orchestrator review.

## Current Runtime Paths

Start the app:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Configuration Mode starts at:

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

Missing-key Configuration Mode path:

```text
http://localhost:8501/?alloca_dev_no_ai_env=1
```

The synthetic Review fixture intentionally writes synthetic outputs through the existing local workflow/export path. It avoids CoinGecko and modelling, but it replaces the active local workflow for that app session. Treat it as a local validation mode, not a read-only overlay.

## Required Live Test Coverage

Use `/docs/specs/app/ai-live-integration.md` as the source of truth.

Configuration Mode:

- `CM-1`: minimal complete configuration.
- `CM-2`: incomplete configuration.
- `CM-3`: invalid or unsupported constraints.
- `CM-4`: missing `PERPLEXITY_API_KEY` path using `?alloca_dev_no_ai_env=1`.

Review Mode:

- `RM-1`: Review opening from the synthetic Review fixture.
- `RM-2`: visible context injection for Risk Parity allocation weights.
- `RM-3`: follow-up chat grounded in the synthetic manifest.

Guardrails:

- `GR-1`: buy/sell financial advice request.
- `GR-2`: direct model-choice request.
- `GR-3`: unsupported live-data/source request.
- `GR-4`: unsupported model request.

Transcript-quality review:

- Run a short representative Configuration transcript.
- Run a short representative Review transcript using the synthetic fixture.
- Assess default response length, educational/neutral tone, recommendation strength, unsupported request handling, metadata quality, and whether the answers stay grounded in app state or synthetic outputs.
- Prepare a concise gap list for Orchestrator review under task `115`.

## Implementation Scope

Own:

- `/app/ai/**`
- AI-owned prompt/spec updates
- `/docs/validation/ai-validation.md`

Do not edit:

- `/frontend/**`, unless Orchestrator explicitly approves a Frontend mini spec
- `/app/storage/**`
- `/app/processing/**`
- shared dependency files

If live testing shows a Frontend, Backend/Data, or Modelling issue, do not fix it directly. Return a mini spec with:

- target files or folders
- requested owner agent
- observed failure
- expected behaviour
- reproduction path
- risk or dependency notes

## Prompt Refinement Rules

For tasks `110` and `111`, make the smallest prompt or validation change that fixes observed live behaviour.

Configuration Mode prompt refinements should focus on:

- asking only for required missing fields
- not treating optional constraints as required
- clearly redirecting unsupported constraints to supported controls
- avoiding asset recommendations or financial advice
- keeping selected model IDs within the supported model registry

Review Mode prompt refinements should focus on:

- neutral trade-off explanation
- acceptable recommendation phrasing, e.g. `Risk Parity best matches your stated preference in this run`
- avoiding phrases such as `Choose Risk Parity` or `You should use Risk Parity`
- using visible Review context without exposing raw context payloads
- not inventing metrics, charts, live prices, or sources

## Acceptance Criteria

Tasks `107`, `108`, and `109` are complete only when every named test in `/docs/specs/app/ai-live-integration.md` has either passed or has a documented gap with an owner and next action.

Tasks `110` and `111` are complete only when:

- any prompt/validation changes needed from live testing are implemented;
- no unsupported model names appear in app-actable metadata;
- financial-advice responses are safely refused or post-processed;
- response length and recommendation strength match the spec.

Task `114` is complete only when:

- Configuration and Review transcript-quality notes exist in `/docs/validation/ai-validation.md` or a clearly referenced AI validation note;
- any remaining gaps are concise enough for Orchestrator task `115`;
- Frontend/Backend/Modelling handoff items are written as mini specs if needed.

## Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/ai
uv lock --check
```

Also update `/docs/validation/ai-validation.md` with:

- live test paths used;
- pass/fail outcome for `CM-1` through `CM-4`;
- pass/fail outcome for `RM-1` through `RM-3`;
- pass/fail outcome for `GR-1` through `GR-4`;
- transcript-quality notes;
- prompt refinements made;
- any open gaps and recommended owner.

## Reporting Back

When complete, report:

- tasks completed;
- files changed;
- live test outcomes;
- prompt refinements made;
- unresolved gaps by owner agent;
- whether Orchestrator can proceed with task `115`.
