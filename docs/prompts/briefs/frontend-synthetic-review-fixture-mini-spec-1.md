| Metadata | Value |
|---|---|
| created | 2026-04-24 13:11:42 BST |
| last_updated | 2026-04-24 13:11:42 BST |
| prompt_used | |

# Frontend Mini Spec: Synthetic Review Fixture 1

You are the Frontend Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/ai-live-integration.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/validation/ai-validation.md`
   - `/docs/validation/frontend-validation.md`

## Primary Task

- Add a frontend-owned synthetic Review fixture entry point so the AI Agent can run `RM-1`, `RM-2`, `RM-3`, and transcript-quality Review tests from `/docs/specs/app/ai-live-integration.md`.

## Why This Matters

AI live integration is ready for Configuration Mode and general provider checks, but Review Mode live testing currently lacks a way to load the fixed synthetic Review manifest into the running Streamlit app without running CoinGecko ingestion and modelling.

The AI Agent also needs a non-destructive missing-key test path for `CM-4`.

## Required Behavior

Add a local/dev-only way to load the fixed synthetic Review fixture from `/docs/specs/app/ai-live-integration.md` into the running app.

The fixture path must:

- load the synthetic confirmed modelling plan
- load synthetic user preferences
- load synthetic model output summary
- load Risk Parity allocation weights visible context
- enter Review Mode without real CoinGecko calls
- allow the Review chat to run normally against Perplexity
- avoid polluting real user workflow outputs where practical

Preferred shape:

- A dev-only Streamlit control or query-parameter path is acceptable.
- It must not be shown as normal user-facing functionality in the standard workflow.
- Keep the implementation simple and clearly marked as local validation support.

## Missing-Key Test Hook

Provide a non-destructive way for the AI Agent to verify `CM-4` missing `PERPLEXITY_API_KEY` behavior.

Acceptable options:

- a dev-only flag/query parameter/session toggle that suppresses AI `.env` loading for one app run
- or a clearly documented manual validation path using a temporary env-free launch

The missing-key path must:

- not delete or edit the user's real `.env`
- not print secrets
- allow the UI to show the recoverable missing-key error
- preserve active Configuration inputs

## Boundaries

- Own `/frontend/**` and Frontend-owned validation docs.
- Do not edit AI provider/prompt code unless Orchestrator approves a separate mini spec.
- Do not edit Backend/Data or Modelling logic.
- Do not add a new dependency.

## Validation

- Run `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app`.
- Run `uv lock --check`.
- Start the Streamlit app and verify the synthetic Review fixture can open Review Mode.
- Verify the missing-key path displays a user-facing recoverable error, not a Python traceback.
- Update `/docs/validation/frontend-validation.md` with the exact validation steps.

## Reporting Back

When done, report:

- files changed
- exact command or UI path for loading the synthetic Review fixture
- exact command or UI path for missing-key validation
- whether AI can resume tasks `108`, `114`, and `115`
- any limitations that should be reflected in `/docs/specs/app/ai-live-integration.md`
