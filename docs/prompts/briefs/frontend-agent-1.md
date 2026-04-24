| Metadata | Value |
|---|---|
| created | 2026-04-23 20:26:05 BST |
| last_updated | 2026-04-23 20:26:05 BST |
| prompt_used | |

# Frontend Agent Brief 1

You are the Frontend Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/prompts/agents/frontend-agent.md`
   - `/docs/specs/frontend/ui-design-build.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/specs/frontend/model-parameters.md`
   - `/docs/specs/frontend/model-review.md`
   - `/docs/specs/frontend/modelling-page.md`
   - `/docs/prompts/briefs/frontend-agent-modelling-contract-1.md`
   - `/docs/prompts/briefs/backend-data-validation-mini-spec-1.md`
   - `/docs/prompts/briefs/frontend-runtime-dependency-mini-spec-1.md`
   - `/docs/validation/general-validation.md`

## Start Condition

You can now begin core Frontend implementation.

Resolved:

- `streamlit` is now in shared project dependencies.
- The Modelling app-layer contract is now merged into `main`.
- The Backend/Data storage, AI, and export interfaces already exist for Frontend integration.

Known gap still open:

- Backend/Data task `092` has not landed yet. Deterministic validation still needs stronger issue-code coverage for unsupported model IDs and impossible constraint combinations.

Treat task `092` as a bounded integration gap, not a reason to wait. Build the Frontend against the current validation callable and keep error handling thin so the stronger Backend issue codes can slot in when they land.

## Primary Tasks

- `032`: decide and implement the one-open-section Review behaviour.
- `051`: implement `/docs/specs/frontend/agent-chat.md`.
- `052`: implement `/docs/specs/frontend/model-parameters.md`.
- `053`: implement `/docs/specs/frontend/model-review.md`.
- `054`: implement `/docs/specs/frontend/modelling-page.md`.
- `055`: implement `/docs/specs/frontend/ui-design-build.md`.

## Scope

- Own Frontend files and Frontend-owned docs only.
- Use the current app-layer callable surfaces from:
  - `app.storage.data_api`
  - `app.ai.data_api`
  - `app.processing`
- Do not change Backend/Data validation semantics yourself.
- Do not edit Modelling, AI, or shared dependency files unless a new mini spec is approved.

## Implementation Guidance

- Start with the phase shell and navigation flow:
  - Configuration
  - Modelling
  - Review
- Implement Configuration against current token-loading, state, and AI plan-generation APIs.
- Implement Modelling against `run_active_modelling(...)` and its progress events.
- Implement Review against the current export manifest and modelling artifact contract.
- For the one-open-section Review requirement, prefer explicit Frontend-controlled section state over brittle implicit expander behavior.
- For validation:
  - consume current validation issues as-is
  - avoid hard-coding fragile assumptions about exact issue-code coverage
  - isolate any mapping logic so Backend task `092` can be adopted with minimal rewrite

## Boundaries

- Do not block on polished validation messaging before starting.
- Do not read storage files directly when app-layer callables already exist.
- Do not invent new model IDs, artifact types, or workflow phases.
- If the Frontend needs new fields from Modelling or Backend/Data, return a mini spec instead of patching other owned areas directly.

## Validation

- Run relevant checks from `/docs/validation/general-validation.md`.
- Run `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app`.
- If you start a Streamlit entrypoint, report the command and local URL.
- Report clearly which pieces are complete versus temporarily waiting on Backend task `092`.

## Reporting Back

When done with the first implementation pass, report:

- which frontend tasks were completed
- what app entrypoint or page structure was added
- which current Backend/Data validation gaps still affect UX
- any mini specs needed from other agents
