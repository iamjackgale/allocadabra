| Metadata | Value |
|---|---|
| created | 2026-04-24 07:19:40 BST |
| last_updated | 2026-04-24 07:42:52 BST |

# Frontend/Backend/Modelling Integration

## Purpose

Define the end-to-end integration contract for the Configuration -> Modelling -> Review flow across Frontend, Backend/Data, and Modelling.

## Status

Ready for implementation. This spec defines the V1 integration contract for the first end-to-end Frontend/Backend/Modelling pass.

## Initial Scope

- Phase routing and state transitions.
- Configuration validation and AI plan confirmation handoff.
- Modelling execution, progress events, retry/failure states, and partial success.
- Review readiness, artifact handoff, export manifest preparation, and downloads.
- Agent ownership boundaries and validation checks.

## Phase State Machine

The canonical user-facing phases are:

- `configuration`
- `modelling`
- `review`

Recommended internal sub-states:

| Phase | Sub-State | Purpose |
|---|---|---|
| `configuration` | `editing_inputs` | User can edit assets, objective, risk appetite, models, and optional constraints. |
| `configuration` | `generating_plan` | App has copied current inputs and is waiting for Perplexity to return a modelling plan. |
| `configuration` | `reviewing_plan` | Model Configuration Component is replaced by rendered Markdown plan with `Run Models`, `Regenerate`, and `Configure` actions. |
| `modelling` | `running` | App is validating, loading prices, building datasets, running models, preparing outputs, and emitting progress events. |
| `modelling` | `failed_retryable` | A recoverable failure happened and user can retry from the Modelling screen. |
| `modelling` | `failed_return_to_config` | A non-recoverable modelling failure happened and user should return to Configuration. |
| `modelling` | `partial_success` | At least one model succeeded and at least one failed; user can continue to Review with failed-model reasons. |
| `modelling` | `ready_for_review` | Required Review artifacts and manifest are available; user can click `Review Results`. |
| `review` | `active` | User can inspect outputs, download artifacts, and ask Review Mode questions. |

V1 does not need explicit `cancelled` or `interrupted` sub-states. These should be handled through `failed_return_to_config` messaging. Interrupted-run resume is a V2 extension.

## Configuration Handoff

### Generate Plan

When the user clicks `Generate Plan`:

1. Frontend takes a snapshot of the current Model Configuration Component state.
2. Frontend/Backend runs deterministic configuration validation where available.
3. App builds the Configuration Mode prompt by injecting:
   - current user inputs
   - app guardrails
   - supported V1 model set
   - modelling plan output requirements
4. AI layer sends the prompt to Perplexity.
5. AI layer receives Markdown plus structured metadata.
6. App validates returned metadata against supported model and configuration rules.
7. Frontend converts the accepted plan into a frontend-ready rendered Markdown view.
8. Model Configuration Component is replaced by the plan review view.

Plan review actions:

| Action | Result |
|---|---|
| `Run Models` | Confirms the modelling plan and enters the pre-modelling handoff. |
| `Regenerate` | Re-runs the AI plan generation using the current input snapshot and latest user context. |
| `Configure` | Returns to editable configuration inputs and invalidates the displayed plan. |

### Run Models

When the user clicks `Run Models`:

1. User is confirming the displayed Modelling Plan.
2. App persists the confirmed plan in session state.
3. App derives the technical model inputs required for selected models and analyses.
4. Derived technical inputs are validated deterministically before the Modelling Phase begins.
5. If valid, the app transitions to `modelling.running`.
6. Modelling Phase begins:
   - validation
   - data gathering
   - dataframe building
   - transformations
   - riskfolio-lib model execution
   - output analysis
   - chart/table/artifact generation
   - export manifest preparation
   - ready-for-review state

V1 decision:

- Keep model execution deterministic after plan confirmation.
- The AI plan can select supported models and explain intent.
- Model IDs, constraints, transformations, and `riskfolio-lib` execution inputs must come from app state and fixed model registry rules.
- Perplexity should not generate solver/runtime parameters for model execution in V1.

## Modelling Handoff

Current expected call sequence:

