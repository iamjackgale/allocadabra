| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-24 07:29:06 BST |

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

## V1 File Formats

V1 active workflow/session storage uses JSON files:

| Data | Format | Path |
|---|---|---|
| Active workflow state | JSON | `/storage/cache/user-inputs/active_workflow.json` |
| Current model-output manifest | JSON | `/storage/cache/model-outputs/manifest.json` |

JSON files must include a `schema_version` and `updated_at` field. Model-output artifacts may be referenced by the manifest. Export bundle construction, artifact paths, missing-artifact handling, and `Download All` behaviour are defined in `/docs/specs/app/export-bundling.md`.

### Active User Inputs

Purpose:

- Store the single active set of user inputs for the current workflow.

Lifecycle:

- Starts on page load as empty/default state.
- Updates as soon as the user enters any parameter or selects any asset.
- Remains editable by the user throughout the preparation flow.
- Can be exported at the end of the process.
- Resets to empty/default state when the user chooses to refresh/start again at the end of the workflow.
- Resets to empty/default state when the user confirms `Reset Configuration` or `Start New Model`.

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
- If Modelling fails or the user cancels during Modelling, restore Configuration chat and prior configuration options.
- Cancellation abandons the active generated plan, returns to the editable Configuration component rather than the modelling plan preview, and clears any partial model outputs.
- Confirmed `Reconfigure` abandons the active generated plan, returns to the editable Configuration component, preserves prior configuration options, and preserves Configuration chat.
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
- Cleared if the user cancels during Modelling before review artifacts are complete.
- If outputs and review artifacts are complete, the active workflow phase should be treated as Review even if the user has not clicked `Review Results`.
- If a modelling run is interrupted before outputs are complete, the app may show interrupted state and offer return to the editable Configuration screen or restart.
- If the user confirms `Return To Configure` from Review, clear current model outputs and Review chat, then return to the editable Configuration form with prior configuration options selected.
- If the user confirms `Start New Model`, clear active inputs, generated plan, Review chat, and model outputs, then return to the empty/default Configuration form.

Recovery:

- The app can recover only the current active model outputs.
- The app cannot recover outputs from previous model runs unless the user downloaded them.

Initial export formats:

- Model output tables should export as `.csv`.
- Model chart images should export as `.png`.
- Download bundles should follow `/docs/specs/app/export-bundling.md`.
- No `.pdf` export is required.

Review UI state:

- V1 does not need to persist the currently open Review section or selected model.
- If Review is reloaded, default to summary metrics and the first model in run order.

## Clear/Reset Behaviour

- The app should not provide a general cache-clearing control.
- Local session storage persists until the user clears local storage/cache files outside the app.
- Workflow reset clears active user inputs and active model outputs.
- Workflow reset must not clear CoinGecko market-data cache.

## Initial App Interfaces

Initial backend/data scaffolding exposes workflow-state helpers from `app.storage.data_api` and `app.storage.session_state`:

| Function | Purpose |
|---|---|
| `get_active_workflow()` | Return the current active workflow state, creating the default state if missing. |
| `update_active_inputs(updates)` | Merge user-input updates into the active workflow state. |
| `validate_active_configuration()` | Run deterministic validation against the current active user-input state. |
| `save_active_workflow(state)` | Persist an edited active workflow state. |
| `store_generated_plan(markdown, metadata=None)` | Store the generated, unconfirmed AI modelling plan. |
| `confirm_generated_plan()` | Mark the current generated modelling plan as confirmed. |
| `abandon_generated_plan()` | Return to editable Configuration while preserving selected inputs and Configuration chat. |
| `mark_modelling_started()` | Move the active workflow into Modelling and clear partial output manifests. |
| `mark_modelling_interrupted(error=None)` | Record interrupted Modelling and clear partial output manifests. |
| `prepare_review_export_bundle(modelling_artifacts=None, failed_models=None, missing_artifacts=None)` | Create export files, manifest, and Download All zip from stored workflow state and Modelling-produced artifact descriptors, then move the active workflow into Review. |
| `mark_review_ready(manifest)` | Store the current model-output/export manifest and move the active workflow into Review. |
| `get_review_export_manifest()` | Return the current export manifest for Review. |
| `get_review_download_all()` | Return Download All metadata for the Frontend. |
| `get_review_artifact_download(artifact_id)` | Return individual artifact download metadata for the Frontend. |
| `return_to_configure_from_review()` | Clear current outputs and Review chat while preserving prior configuration choices. |
| `reset_configuration()` / `start_new_model()` | Clear active inputs, plan, chats, and outputs without touching CoinGecko cache. |

Export bundle generation follows `/docs/specs/app/export-bundling.md`.

### Deterministic Validation Issue Shape

`validate_active_configuration()` returns the existing validation envelope:

```python
{
    "valid": bool,
    "issues": [
        {
            "field": str,
            "code": str,
            "message": str,
            "context": dict | None,
        }
    ],
}
```

`field` is a stable dotted app-state path for frontend mapping. `code` is the stable machine-readable issue type. `message` is user-facing copy and may be revised without changing frontend control mapping. `context` is optional structured metadata for the issue, such as `model_id`, `constraint_id`, `asset_id`, `min_value`, `max_value`, or `selected_asset_count`.

Task `092` extends deterministic validation to reject unsupported or duplicate model IDs and impossible V1 constraint combinations before AI plan generation or Modelling starts. Model and constraint issue codes follow `/docs/prompts/briefs/backend-data-validation-mini-spec-1.md`, including:

- `unsupported_model_id`
- `duplicate_model_ids`
- `constraints_invalid_type`
- `unknown_constraint_key`
- `constraint_percent_invalid`
- `constraint_asset_count_invalid`
- `constraint_asset_ids_invalid`
- `constraint_asset_id_not_selected`
- `constraint_min_greater_than_max`
- `global_min_allocation_sum_exceeds_100`
- `global_max_allocation_sum_below_100`
- `selected_asset_min_allocation_sum_exceeds_100`
- `selected_asset_max_allocation_sum_below_100`
- `min_assets_constraint_exceeds_selected_assets`
- `min_assets_constraint_greater_than_max_assets_constraint`

Frontend may emit `min_assets_in_portfolio=0` to mean unset. Backend/Data treats that as no minimum asset-count constraint. A `max_assets_in_portfolio` value greater than the current selected asset count is treated as a loose upper bound and does not block validation by itself; impossible asset-count validation is reserved for minimum counts that exceed the selected assets and min/max contradictions.

V1 constraint fields validated by Backend/Data are:

- `constraints.global_min_allocation_percent`
- `constraints.global_max_allocation_percent`
- `constraints.selected_asset_min_allocation.asset_ids`
- `constraints.selected_asset_min_allocation.percent`
- `constraints.selected_asset_max_allocation.asset_ids`
- `constraints.selected_asset_max_allocation.percent`
- `constraints.min_assets_in_portfolio`
- `constraints.max_assets_in_portfolio`

## Relationship To Other Specs

- `/docs/specs/data-backend/data-storage.md` owns CoinGecko market-data cache rules.
- `/docs/specs/app/export-bundling.md` defines export bundle structure, artifact manifest shape, missing-artifact handling, individual download behaviour, and `Download All` rules.
- `/docs/specs/ai/parameters-agent.md` consumes and updates active user input context during preparation.
- `/docs/specs/ai/review-agent.md` consumes model outputs during final review.
- `/docs/specs/ai/ai-model-integration.md` defines Configuration Mode and Review Mode session rules.
- `/docs/specs/frontend/model-review.md` defines how final outputs are displayed and downloaded.
