| Metadata | Value |
|---|---|
| created | 2026-04-23 19:54:01 BST |
| last_updated | 2026-04-23 19:54:01 BST |
| prompt_used | |

# Frontend Mini Spec: Modelling Run Contract 1

This brief gives the Frontend Agent the current Modelling-owned app-layer contract to build against.

Read alongside:

- `/docs/specs/data-backend/riskfolio-lib.md`
- `/docs/specs/data-backend/session-storage.md`
- `/docs/specs/app/export-bundling.md`
- `/docs/validation/modelling-validation.md`

## Source Of Truth

The current callable surface is implemented in:

- `/app/processing/data_api.py`
- `/app/processing/progress.py`

Public import:

```python
from app.processing import modelling_contract, run_active_modelling
```

## Primary Callable

```python
run_active_modelling(
    *,
    progress_callback: ProgressCallback | None = None,
    force_refresh_prices: bool = False,
    output_dir: Path = MODEL_OUTPUTS_DIR,
) -> dict[str, Any]
```

Purpose:

- Read active workflow inputs from Backend/Data callables.
- Validate configuration and confirmed modelling-plan state.
- Load cached price histories through Backend/Data callables.
- Run dataset preparation, model execution, metrics, and artifact generation.
- Return a frontend-safe result.

Non-goals:

- Does **not** create zip bundles.
- Does **not** write the final Review export manifest.
- Does **not** transition the workflow into Review.

Backend/Data still owns:

- `prepare_review_export_bundle(...)`
- final manifest storage
- individual download metadata
- `Download All` bundle creation

## Progress Events

The callable accepts an optional callback and also returns the emitted event list in `progress_events`.

Event shape:

```text
phase: "validation" | "ingestion" | "datasets" | "modelling" | "analysis" | "outputs"
status: "started" | "completed" | "failed" | "info"
message: string
created_at: ISO timestamp
```

Frontend expectation:

- Use these as the Modelling screen checkpoint source.
- Show one current micro-log message at a time.
- Do not assume percentage progress.
- A phase may emit both `started` and `completed`.
- Failure can occur before `outputs`.

## Result Shape

`run_active_modelling(...)` currently returns:

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

### Meaning

- `ok=True`: at least one selected model succeeded.
- `successful_models`: stable model IDs:
  - `mean_variance`
  - `risk_parity`
  - `hierarchical_risk_parity`
- `failed_models`: per-model failures suitable for Review and partial-success states.
- `artifacts`: modelling-owned artifact descriptors that Backend/Data can package and Frontend can display.
- `missing_artifacts`: optional artifacts that were not computable; reason is explicit.
- `errors`: run-level validation/ingestion/runtime errors.
- `user_message`: concise display copy for the current outcome.
- `dataset_metadata`: useful for debug/detail panels, not required for first-pass UI.
- `output_dir`: local artifact directory, mainly for backend/export handoff.

## Partial Failures

Supported state:

- Some selected models succeed.
- Some selected models fail.
- `ok=True` in this case.

Frontend expectation:

- Proceed to Review if Backend/Data export preparation succeeds.
- Show successful model outputs normally.
- Show failed models in red or warning treatment with the provided failure reason.
- Do not block Review just because one model failed.

`failed_models` shape:

```text
model_id: string
label: string
stage: string
reason: string
exception_type: string
```

## Run-Level Errors

These live in `errors`, distinct from per-model failures.

Examples already emitted:

- `invalid_configuration`
- `unsupported_models`
- `modelling_plan_not_confirmed`
- `price_history_unavailable`
- `dataset_build_failed`
- `model_execution_failed`
- `modelling_failed`

Common fields:

```text
code: string
message: string
field: string | null
id: string | null
model_ids: list[str] | null
exception_type: string | null
```

## Retryable Errors

For Frontend purposes, treat these as retryable by default:

- `price_history_unavailable`
- `dataset_build_failed`
- `model_execution_failed`
- `modelling_failed`

Treat these as configuration-fix-required, not immediate retry:

- `invalid_configuration`
- `unsupported_models`
- `modelling_plan_not_confirmed`

This is a UI handling rule for now; there is not yet a separate `retryable: bool` field in the contract.

## Review Summaries

There is not currently a separate `review_summaries` top-level field.

Frontend should derive the initial review summary view from artifacts:

- `output_type="summary_metrics"` for side-by-side comparison
- `failed_models` for warning/failure panels
- `successful_models` to determine which model sections to render

If a dedicated summary payload becomes necessary later, request it as a follow-up contract change rather than inferring new backend fields ad hoc.

## Artifact Descriptors

`artifacts` and `missing_artifacts` use manifest-style entries aligned with `/docs/specs/app/export-bundling.md`.

Core fields:

```text
artifact_id: string
label: string
category: "general" | "model" | "manifest" | "missing" | "failure"
model_id: string | null
output_type: string
format: "json" | "md" | "csv" | "png" | "txt"
path: string | null
status: "available" | "missing" | "failed" | "disabled"
reason: string | null
included_in_download_all: bool
individual_download_enabled: bool
```

Frontend expectation:

- Use `output_type` and `model_id` to map artifacts to panels/sections.
- For chart sections, prefer the `.png` artifact as the visible download target when present.
- Keep the underlying `.csv` available to Backend/Data for `Download All`.
- Use `missing_artifacts` or `status != "available"` plus `reason` to disable controls with explicit explanations.

## Current Frontend Mapping Guidance

Suggested first-pass mapping:

- Summary metrics panel:
  - `category="general"`
  - `output_type="summary_metrics"`
- Canonical modelling dataset section:
  - `output_type="canonical_modelling_dataset"`
- Per-model sections by `model_id`:
  - `allocation_weights`
  - `allocation_over_time`
  - `cumulative_performance`
  - `drawdown`
  - `rolling_volatility`
  - optional:
    - `risk_contribution`
    - `efficient_frontier`
    - `dendrogram`

## Validation Already Run

Confirmed in `/docs/validation/modelling-validation.md`:

- processing runtime import check: passed
- storage export import check: passed
- active modelling smoke test: passed
- unsupported model smoke test: passed

## Frontend Boundary Notes

- Do not assume Backend/Data has already packaged exports when Modelling returns.
- Expect Frontend to call Backend/Data export preparation after a successful or partial-success modelling run.
- Do not invent new model IDs or artifact types.
- If the UI needs a field not present in this contract, request a new Modelling mini spec rather than reading internal storage files directly.
