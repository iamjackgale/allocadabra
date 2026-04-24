"""Deterministic backend validation for configuration inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MIN_ASSETS = 2
MAX_ASSETS = 10
MIN_MODELS = 1
MAX_MODELS = 3

SUPPORTED_MODEL_IDS = {
    "mean_variance",
    "risk_parity",
    "hierarchical_risk_parity",
}

CONSTRAINT_KEYS = {
    "global_min_allocation_percent",
    "global_max_allocation_percent",
    "selected_asset_min_allocation",
    "selected_asset_max_allocation",
    "min_assets_in_portfolio",
    "max_assets_in_portfolio",
}

SELECTED_ASSET_CONSTRAINT_KEYS = {"asset_ids", "percent"}

TREASURY_OBJECTIVES = {
    "Maximize return",
    "Stable performance",
    "Best risk-adjusted returns",
    "Reduce drawdowns",
    "Diversify exposure",
}

RISK_APPETITES = {
    "Very low",
    "Low",
    "Medium",
    "High",
    "Very high",
}


@dataclass(frozen=True)
class ValidationIssue:
    """User-facing deterministic validation issue."""

    field: str
    code: str
    message: str
    context: dict[str, Any] | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Validation result consumed by frontend and AI layers."""

    valid: bool
    issues: list[ValidationIssue]


def validate_configuration_inputs(inputs: dict[str, Any]) -> ValidationResult:
    """Validate active user inputs before plan generation or modelling."""
    issues: list[ValidationIssue] = []

    assets = inputs.get("selected_assets", [])
    if not isinstance(assets, list):
        assets = []

    if len(assets) < MIN_ASSETS:
        issues.append(
            ValidationIssue(
                field="selected_assets",
                code="too_few_assets",
                message="Select at least 2 assets before generating a modelling plan.",
            )
        )
    if len(assets) > MAX_ASSETS:
        issues.append(
            ValidationIssue(
                field="selected_assets",
                code="too_many_assets",
                message="Select no more than 10 assets for a modelling run.",
            )
        )

    asset_ids = [_asset_id(asset) for asset in assets]
    duplicate_ids = {asset_id for asset_id in asset_ids if asset_ids.count(asset_id) > 1}
    if duplicate_ids:
        issues.append(
            ValidationIssue(
                field="selected_assets",
                code="duplicate_assets",
                message="Remove duplicate assets before generating a modelling plan.",
            )
        )

    objective = inputs.get("treasury_objective")
    if objective not in TREASURY_OBJECTIVES:
        issues.append(
            ValidationIssue(
                field="treasury_objective",
                code="invalid_treasury_objective",
                message="Choose one supported treasury objective.",
            )
        )

    risk_appetite = inputs.get("risk_appetite")
    if risk_appetite not in RISK_APPETITES:
        issues.append(
            ValidationIssue(
                field="risk_appetite",
                code="invalid_risk_appetite",
                message="Choose one supported risk appetite.",
            )
        )

    selected_models = inputs.get("selected_models", [])
    if not isinstance(selected_models, list):
        issues.append(
            ValidationIssue(
                field="selected_models",
                code="invalid_model_selection",
                message="Choose supported models from the model selector.",
            )
        )
        selected_models = []

    if len(selected_models) < MIN_MODELS:
        issues.append(
            ValidationIssue(
                field="selected_models",
                code="too_few_models",
                message="Choose at least 1 supported model.",
            )
        )
    if len(selected_models) > MAX_MODELS:
        issues.append(
            ValidationIssue(
                field="selected_models",
                code="too_many_models",
                message="Choose no more than 3 models for comparison.",
            )
        )

    _validate_selected_models(selected_models, issues)
    _validate_constraints(inputs.get("constraints"), asset_ids, issues)

    return ValidationResult(valid=not issues, issues=issues)


def _asset_id(asset: Any) -> str:
    if isinstance(asset, dict):
        return str(asset.get("id", "")).strip()
    return str(asset).strip()


