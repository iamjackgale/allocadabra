| Metadata | Value |
|---|---|
| created | 2026-04-23 12:29:28 BST |
| last_updated | 2026-04-23 12:29:28 BST |
| prompt_used | |

# Modelling Agent Brief 1

You are the Modelling Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review all specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/data-backend/dataset-building.md`
   - `/docs/specs/data-backend/riskfolio-lib.md`
   - `/docs/specs/app/export-bundling.md`
   - `/docs/specs/data-backend/session-storage.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/modelling-validation.md`

## Primary Tasks

- `031`: Define the frontend-callable modelling app-layer contract.
- `066`: Define and implement the active workflow modelling run interface.
- `067`: Add structured progress callback/event support.
- `068`: Integrate active workflow and cached price histories with the modelling runner without taking over Backend/Data export ownership.

## Scope

- Own `/app/processing/**`.
- You may read `/app/storage/**`, but do not rewrite Backend/Data storage or export packaging logic.
- Backend/Data owns cache/session/export bundle creation.
- Modelling owns model execution, output artifact generation, failed model details, and modelling progress events.

## Expected Direction

- Add a high-level callable such as `run_active_modelling(...)`.
- Read active workflow inputs, selected models, and selected assets.
- Use existing Backend/Data APIs for cached price histories rather than duplicating storage logic.
- Call existing modelling generation code.
- Return a frontend-safe shape with:
  - `ok`
  - `successful_models`
  - `failed_models`
  - `artifacts`
  - `missing_artifacts`
  - `errors`
  - `user_message`
- Support an optional progress callback with checkpoint phases:
  - `validation`
  - `ingestion`
  - `datasets`
  - `modelling`
  - `analysis`
  - `outputs`

## Boundaries

- Do not create zip bundles.
- Do not own final export manifest storage.
- If Backend/Data needs a new adapter, return a mini spec instead of editing their area directly.
- Keep model IDs stable: `mean_variance`, `risk_parity`, `hierarchical_risk_parity`.

## Validation

- Run relevant commands from `/docs/validation/general-validation.md`.
- Add or update `/docs/validation/modelling-validation.md` with any new smoke checks.
- If you add callable interfaces, document their return shape clearly.
- Update `/docs/tasks.md` only if instructed by Orchestrator; otherwise report task completion/status back.
