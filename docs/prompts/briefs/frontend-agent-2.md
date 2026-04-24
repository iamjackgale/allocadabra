| Metadata | Value |
|---|---|
| created | 2026-04-24 07:54:20 BST |
| last_updated | 2026-04-24 07:54:20 BST |
| prompt_used | 2026-04-24 08:01:13 BST |

# Frontend Agent Brief 2

You are the Frontend Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/specs/frontend/ui-design-build.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/specs/frontend/model-parameters.md`
   - `/docs/specs/frontend/model-review.md`
   - `/docs/specs/frontend/modelling-page.md`
   - `/docs/validation/frontend-validation.md`

## Current Mainline Progress

The Orchestrator has merged:

- Frontend first Streamlit pass in `/frontend/**`.
- Backend/Data task `092` deterministic configuration validation.
- Modelling cooperative cancellation support using `cancel_check`.
- Frontend/Backend/Modelling integration spec at `/docs/specs/app/frontend-backend-modelling-integration.md`.

The first-pass frontend implementation tasks are marked complete:

- `032`
- `051`
- `052`
- `053`
- `054`
- `055`
- `098`
- `099`
- `100`
- `101`
- `102`

## Primary Task

- `120`: Pull latest `main`, adopt Backend task `092` validation issue codes, adopt Modelling cooperative cancellation, and report any remaining UI integration gaps.

## Immediate Work

1. Re-review the current `/frontend/**` implementation against latest `main`.
2. Confirm Configuration validation correctly consumes Backend/Data issue shape:
   - `field`
   - `code`
   - `message`
   - optional `context`
3. Confirm the UI handles the new task `092` issue codes without parsing message text.
4. Pass a session-state-backed `cancel_check` into `run_active_modelling(...)`.
5. Treat `modelling_cancelled` as a user-requested cancellation, not as a generic modelling failure.
6. Re-run frontend validation commands from `/docs/validation/frontend-validation.md`.
7. Report any remaining gaps that require Backend/Data, Modelling, AI, or QA ownership.

## Boundaries

- Own `/frontend/**` and Frontend-owned docs.
- Do not edit Backend/Data validation logic.
- Do not edit Modelling execution logic.
- Do not edit AI prompt/provider logic.
- If a callable shape is still insufficient, return a mini spec rather than patching another agent's folder.

## Known Open Work

- Task `105` remains open for the broader local smoke test matrix.
- Task `112` and task `113` remain open for AI chat UI verification in live integrated use.
- Task `119` remains open until `COINGECKO_API_KEY` and `PERPLEXITY_API_KEY` are configured for a full live Streamlit run.