def _validate_selected_models(
    selected_models: list[Any],
    issues: list[ValidationIssue],
) -> None:
    model_ids: list[str] = []
    for index, model in enumerate(selected_models):
        if not isinstance(model, str) or not model.strip():
            issues.append(
                ValidationIssue(
                    field="selected_models",
                    code="invalid_model_selection",
                    message="Choose supported models from the model selector.",
                    context={"index": index},
                )
            )
            continue

        model_id = model.strip()
        model_ids.append(model_id)
        if model_id not in SUPPORTED_MODEL_IDS:
            issues.append(
                ValidationIssue(
                    field="selected_models",
                    code="unsupported_model_id",
                    message="Choose only supported V1 models.",
                    context={"model_id": model_id},
                )
            )

    seen: set[str] = set()
    for model_id in model_ids:
        if model_id in seen:
            issues.append(
                ValidationIssue(
                    field="selected_models",
                    code="duplicate_model_ids",
                    message="Choose each model only once.",
                    context={"model_id": model_id},
                )
            )
        seen.add(model_id)


def _validate_constraints(
    constraints: Any,
    selected_asset_ids: list[str],
    issues: list[ValidationIssue],
) -> None:
    if constraints in (None, {}):
        return
    if not isinstance(constraints, dict):
        issues.append(
            ValidationIssue(
                field="constraints",
                code="constraints_invalid_type",
                message="Use the supported constraint controls only.",
                context={"constraint_id": "constraints"},
            )
        )
        return

    for key in constraints:
        if key not in CONSTRAINT_KEYS:
            issues.append(
                ValidationIssue(
                    field="constraints",
                    code="unknown_constraint_key",
                    message="Use the supported constraint controls only.",
                    context={"constraint_id": key},
                )
            )

    selected_asset_count = len([asset_id for asset_id in selected_asset_ids if asset_id])
    selected_asset_set = {asset_id for asset_id in selected_asset_ids if asset_id}

    global_min = _optional_percent(
        constraints.get("global_min_allocation_percent"),
        field="constraints.global_min_allocation_percent",
        constraint_id="global_min_allocation_percent",
        issues=issues,
    )
    global_max = _optional_percent(
        constraints.get("global_max_allocation_percent"),
        field="constraints.global_max_allocation_percent",
        constraint_id="global_max_allocation_percent",
        issues=issues,
    )

    if global_min is not None and global_max is not None and global_min > global_max:
        issues.append(
            ValidationIssue(
                field="constraints.global_min_allocation_percent",
                code="constraint_min_greater_than_max",
                message="Minimum allocation cannot be greater than maximum allocation.",
                context={
                    "constraint_id": "global_allocation_percent",
                    "min_value": global_min,
                    "max_value": global_max,
                },
            )
        )

    if selected_asset_count > 0:
        if global_min is not None and global_min * selected_asset_count > 100:
            issues.append(
                ValidationIssue(
                    field="constraints.global_min_allocation_percent",
                    code="global_min_allocation_sum_exceeds_100",
                    message="The minimum allocation across selected assets exceeds 100%.",
                    context={
                        "constraint_id": "global_min_allocation_percent",
                        "min_value": global_min,
                        "selected_asset_count": selected_asset_count,
                    },
                )
            )
        if global_max is not None and global_max * selected_asset_count < 100:
            issues.append(
                ValidationIssue(
                    field="constraints.global_max_allocation_percent",
                    code="global_max_allocation_sum_below_100",
                    message="The maximum allocation across selected assets is below 100%.",
                    context={
                        "constraint_id": "global_max_allocation_percent",
                        "max_value": global_max,
                        "selected_asset_count": selected_asset_count,
                    },
                )
            )

    selected_min = _selected_asset_constraint(
        constraints.get("selected_asset_min_allocation"),
        constraint_id="selected_asset_min_allocation",
        field_prefix="constraints.selected_asset_min_allocation",
        selected_asset_set=selected_asset_set,
        issues=issues,
    )
    selected_max = _selected_asset_constraint(
        constraints.get("selected_asset_max_allocation"),
        constraint_id="selected_asset_max_allocation",
        field_prefix="constraints.selected_asset_max_allocation",
        selected_asset_set=selected_asset_set,
        issues=issues,
    )

    _validate_percent_relationships(
        global_min=global_min,
        global_max=global_max,
        selected_min=selected_min,
        selected_max=selected_max,
        issues=issues,
    )

    min_assets = _optional_asset_count(
        constraints.get("min_assets_in_portfolio"),
        field="constraints.min_assets_in_portfolio",
        constraint_id="min_assets_in_portfolio",
        selected_asset_count=selected_asset_count,
        issues=issues,
    )
    max_assets = _optional_asset_count(
        constraints.get("max_assets_in_portfolio"),
        field="constraints.max_assets_in_portfolio",
        constraint_id="max_assets_in_portfolio",
        selected_asset_count=selected_asset_count,
        issues=issues,
    )

    if min_assets is not None and max_assets is not None and min_assets > max_assets:
        issues.append(
            ValidationIssue(
                field="constraints.min_assets_in_portfolio",
                code="min_assets_constraint_greater_than_max_assets_constraint",
                message="Minimum asset count cannot be greater than maximum asset count.",
                context={
                    "constraint_id": "asset_count",
                    "min_value": min_assets,
                    "max_value": max_assets,
                    "selected_asset_count": selected_asset_count,
                },
            )
        )


