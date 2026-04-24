| Metadata | Value |
|---|---|
| created | 2026-04-24 13:13:47 BST |
| last_updated | 2026-04-24 13:13:47 BST |
| prompt_used |  |

# AI/Perplexity Agent Brief 2

You are the AI/Perplexity Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/ai/ai-model-integration.md`
   - `/docs/specs/ai/parameters-agent.md`
   - `/docs/specs/ai/review-agent.md`
   - `/docs/specs/data-backend/riskfolio-lib.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/ai-validation.md`
   - `/docs/validation/modelling-validation.md`

## Primary Task

- `081`: Align AI supported-model validation with the Modelling-owned supported-model registry now that a stable app-layer modelling contract exists.

## Why This Can Proceed Now

The live AI integration tasks remain partly blocked by the Frontend synthetic Review fixture, but `081` is independent of that fixture.

The Modelling Agent has exposed a stable frontend-callable modelling contract through `/app/processing/**`. The AI layer should now stop relying on duplicated hardcoded model definitions where a Modelling-owned source can be used safely.

## Scope

- Own `/app/ai/**`.
- You may update AI specs and AI validation docs.
- You may read `/app/processing/**` and call the Modelling-owned contract helper, but do not edit Modelling code.
- Do not edit Frontend UI code, Backend/Data storage/export code, or shared dependency files.

## Required Direction

Create one AI-owned helper for supported model access and validation.

Expected behavior:

- Load supported model IDs and labels from the Modelling-owned contract where practical.
- Validate Configuration Mode metadata against that source.
- Validate Review Mode metadata against that source.
- Ensure unsupported and future-only model IDs are rejected consistently.
- Ensure prompt builders mention only the currently supported model set.
- Keep the V1 supported model set aligned to:
  - `mean_variance`
  - `risk_parity`
  - `hierarchical_risk_parity`

If importing the Modelling contract creates circular-import or runtime-weight problems, keep a fixed V1 fallback inside one AI-owned helper only. Document the fallback clearly in code and validation docs.

## Acceptance Criteria

- There is a single AI-owned path for supported-model validation.
- Configuration plan metadata cannot accept unsupported model IDs.
- Review response metadata cannot reference unsupported model IDs.
- Prompt text cannot drift into unsupported or future-only model names.
- Existing financial-advice, invalid-metadata, and text/metadata conflict protections continue to pass.
- AI specs or validation docs are updated if supported-model behavior changes.

## Suggested Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/ai
uv lock --check
```

Add a lightweight smoke check that verifies:

- supported model IDs load from the Modelling contract or documented fallback;
- `mean_variance`, `risk_parity`, and `hierarchical_risk_parity` are accepted;
- unsupported IDs are rejected;
- future-only model IDs are rejected;
- Configuration and Review metadata validation use the same supported-model source.

Update `/docs/validation/ai-validation.md` with the exact commands used.

## Reporting Back

When complete, report:

- files changed;
- whether the AI layer reads the Modelling contract directly or uses a fallback;
- validation commands and outcomes;
- whether `081` is complete;
- whether remaining live AI tasks are still blocked only by the synthetic Review fixture.
