"""Deterministic backend validation for configuration inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MIN_ASSETS = 2
MAX_ASSETS = 10
MIN_MODELS = 1
MAX_MODELS = 3

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

    return ValidationResult(valid=not issues, issues=issues)


def _asset_id(asset: Any) -> str:
    if isinstance(asset, dict):
        return str(asset.get("id", "")).strip()
    return str(asset).strip()