def _optional_percent(
    value: Any,
    *,
    field: str,
    constraint_id: str,
    issues: list[ValidationIssue],
) -> float | None:
    if value is None:
        return None
    if not _is_number(value) or value < 0 or value > 100:
        issues.append(
            ValidationIssue(
                field=field,
                code="constraint_percent_invalid",
                message="Allocation constraints must be percentages from 0 to 100.",
                context={"constraint_id": constraint_id},
            )
        )
        return None
    return float(value)


def _required_percent(
    value: Any,
    *,
    field: str,
    constraint_id: str,
    issues: list[ValidationIssue],
) -> float | None:
    if value is None:
        issues.append(
            ValidationIssue(
                field=field,
                code="constraint_percent_invalid",
                message="Allocation constraints must include a percentage from 0 to 100.",
                context={"constraint_id": constraint_id},
            )
        )
        return None
    return _optional_percent(
        value,
        field=field,
        constraint_id=constraint_id,
        issues=issues,
    )


def _selected_asset_constraint(
    value: Any,
    *,
    constraint_id: str,
    field_prefix: str,
    selected_asset_set: set[str],
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    if value in (None, {}):
        return None
    if not isinstance(value, dict):
        issues.append(
            ValidationIssue(
                field=field_prefix,
                code="constraints_invalid_type",
                message="Use the supported selected-asset constraint controls only.",
                context={"constraint_id": constraint_id},
            )
        )
        return None

    for key in value:
        if key not in SELECTED_ASSET_CONSTRAINT_KEYS:
            issues.append(
                ValidationIssue(
                    field=field_prefix,
                    code="unknown_constraint_key",
                    message="Use the supported selected-asset constraint controls only.",
                    context={"constraint_id": constraint_id, "key": key},
                )
            )

    asset_ids = _constraint_asset_ids(
        value.get("asset_ids"),
        field=f"{field_prefix}.asset_ids",
        constraint_id=constraint_id,
        selected_asset_set=selected_asset_set,
        issues=issues,
    )
    percent = _required_percent(
        value.get("percent"),
        field=f"{field_prefix}.percent",
        constraint_id=constraint_id,
        issues=issues,
    )

    if percent is not None and asset_ids and constraint_id.endswith("_min_allocation"):
        if percent * len(asset_ids) > 100:
            issues.append(
                ValidationIssue(
                    field=f"{field_prefix}.percent",
                    code="selected_asset_min_allocation_sum_exceeds_100",
                    message="The minimum allocation for selected assets exceeds 100%.",
                    context={
                        "constraint_id": constraint_id,
                        "min_value": percent,
                        "selected_asset_count": len(asset_ids),
                    },
                )
            )

    if percent is not None and asset_ids and constraint_id.endswith("_max_allocation"):
        if set(asset_ids) == selected_asset_set and percent * len(asset_ids) < 100:
            issues.append(
                ValidationIssue(
                    field=f"{field_prefix}.percent",
                    code="selected_asset_max_allocation_sum_below_100",
                    message="The maximum allocation for selected assets is below 100%.",
                    context={
                        "constraint_id": constraint_id,
                        "max_value": percent,
                        "selected_asset_count": len(asset_ids),
                    },
                )
            )

    if percent is None or asset_ids is None:
        return None
    return {"asset_ids": asset_ids, "percent": percent}


def _constraint_asset_ids(
    value: Any,
    *,
    field: str,
    constraint_id: str,
    selected_asset_set: set[str],
    issues: list[ValidationIssue],
) -> list[str] | None:
    if not isinstance(value, list) or not value:
        issues.append(
            ValidationIssue(
                field=field,
                code="constraint_asset_ids_invalid",
                message="Choose at least one selected asset for this constraint.",
                context={"constraint_id": constraint_id},
            )
        )
        return None

    asset_ids: list[str] = []
    for index, asset_id in enumerate(value):
        if not isinstance(asset_id, str) or not asset_id.strip():
            issues.append(
                ValidationIssue(
                    field=field,
                    code="constraint_asset_ids_invalid",
                    message="Choose valid selected assets for this constraint.",
                    context={"constraint_id": constraint_id, "index": index},
                )
            )
            continue

        normalized = asset_id.strip()
        if normalized in asset_ids:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="constraint_asset_ids_invalid",
                    message="Choose each constrained asset only once.",
                    context={"constraint_id": constraint_id, "asset_id": normalized},
                )
            )
        if normalized not in selected_asset_set:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="constraint_asset_id_not_selected",
                    message="Selected-asset constraints can only reference current assets.",
                    context={"constraint_id": constraint_id, "asset_id": normalized},
                )
            )
        asset_ids.append(normalized)

    return asset_ids