1. Frontend calls Backend/Data validation for active configuration.
2. Frontend calls AI plan generation and confirmation flow.
3. Frontend persists/uses confirmed modelling plan state through Backend/Data session callables.
4. Frontend calls `app.processing.run_active_modelling(...)`.
5. Modelling calls Backend/Data APIs to:
   - read active workflow state
   - validate active configuration
   - fetch cached or refreshed price histories
6. Modelling returns:
   - `ok`
   - `successful_models`
   - `failed_models`
   - `artifacts`
   - `missing_artifacts`
   - `errors`
   - `user_message`
   - `progress_events`
   - `dataset_metadata`
   - `output_dir`
7. Frontend calls Backend/Data export preparation with:
   - `modelling_artifacts`
   - `failed_models`
   - `missing_artifacts`
8. Backend/Data prepares the Review export manifest and marks the workflow ready for Review.
9. Frontend enters `modelling.ready_for_review`.
10. User clicks `Review Results`.
11. Frontend enters `review.active`.

Ownership:

| Area | Owner |
|---|---|
| UI phase flow and user actions | Frontend Agent |
| Active session state, validation, cache, export manifest, downloads | Backend/Data Agent |
| Dataset construction, model execution, metrics, chart/table artifacts, progress events | Modelling Agent |
| Configuration and Review chat/plan calls | AI/Perplexity Agent |

V1 decision:

- Frontend orchestrates the handoff explicitly.
- Frontend calls `run_active_modelling(...)`.
- Frontend then calls Backend/Data export preparation using returned `artifacts`, `failed_models`, and `missing_artifacts`.
- Backend/Data prepares the export manifest and marks the workflow ready for Review.
- This keeps the Review readiness gate visible to the UI.

## Failure And Retry Rules

Failures should first appear on the Modelling screen.

Initial failure categories:

| Category | Examples | User Path |
|---|---|---|
| Retryable in Modelling | CoinGecko timeout, temporary cache read/write issue, transient export preparation failure | Stay on Modelling screen and show retry action. |
| Return to Configuration | invalid constraints, unsupported model selection, too few/many assets, insufficient valid price history for required assets, no confirmed modelling plan | Show reason and return-to-configuration action. |
| Partial success | one or more models fail but at least one selected model succeeds | Allow Review with failed-model reasons carried into Review outputs. |
| Terminal no-output failure | all selected models fail during execution or all required artifacts fail to write | Stay on Modelling screen with return-to-configuration and retry only where useful. |

Insufficient price history should not offer one-click asset removal in V1. User should return to Configuration.

All-model failure rules:

- Offer `Retry` only for data/API/cache/export-related failures where retry may reasonably succeed.
- Otherwise offer `Return to Configure`.

## Review Readiness

The app can enter Review only after all required Review state is available.

Required:

- confirmed modelling plan Markdown
- final confirmed user inputs JSON
- model output artifacts for at least one successful model
- failed model details, if any model failed
- missing artifact descriptors, where optional artifacts could not be produced
- export manifest
- download-all bundle metadata, if available

The final gate should be artifact and manifest readiness.

If export preparation partially fails:

- Review may still open if model outputs exist.
- Individual missing downloads should be disabled with reasons.
- `Download All` failure should not block Review.
- Avoid cluttering the UI with download-failure warnings before the user asks to download.
- If `Download All` is known unavailable, the control may be disabled.
- If a failure is only discovered on click, show a concise pop-up/error message.

Review transition rule:

- User should always click `Review Results` to enter Review after modelling completes.
- If the page refreshes after Review is ready, the app should open directly in Review.

## Validation Checks

Open validation checklist to refine:

| Agent | Must Verify |
|---|---|
| Frontend Agent | Phase routing, button actions, progress rendering, Review display, download controls, and user-visible failure states. |
| Backend/Data Agent | Configuration validation issue codes, active session state transitions, price/cache callables, export manifest, individual downloads, and `Download All`. |
| Modelling Agent | `run_active_modelling(...)` return shape, progress event phases, successful model artifacts, partial failure shape, and missing artifact descriptors. |
| AI/Perplexity Agent | Configuration plan generation returns valid Markdown/metadata and Review chat receives the intended visible context. |
| Orchestrator Agent | Cross-agent contracts are consistent and no agent has taken ownership of another agent's folder or interface. |

Frontend Agent should run the first integrated smoke test while implementing. QA/Validation Agent should later formalize repeatable checks.
