| Metadata | Value |
|---|---|
| created | 2026-04-24 07:20:53 BST |
| last_updated | 2026-04-24 07:20:53 BST |
| prompt_used | |

# Backend/Data Agent Brief 2

You are the Backend/Data Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/frontend/model-parameters.md`
   - `/docs/specs/data-backend/session-storage.md`
   - `/docs/prompts/briefs/backend-data-validation-mini-spec-1.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/backend-validation.md`

## Primary Task

- `092`: Implement deterministic configuration validation for unsupported model IDs and impossible constraint combinations, with stable field-specific issue codes for the Frontend Configuration flow.

## Why This Matters

The Frontend Agent can start core implementation, but it needs deterministic validation errors so the Configuration screen can block invalid submissions before AI plan generation or modelling starts.

## Scope

- Own `/app/storage/**` and Backend/Data validation docs.
- Do not edit Frontend UI code, Modelling execution code, AI prompt logic, or shared dependency files.
- Keep this focused on deterministic validation and issue-code shape.

## Required Validation Coverage

At minimum, validate:

- unsupported selected model IDs
- duplicate or malformed model selections if relevant to the current input shape
- impossible global allocation constraints
- impossible selected-asset allocation constraints
- contradictory min/max percentage constraints
- impossible min/max asset-count constraints
- allocation sums that cannot be satisfied by the current selected asset count

## Required Return Shape

Use stable machine-readable issue codes and field references so Frontend can render errors predictably.

Each issue should include:

- `code`
- `field`
- `message`
- optional structured context where useful, such as `model_id`, `constraint_id`, `asset_id`, `min_value`, `max_value`, or `selected_asset_count`

Prefer extending the existing validation result shape rather than introducing a parallel validation API.

## Suggested Issue Codes

Use or refine these codes if they fit the existing implementation:

- `unsupported_model_id`
- `duplicate_model_id`
- `invalid_constraint_value`
- `constraint_min_exceeds_max`
- `constraint_sum_impossible`
- `asset_count_min_exceeds_max`
- `asset_count_constraint_impossible`
- `selected_asset_constraint_unknown_asset`

## Boundaries

- Do not change the supported model set.
- Do not redesign constraint UX.
- Do not introduce AI validation as a substitute for deterministic checks.
- Do not add a new test framework in this pass.

## Validation

- Run relevant checks from `/docs/validation/general-validation.md`.
- Run Backend/Data validation checks from `/docs/validation/backend-validation.md`.
- Run `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/storage`.
- Add or update focused smoke coverage for:
  - unsupported model ID
  - impossible allocation sums
  - contradictory min/max constraints
  - impossible asset-count constraints

## Reporting Back

When done, report:

- exact callable(s) changed
- final issue-code shape
- validation commands run
- any remaining validation cases deferred to Frontend, Modelling, or QA
