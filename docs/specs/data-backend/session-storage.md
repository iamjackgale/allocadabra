created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 09:30:05 BST

# Session Storage Spec

## Purpose

Define how active user workflow state is stored in the browser and retrieved by the app.

## Storage Boundary

- All session storage is local to the user's browser.
- The app should not require a separate backend service for user input or model output persistence.
- The system supports one active workflow state at a time.
- The app does not keep recoverable history for previous modelling runs unless the user downloaded exports at the time.
- Session state is separate from CoinGecko market-data cache.

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

### Model Outputs

Purpose:

- Store generated model outputs for the final review/export stage.

Lifecycle:

- Created only after the user confirms scope and chooses to generate models.
- Accessible only at the final review stage.
- Not accessible throughout earlier workflow stages.
- Stored until the user explicitly clicks to start a new model.
- Cleared when the user starts a new model.

Recovery:

- The app can recover only the current active model outputs.
- The app cannot recover outputs from previous model runs unless the user downloaded them.

Initial export formats:

- Model output tables should export as `.csv`.
- Other model visualisations or artifacts may be added later.
- No `.pdf` export is required.

## Clear/Reset Behaviour

- The app should not provide a general cache-clearing control.
- Browser storage persists until the user clears browser cache/storage outside the app.
- Workflow reset clears active user inputs and active model outputs.
- Workflow reset must not clear CoinGecko market-data cache.

## Relationship To Other Specs

- `/docs/specs/data-backend/data-storage.md` owns CoinGecko market-data cache rules.
- `/docs/specs/ai/parameters-agent.md` consumes and updates active user input context during preparation.
- `/docs/specs/ai/review-agent.md` consumes model outputs during final review.
- `/docs/specs/frontend/model-review.md` defines how final outputs are displayed and downloaded.

## Open Questions

- Exact browser storage technology for active workflow state.
- Exact schema for user inputs, modelling plan metadata, and model output manifests.
- Exact export bundle structure for mixed `.json`, `.md`, `.csv`, and visual artifacts.
