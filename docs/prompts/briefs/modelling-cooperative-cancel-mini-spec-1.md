| Metadata | Value |
|---|---|
| created | 2026-04-24 07:15:35 BST |
| last_updated | 2026-04-24 07:15:35 BST |
| source_agent | Frontend Agent |
| requested_owner | Modelling Agent |
| dependency_owner | Backend/Data Agent, only if cancellation state is persisted |

# Modelling Mini Spec: Cooperative Cancellation 1

## Purpose

Define the missing cooperative cancellation contract needed for the Frontend `Cancel` action during active Modelling.

The first frontend implementation can abandon the workflow/UI and ignore in-flight results, but the current modelling callable does not expose a stop signal. As a result, the underlying modelling thread may continue to fetch prices, build datasets, run solvers, or write temporary artifacts after the user has cancelled.

## Requested Owner

- Primary owner: Modelling Agent.
- Secondary owner: Backend/Data Agent only if the chosen design persists cancellation state in active workflow/session storage.

## Target Folders/Files

Likely Modelling-owned files:

- `/app/processing/data_api.py`
- `/app/processing/runner.py`
- `/app/processing/progress.py`
- `/docs/prompts/briefs/frontend-agent-modelling-contract-1.md`, or a follow-up modelling contract brief.
- `/docs/validation/modelling-validation.md`

Potential Backend/Data files only if needed:

- `/app/storage/session_state.py`
- `/app/storage/data_api.py`
- `/docs/specs/data-backend/session-storage.md`

## Current Contract

The current frontend-callable modelling surface is:

```python
run_active_modelling(
    *,
    progress_callback: ProgressCallback | None = None,
    force_refresh_prices: bool = False,
    output_dir: Path = MODEL_OUTPUTS_DIR,
) -> dict[str, Any]
```

The current result shape includes:

```text
ok: bool
successful_models: list[str]
failed_models: list[dict]
artifacts: list[dict]
missing_artifacts: list[dict]
errors: list[dict]
user_message: str
progress_events: list[dict]
dataset_metadata: dict
output_dir: str | null
```

## Problem

Streamlit cannot forcibly and safely kill a running Python thread. A spec-compliant `Cancel` button needs cooperative checks inside the modelling run.

Without cooperative cancellation:

- UI state can return to Configuration.
- The generated plan can be abandoned.
- Partial outputs can be ignored or deleted after the run ends.
- The compute/network work itself may continue until `run_active_modelling(...)` returns.

This does not fully satisfy the Modelling page spec language: `Cancel abandons the active run and generated plan, deletes partial model outputs, keeps cached market data unchanged, and returns to Configuration with previous options selected.`

## Proposed Contract Change

Add an optional cancellation callback to the active modelling callable:

```python
CancelCheck = Callable[[], bool]

run_active_modelling(
    *,
    progress_callback: ProgressCallback | None = None,
    cancel_check: CancelCheck | None = None,
    force_refresh_prices: bool = False,
    output_dir: Path = MODEL_OUTPUTS_DIR,
) -> dict[str, Any]
```

Behavior:

- `cancel_check` returns `True` when the run should stop.
- The modelling layer checks `cancel_check` between each major phase and before/after each model execution.
- The modelling layer should also check before writing final artifact descriptors and before returning success.
- If cancellation is requested, return a normal frontend-safe result instead of raising an uncaught exception.

## Proposed Cancelled Result Shape

When cancelled, return:

```python
{
    "ok": False,
    "cancelled": True,
    "successful_models": [],
    "failed_models": [],
    "artifacts": [],
    "missing_artifacts": [],
    "errors": [
        {
            "code": "modelling_cancelled",
            "message": "The modelling run was cancelled.",
        }
    ],
    "user_message": "The modelling run was cancelled.",
    "progress_events": [...],
    "dataset_metadata": {},
    "output_dir": str | None,
}
```

Notes:

- `cancelled` is new and optional; absent or `False` means existing behavior.
- `code="modelling_cancelled"` should not be treated as retryable failure copy.
- Frontend will not call `prepare_review_export_bundle(...)` for cancelled runs.

## Progress Events

On cancellation, emit:

```python
{
    "phase": current_phase,
    "status": "failed",
    "message": "Modelling was cancelled.",
    "created_at": "...",
}
```

Optional but useful:

- Add `status="cancelled"` to `ProgressStatus` if the Modelling Agent wants a distinct state. If added, update the frontend mini contract and validation docs. If not, use `status="failed"` with `code="modelling_cancelled"` in the final result.

## Required Checkpoints

The Modelling Agent should check cancellation:

- after deterministic validation completes.
- before price-history loading starts.
- after price-history loading completes.
- before dataset building starts.
- after dataset building completes.
- before each selected model starts.
- after each selected model finishes.
- before analysis artifacts are written.
- before output finalization.

This is sufficient for V1. It does not need to interrupt a solver call mid-solve.

## Artifact And Storage Rules

On cancellation:

- Do not prepare Review export bundles.
- Do not mark workflow as Review.
- Do not include cancelled partial artifacts in final manifest.
- Best effort: delete model-owned temporary output directory if the frontend passes a temp `output_dir`.
- Keep CoinGecko market-data cache unchanged.
- Preserve previous configuration options.
- Abandon the generated plan according to existing Frontend/Backend lifecycle behavior.

## Frontend Impact

Frontend can then:

- Pass a session-state-backed `cancel_check` into `run_active_modelling(...)`.
- Stop showing the active run once cancellation is acknowledged.
- Avoid showing a generic failed-modelling state for user-requested cancellation.
- Keep current UI copy and confirmation behavior unchanged.

## Backend/Data Impact

No Backend/Data change is required if cancellation state remains frontend-local during the active Streamlit session.

Backend/Data change may be useful if the team wants durable cancellation state across refresh:

- Add a workflow `modelling_run.status="cancel_requested"` state.
- Add a frontend-callable helper such as `mark_modelling_cancel_requested()`.
- Ensure `mark_modelling_interrupted(...)`, `abandon_generated_plan()`, and `clear_model_outputs()` keep current cache-preservation rules.

This is optional for V1; the most important missing capability is the Modelling-owned `cancel_check`.

## Validation Expectations

Add modelling smoke checks for:

- `cancel_check` returns `True` before ingestion; result has `cancelled=True` and no artifacts.
- `cancel_check` returns `True` before the second selected model; result has `cancelled=True` and no Review-ready output handoff.
- Cancellation emits a progress event with user-facing cancellation copy.
- Cancelled run does not call Backend/Data export preparation.
- Cancelled run does not clear CoinGecko market cache.

## Risks / Dependencies

- A solver call may still run to completion before cancellation is observed. That is acceptable for V1 if cancellation checks happen before and after each model.
- The frontend uses a background thread for responsiveness. The Modelling Agent should avoid requiring Streamlit APIs inside the modelling callable.
- If cancellation becomes persisted in Backend/Data storage, the agents must avoid race conditions where a cancelled run later marks Review ready.

## Recommended Next Step

The Modelling Agent should extend `run_active_modelling(...)` with `cancel_check`, add cancellation checks at phase boundaries and model boundaries, return a `modelling_cancelled` result shape, and document the updated contract in the modelling validation handoff.

