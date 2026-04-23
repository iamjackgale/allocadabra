"""AI response and metadata validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ai.models import (
    FUTURE_ONLY_MODEL_NAMES,
    SUPPORTED_MODEL_NAMES,
    display_name_for_model_id,
    normalize_selected_model_ids,
    unsupported_model_ids,
)
from app.ai.parsing import markdown_sections
from app.storage.validation import validate_configuration_inputs


REQUIRED_PLAN_HEADINGS = (
    "objective",
    "risk appetite",
    "selected assets",
    "constraints",
    "selected models",
    "data window",
)


@dataclass(frozen=True)
class MetadataValidation:
    """Validation result for app-actable AI output."""

    valid: bool
    metadata: dict[str, Any]
    issues: list[str]


def validate_modelling_plan(
    markdown: str,
    metadata: dict[str, Any] | None,
    *,
    active_inputs: dict[str, Any] | None = None,
    require_complete: bool = True,
) -> MetadataValidation:
    """Validate plan Markdown and app-actable metadata."""
    issues: list[str] = []
    metadata = dict(metadata or {})

    sections = markdown_sections(markdown)
    missing_headings = [heading for heading in REQUIRED_PLAN_HEADINGS if heading not in sections]
    if missing_headings:
        issues.append("Missing required plan headings: " + ", ".join(missing_headings))

    model_ids = _metadata_model_ids(metadata) or _model_ids_from_markdown(markdown)
    if not model_ids:
        issues.append("Missing selected_model_ids metadata.")
    else:
        metadata["selected_model_ids"] = model_ids

    unsupported = unsupported_model_ids(model_ids)
    if unsupported:
        issues.append("Unsupported model IDs in AI metadata: " + ", ".join(unsupported))

    future_names = _future_only_names_in_text(markdown)
    if future_names:
        issues.append("Future-only models appeared in plan text: " + ", ".join(future_names))

    missing_required_fields = metadata.get("missing_required_fields", [])
    if require_complete and isinstance(missing_required_fields, list) and missing_required_fields:
        issues.append("Plan reports missing required fields: " + ", ".join(map(str, missing_required_fields)))

    if active_inputs is not None:
        expected_model_ids = normalize_selected_model_ids(active_inputs.get("selected_models"))
        if model_ids and set(model_ids) != set(expected_model_ids):
            issues.append("Plan metadata conflicts with the currently selected model IDs.")

        validation_inputs = {**active_inputs, "selected_models": expected_model_ids}
        deterministic = validate_configuration_inputs(validation_inputs)
        if require_complete and not deterministic.valid:
            issues.extend(issue.message for issue in deterministic.issues)

    return MetadataValidation(valid=not issues, metadata=metadata, issues=issues)


def validate_suggested_model_metadata(metadata: dict[str, Any]) -> MetadataValidation:
    """Validate model suggestions in non-plan chat metadata."""
    model_ids = _metadata_model_ids(metadata)
    issues: list[str] = []
    if model_ids:
        unsupported = unsupported_model_ids(model_ids)
        if unsupported:
            issues.append("Unsupported model IDs in AI metadata: " + ", ".join(unsupported))
    return MetadataValidation(valid=not issues, metadata=metadata, issues=issues)


def looks_like_financial_advice(text: str) -> bool:
    """Detect obvious buy/sell/hold/trade recommendations."""
    advice_pattern = re.compile(
        r"\b(?:you should|you need to|i recommend|we recommend|best to|it is best to)\s+"
        r"(?:buy|sell|hold|trade|invest)\b",
        flags=re.IGNORECASE,
    )
    return bool(advice_pattern.search(text))


def _metadata_model_ids(metadata: dict[str, Any]) -> list[str]:
    raw = metadata.get("selected_model_ids")
    if raw is None and isinstance(metadata.get("configuration"), dict):
        raw = metadata["configuration"].get("selected_model_ids")
    if not isinstance(raw, list):
        return []
    return [str(model_id).strip() for model_id in raw if str(model_id).strip()]


def _model_ids_from_markdown(markdown: str) -> list[str]:
    found: list[str] = []
    text = markdown.lower()

    for display_name, model_id in SUPPORTED_MODEL_NAMES.items():
        if model_id in text or display_name.lower() in text:
            found.append(model_id)

    # Stable order for execution metadata.
    ordered = []
    for model_id in normalize_selected_model_ids(found):
        if model_id in found and model_id not in ordered:
            ordered.append(model_id)
    return ordered


def _future_only_names_in_text(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name in FUTURE_ONLY_MODEL_NAMES if name.lower() in lowered]


def selected_model_names(model_ids: list[str]) -> list[str]:
    """Return display names for supported model IDs."""
    return [display_name_for_model_id(model_id) for model_id in model_ids]
