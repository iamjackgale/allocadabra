| Metadata | Value |
|---|---|
| created | 2026-04-24 07:15:35 BST |
| last_updated | 2026-04-24 07:15:35 BST |
| source_agent | Frontend Agent |
| requested_owner | Backend/Data Agent |

# Backend/Data Mini Spec: Frontend Validation Integration 2

## Purpose

Confirm the Backend/Data validation work still needed after the first frontend implementation pass, with enough context for task `092` to land cleanly against the current UI.

This mini spec complements `/docs/prompts/briefs/backend-data-validation-mini-spec-1.md`; it does not replace it.

## Requested Owner

- Backend/Data Agent.

## Target Folders/Files

- `/app/storage/validation.py`
- `/app/storage/data_api.py`, only if the return envelope needs documentation or helper updates.
- `/docs/specs/data-backend/session-storage.md`, only if the validation interface documentation needs to be updated.
- Optional validation docs or smoke tests under `/docs/validation/backend-validation.md` once implementation lands.

## Current Frontend State

The frontend now emits configuration inputs in the shape expected by the previous Backend/Data validation mini spec:

```python
{
    "selected_assets": [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    ],
    "treasury_objective": "Stable performance",
    "risk_appetite": "Medium",
    "selected_models": ["mean_variance", "risk_parity"],
    "constraints": {
        "global_min_allocation_percent": 0,
        "global_max_allocation_percent": 100,
        "selected_asset_min_allocation": {
            "asset_ids": ["bitcoin"],
            "percent": 10,
        } | None,
        "selected_asset_max_allocation": {
            "asset_ids": ["bitcoin"],
            "percent": 50,
        } | None,
        "min_assets_in_portfolio": 0,
        "max_assets_in_portfolio": 3,
    },
}
```

The frontend consumes validation results only through the current app-layer callable:

```python
from app.storage.data_api import validate_active_configuration
```

Expected return envelope remains:

```python
{
    "valid": bool,
    "issues": [
        {
            "field": str,
            "code": str,
            "message": str,
        }
    ],
}
```

## Problem

The frontend is ready to map stable `field` and `code` values to inline control groups and chat feedback, but the current Backend/Data validation coverage is still too coarse for:

- unsupported model IDs.
- duplicate model IDs.
- malformed constraint objects.
- unknown constraint keys.
- selected-asset constraint IDs that are not selected assets.
- impossible allocation combinations.
- impossible portfolio asset-count constraints.

Until task `092` lands, users may only see broad validation messages and some invalid constraint combinations may reach AI plan generation or modelling later than intended.

## Required Backend/Data Behavior

Implement the contract from `/docs/prompts/briefs/backend-data-validation-mini-spec-1.md`, with these frontend-specific confirmations:

- Validate `selected_models` as stable IDs, not display labels.
- Reject unsupported IDs using `field="selected_models"` and `code="unsupported_model_id"`.
- Reject duplicate IDs using `field="selected_models"` and `code="duplicate_model_ids"`.
- Validate `constraints` as an object when present.
- Reject unknown constraint keys instead of ignoring them.
- Validate percent values in the closed range `0..100`.
- Validate asset-count constraints as integers within selected-asset bounds.
- Validate selected-asset constraint `asset_ids` as a non-empty list of selected asset IDs when that nested constraint is present.
- Return all issues found in one pass.
- Preserve the existing return envelope so the frontend does not need a new integration surface.

## Required Stable Fields

Backend/Data should use the field paths already proposed in mini spec 1:

| Concern | Field |
|---|---|
| Selected models list | `selected_models` |
| Global minimum allocation | `constraints.global_min_allocation_percent` |
| Global maximum allocation | `constraints.global_max_allocation_percent` |
| Selected-asset minimum allocation asset list | `constraints.selected_asset_min_allocation.asset_ids` |
| Selected-asset minimum allocation percent | `constraints.selected_asset_min_allocation.percent` |
| Selected-asset maximum allocation asset list | `constraints.selected_asset_max_allocation.asset_ids` |
| Selected-asset maximum allocation percent | `constraints.selected_asset_max_allocation.percent` |
| Minimum assets in portfolio | `constraints.min_assets_in_portfolio` |
| Maximum assets in portfolio | `constraints.max_assets_in_portfolio` |
| Whole constraints object | `constraints` |

## Required Stable Codes

Backend/Data should implement the issue codes already proposed in mini spec 1. The frontend is prepared to consume them without parsing message text.

Priority codes for the current UI:

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
- `max_assets_constraint_exceeds_selected_assets`
- `min_assets_constraint_greater_than_max_assets_constraint`

## Validation Examples Backend/Data Should Add

The Backend/Data Agent should add smoke checks or tests for:

- `selected_models=["mean_variance", "not_a_model"]` returns `unsupported_model_id`.
- `selected_models=["mean_variance", "mean_variance"]` returns `duplicate_model_ids`.
- `constraints=[]` returns `constraints_invalid_type`.
- `constraints={"unsupported": 1}` returns `unknown_constraint_key`.
- six selected assets with `global_min_allocation_percent=20` returns `global_min_allocation_sum_exceeds_100`.
- three selected assets with `global_max_allocation_percent=30` returns `global_max_allocation_sum_below_100`.
- selected-asset allocation references an unselected asset ID and returns `constraint_asset_id_not_selected`.
- `min_assets_in_portfolio > max_assets_in_portfolio` returns `min_assets_constraint_greater_than_max_assets_constraint`.

## Frontend Impact

No frontend API change is required if the existing return envelope is preserved.

Once task `092` lands, the Frontend Agent or QA/Validation Agent should verify:

- Configuration chat feedback lists the stronger deterministic issues.
- Constraint fields no longer allow impossible setups to proceed to AI plan generation.
- Unsupported/future model IDs in corrupted or restored state are blocked before modelling.

## Risks / Dependencies

- The frontend currently sends default zero/maximum values for some optional constraints. Backend/Data should treat neutral values as valid no-op constraints unless the nested selected-asset constraint object is present and non-null.
- Backend/Data should not require optional selected-asset min/max nested constraints unless the frontend sends the nested object.
- Backend/Data should keep user-facing messages concise because the frontend will surface them in chat feedback and possibly near controls.

## Recommended Next Step

Backend/Data should implement task `092` directly in `/app/storage/validation.py`, keep `app.storage.data_api.validate_active_configuration()` unchanged, and add validation smoke coverage to the backend validation handoff.

