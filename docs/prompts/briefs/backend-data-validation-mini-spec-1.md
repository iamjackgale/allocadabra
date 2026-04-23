| Metadata | Value |
|---|---|
| created | 2026-04-23 19:58:43 BST |
| last_updated | 2026-04-23 19:58:43 BST |
| author | Backend/Data Agent |
| requested_by | User / Frontend handoff |

# Backend/Data Validation Mini Spec 1

## Purpose

Provide the Frontend Agent with a concrete Backend/Data validation contract for the next deterministic validation expansion:

- unsupported model IDs
- constraint feasibility
- stable field-specific issue codes

This mini spec is a Backend/Data-owned change proposal. It does not change Frontend-owned files directly.

## Requested Owner

- Backend/Data Agent

## Target Folders/Files

- `/app/storage/validation.py`
- `/app/storage/data_api.py`
- `/docs/specs/data-backend/session-storage.md` for interface documentation if needed

Frontend should consume the resulting issue codes but should not own the validation logic.

## Reason

The current deterministic validation only checks asset count, duplicate assets, treasury objective, risk appetite, and model count. It does not yet:

- reject unsupported model IDs with stable issue codes
- validate constraint shape and type
- catch clearly impossible constraint combinations before any AI call

The frontend configuration flow needs stable issue codes and field paths so it can map backend validation results to specific controls and user-facing messages.

## Proposed Input Contract

Backend deterministic validation should continue to validate `inputs: dict[str, Any]` and treat `constraints` as an optional nested object with this V1 shape:

```python
constraints = {
    "global_min_allocation_percent": float | int | None,
    "global_max_allocation_percent": float | int | None,
    "selected_asset_min_allocation": {
        "asset_ids": list[str],
        "percent": float | int | None,
    } | None,
    "selected_asset_max_allocation": {
        "asset_ids": list[str],
        "percent": float | int | None,
    } | None,
    "min_assets_in_portfolio": int | None,
    "max_assets_in_portfolio": int | None,
}
```

Notes:

- Percent values are user-entered percentages in the closed range `0..100`.
- `asset_ids` must refer to currently selected assets only.
- Missing `constraints` means no constraints.
- Unknown constraint keys should be rejected, not ignored silently.

## Supported Model Contract

Deterministic validation should validate `selected_models` as stable app IDs, not display labels.

Initial supported V1 IDs:

- `mean_variance`
- `risk_parity`
- `hierarchical_risk_parity`

Validation should reject any unsupported ID even if the count is otherwise valid.

## Stable Field Paths

Backend validation issues should use these `field` values so Frontend can bind them predictably:

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

## Stable Issue Codes

### Model IDs

| Code | Field | Trigger |
|---|---|---|
| `too_few_models` | `selected_models` | No selected models. |
| `too_many_models` | `selected_models` | More than 3 selected models. |
| `duplicate_model_ids` | `selected_models` | Same model ID appears more than once. |
| `unsupported_model_id` | `selected_models` | Any selected model ID is outside the V1 supported set. |

### Constraint Shape / Type

| Code | Field | Trigger |
|---|---|---|
| `constraints_invalid_type` | `constraints` | `constraints` is present but not an object/dict. |
| `unknown_constraint_key` | `constraints` | Unrecognized key is present in `constraints`. |
| `constraint_percent_invalid` | field-specific | Percent value is missing, non-numeric, or outside `0..100`. |
| `constraint_asset_count_invalid` | field-specific | Asset-count constraint is missing, non-integer, or outside valid bounds. |
| `constraint_asset_ids_invalid` | field-specific | Asset ID list is missing, empty when required, duplicated, or not a list of strings. |
| `constraint_asset_id_not_selected` | field-specific | Constraint references an asset ID not present in `selected_assets`. |

### Constraint Relationships / Feasibility

| Code | Field | Trigger |
|---|---|---|
| `constraint_min_greater_than_max` | field-specific | A minimum constraint exceeds the corresponding maximum constraint. |
| `global_min_allocation_sum_exceeds_100` | `constraints.global_min_allocation_percent` | `global_min_allocation_percent * selected_asset_count > 100`. |
| `global_max_allocation_sum_below_100` | `constraints.global_max_allocation_percent` | `global_max_allocation_percent * selected_asset_count < 100`. |
| `selected_asset_min_allocation_sum_exceeds_100` | `constraints.selected_asset_min_allocation.percent` | `percent * constrained_asset_count > 100`. |
| `selected_asset_max_allocation_sum_below_100` | `constraints.selected_asset_max_allocation.percent` | Only when the constrained asset list covers all selected assets and `percent * constrained_asset_count < 100`. |
| `min_assets_constraint_exceeds_selected_assets` | `constraints.min_assets_in_portfolio` | Minimum portfolio asset count is greater than the number of selected assets. |
| `max_assets_constraint_exceeds_selected_assets` | `constraints.max_assets_in_portfolio` | Maximum portfolio asset count is greater than the number of selected assets. |
| `min_assets_constraint_greater_than_max_assets_constraint` | `constraints.min_assets_in_portfolio` | Minimum portfolio asset count is greater than maximum portfolio asset count. |

## Validation Rules

Backend/Data should add these deterministic rules:

1. Validate model IDs before AI plan generation.
2. Reject duplicate model IDs separately from unsupported IDs.
3. Validate `constraints` type before inspecting nested fields.
4. Validate all known percentage constraints within `0..100`.
5. Validate all asset-count constraints as integers.
6. Validate selected-asset constraint `asset_ids` against currently selected asset IDs.
7. Catch the two explicitly required impossible examples from the frontend spec:
   - minimum allocation of `20%` across `6` assets
   - maximum allocation of `30%` across only `3` assets
8. Return all deterministic issues found in one pass rather than stopping at the first failure.

## Frontend Impact

Frontend should assume:

- `validate_active_configuration()` may now return more than one issue for `selected_models` and `constraints`.
- `field` values are stable dotted paths, suitable for mapping to inline control states or grouped chat explanations.
- `code` values are the contract for behavior; `message` is user-facing copy and may evolve.

Frontend should not hard-code natural-language parsing of `message` strings.

## Data/API Impact

No new endpoint is required. This is an expansion of the existing deterministic validation result:

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

## Risks / Dependencies

- The frontend constraint form should emit stable model IDs, not display labels.
- If Frontend or AI currently writes a different `constraints` shape into active state, Backend/Data should align to this mini spec before adding the new rules.
- Modelling does not need to change for this mini spec; this work is pre-AI, pre-run validation only.

## Recommended Next Step

Backend/Data can implement this immediately inside `/app/storage/validation.py` and expose the unchanged return envelope through `/app/storage/data_api.py`.
