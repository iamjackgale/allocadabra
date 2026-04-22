| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 21:45:53 BST |

# Session Storage Spec

## Purpose

Define how active user workflow state is stored locally and retrieved by the app.

## Storage Boundary

- All session storage is local to the app workspace.
- The app should not require a separate backend service for user input or model output persistence.
- The system supports one active workflow state at a time.
- The app does not keep recoverable history for previous modelling runs unless the user downloaded exports at the time.
- Session state is separate from CoinGecko market-data cache.
- V1 storage should live under `/storage/cache/user-inputs` and `/storage/cache/model-outputs`.

## Stored State Types

### Active User Inputs

Purpose:

- Store the single active set of user inputs for the current workflow.

Lifecycle:

- Starts on page load as empty/default state.
- Updates as soon as the user enters any parameter or selects any asset.
- Remains editable by the user throughout the preparation flow.
- Can be exported at the end of the process.
- Resets to empty/default state when the user chooses to refresh/start again at the end of the workflow.

Recovery:

- The app can recover only the current active input state.
- The app cannot recover inputs from previous model runs unless the user downloaded them.

Initial export format:

- User inputs should export as `.json`.

### AI-Generated Modelling Plan

Purpose:

- Store the Perplexity-generated natural-language modelling plan for the active workflow.

Lifecycle:

- Created during the modelling preparation phase.
- Available for user confirmation before model generation.
- Stored as part of the active workflow state.
- Can be exported at the end of the process.

Initial export format:

- AI modelling plan should export as `.md`.

### AI Chat Sessions

Purpose:

- Store active workflow AI messages for Configuration Mode and Review Mode.

Lifecycle:

- Configuration Mode chat starts during parameter setting.
- Configuration Mode chat persists through Configuration and Modelling.
- Configuration Mode chat is wiped immediately after Modelling succeeds and review artifacts are ready.
- Review Mode chat starts after model outputs exist.
- Review Mode receives the confirmed modelling plan from Configuration Mode.
- Review Mode does not receive the full Configuration Mode transcript by default.

Storage rules:

- Store Configuration Mode and Review Mode as separate sessions inside the single active workflow state.
- AI messages are recoverable only for the current active workflow.
- Chat transcripts are not exportable in V1.
- Previous AI conversations are unrecoverable.
- If Modelling fails and the user returns to Configuration, restore Configuration chat with prior configuration and plan state.
- If the app reloads after Review is ready, reopen in Review Mode rather than returning to Modelling or Configuration.
- Review Mode chat is wiped when the user starts a new model.

### Model Outputs

Purpose:

- Store generated model outputs for the final review/export stage.

Lifecycle:

- Created only after the user confirms scope and chooses to generate models.
- Accessible only at the final review stage.
- Not accessible throughout earlier workflow stages.
- Stored until the user explicitly clicks to start a new model.
- Cleared when the user starts a new model.
- If outputs and review artifacts are complete, the active workflow phase should be treated as Review even if the user has not clicked `Review Results`.
- If a modelling run is interrupted before outputs are complete, the app may show interrupted state and offer return to Configuration or restart.

Recovery:

- The app can recover only the current active model outputs.
- The app cannot recover outputs from previous model runs unless the user downloaded them.

Initial export formats:

- Model output tables should export as `.csv`.
- Model chart images should export as `.png`.
- Download bundles should include every generated artifact, including accepted modelling plan and user input JSON.
- No `.pdf` export is required.

Review UI state:

- V1 does not need to persist the currently open Review section or selected model.
- If Review is reloaded, default to summary metrics and the first model in run order.

## Clear/Reset Behaviour

- The app should not provide a general cache-clearing control.
- Local session storage persists until the user clears local storage/cache files outside the app.
- Workflow reset clears active user inputs and active model outputs.
- Workflow reset must not clear CoinGecko market-data cache.

## Relationship To Other Specs

- `/docs/specs/data-backend/data-storage.md` owns CoinGecko market-data cache rules.
- `/docs/specs/ai/parameters-agent.md` consumes and updates active user input context during preparation.
- `/docs/specs/ai/review-agent.md` consumes model outputs during final review.
- `/docs/specs/ai/ai-model-integration.md` defines Configuration Mode and Review Mode session rules.
- `/docs/specs/frontend/model-review.md` defines how final outputs are displayed and downloaded.

## Open Questions

- Exact local storage file format for active workflow state.
- Exact schema for user inputs, modelling plan metadata, and model output manifests.
- Exact export bundle structure for mixed `.json`, `.md`, `.csv`, and visual artifacts.