def _validate_percent_relationships(
    *,
    global_min: float | None,
    global_max: float | None,
    selected_min: dict[str, Any] | None,
    selected_max: dict[str, Any] | None,
    issues: list[ValidationIssue],
) -> None:
    if selected_min and global_max is not None and selected_min["percent"] > global_max:
        issues.append(
            ValidationIssue(
                field="constraints.selected_asset_min_allocation.percent",
                code="constraint_min_greater_than_max",
                message="Selected-asset minimum allocation cannot exceed the global maximum.",
                context={
                    "constraint_id": "selected_asset_min_allocation",
                    "min_value": selected_min["percent"],
                    "max_value": global_max,
                    "asset_ids": selected_min["asset_ids"],
                },
            )
        )

    if selected_max and global_min is not None and global_min > selected_max["percent"]:
        issues.append(
            ValidationIssue(
                field="constraints.selected_asset_max_allocation.percent",
                code="constraint_min_greater_than_max",
                message="Global minimum allocation cannot exceed the selected-asset maximum.",
                context={
                    "constraint_id": "selected_asset_max_allocation",
                    "min_value": global_min,
                    "max_value": selected_max["percent"],
                    "asset_ids": selected_max["asset_ids"],
                },
            )
        )

    if not selected_min or not selected_max:
        return

    overlapping_assets = sorted(set(selected_min["asset_ids"]) & set(selected_max["asset_ids"]))
    if overlapping_assets and selected_min["percent"] > selected_max["percent"]:
        issues.append(
            ValidationIssue(
                field="constraints.selected_asset_min_allocation.percent",
                code="constraint_min_greater_than_max",
                message="Selected-asset minimum allocation cannot exceed selected-asset maximum allocation.",
                context={
                    "constraint_id": "selected_asset_allocation_percent",
                    "min_value": selected_min["percent"],
                    "max_value": selected_max["percent"],
                    "asset_ids": overlapping_assets,
                },
            )
        )


def _optional_asset_count(
    value: Any,
    *,
    field: str,
    constraint_id: str,
    selected_asset_count: int,
    issues: list[ValidationIssue],
) -> int | None:
    if value is None or value == 0:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        issues.append(
            ValidationIssue(
                field=field,
                code="constraint_asset_count_invalid",
                message="Asset-count constraints must be whole numbers of at least 1.",
                context={"constraint_id": constraint_id},
            )
        )
        return None
    if (
        constraint_id == "min_assets_in_portfolio"
        and selected_asset_count > 0
        and value > selected_asset_count
    ):
        issues.append(
            ValidationIssue(
                field=field,
                code="min_assets_constraint_exceeds_selected_assets",
                message="Asset-count constraints cannot exceed the number of selected assets.",
                context={
                    "constraint_id": constraint_id,
                    "selected_asset_count": selected_asset_count,
                    "max_value": value,
                },
            )
        )
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
