"""Typed helpers for app-actable AI metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


MetadataKind = Literal[
    "modelling_plan",
    "configuration_suggestion",
    "review_response",
    "review_opening",
    "imported_modelling_plan",
]


@dataclass(frozen=True)
class ParsedPlanFields:
    """Structured fields parsed from a modelling plan Markdown document."""

    objective: str | None = None
    risk_appetite: str | None = None
    selected_assets: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    selected_model_ids: list[str] = field(default_factory=list)
    data_window: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "risk_appetite": self.risk_appetite,
            "selected_assets": self.selected_assets,
            "constraints": self.constraints,
            "selected_model_ids": self.selected_model_ids,
            "data_window": self.data_window,
        }


@dataclass(frozen=True)
class ModellingPlanMetadata:
    """Typed metadata required for app-actable modelling plans."""

    selected_model_ids: list[str]
    missing_required_fields: list[str] = field(default_factory=list)
    parsed_plan: ParsedPlanFields | None = None
    kind: MetadataKind = "modelling_plan"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": self.kind,
            "selected_model_ids": self.selected_model_ids,
            "missing_required_fields": self.missing_required_fields,
        }
        if self.parsed_plan is not None:
            payload["parsed_plan"] = self.parsed_plan.to_dict()
        return payload


@dataclass(frozen=True)
class ConfigurationSuggestionMetadata:
    """Typed metadata for non-plan Configuration Mode suggestions."""

    selected_model_ids: list[str] = field(default_factory=list)
    missing_required_fields: list[str] = field(default_factory=list)
    kind: MetadataKind = "configuration_suggestion"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "selected_model_ids": self.selected_model_ids,
            "missing_required_fields": self.missing_required_fields,
        }


@dataclass(frozen=True)
class ReviewResponseMetadata:
    """Typed metadata for optional Review Mode response references."""

    referenced_model_ids: list[str] = field(default_factory=list)
    referenced_metric_names: list[str] = field(default_factory=list)
    referenced_artifact_ids: list[str] = field(default_factory=list)
    referenced_output_table_names: list[str] = field(default_factory=list)
    needs_detailed_context: bool = False
    kind: MetadataKind = "review_response"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "referenced_model_ids": self.referenced_model_ids,
            "referenced_metric_names": self.referenced_metric_names,
            "referenced_artifact_ids": self.referenced_artifact_ids,
            "referenced_output_table_names": self.referenced_output_table_names,
            "needs_detailed_context": self.needs_detailed_context,
        }


def list_of_strings(value: object) -> list[str]:
    """Return a normalized list of non-empty strings."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def bool_value(value: object) -> bool:
    """Return a strict bool from app metadata."""
    return value is True
