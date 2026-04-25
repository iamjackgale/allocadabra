"""AI response and metadata validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ai.models import (
    FUTURE_ONLY_MODEL_IDS,
    FUTURE_ONLY_MODEL_NAMES,
    SUPPORTED_MODEL_IDS,
    SUPPORTED_MODEL_NAMES,
    display_name_for_model_id,
    model_id_from_text,
    normalize_selected_model_ids,
    unsupported_model_ids,
)
from app.ai.parsing import markdown_sections
from app.ai.schemas import (
    ConfigurationSuggestionMetadata,
    ModellingPlanMetadata,
    ParsedPlanFields,
    ReviewResponseMetadata,
    bool_value,
    list_of_strings,
)
from app.storage.validation import RISK_APPETITES, TREASURY_OBJECTIVES, validate_configuration_inputs


REQUIRED_PLAN_HEADINGS = (
    "objective",
    "risk appetite",
    "selected assets",
    "constraints",
    "selected models",
    "data window",
)

SUPPORTED_CONSTRAINT_PHRASES = (
    "none",
    "no constraints",
    "max allocation per asset",
    "maximum allocation per asset",
    "min allocation per asset",
    "minimum allocation per asset",
    "max allocation to selected asset",
    "maximum allocation to selected asset",
    "min allocation to selected asset",
    "minimum allocation to selected asset",
    "max number of assets",
    "maximum number of assets",
    "min number of assets",
    "minimum number of assets",
)

DATA_WINDOW_PHRASES = (
    "365",
    "coingecko",
    "daily observations",
)

KNOWN_METRIC_NAMES = {
    "total_return_pct",
    "max_drawdown_pct",
    "sharpe_ratio",
    "calmar_ratio",
    "omega_ratio",
    "sortino_ratio",
    "annualized_return_pct",
    "annualized_volatility_pct",
    "30d_volatility_pct",
    "avg_drawdown_pct",
    "skewness",
    "kurtosis",
    "cvar_pct",
    "cdar_pct",
}

METRIC_NAME_ALIASES = {
    "sharpe": "sharpe_ratio",
    "sharpe ratio": "sharpe_ratio",
    "calmar": "calmar_ratio",
    "calmar ratio": "calmar_ratio",
    "omega": "omega_ratio",
    "omega ratio": "omega_ratio",
    "sortino": "sortino_ratio",
    "sortino ratio": "sortino_ratio",
    "annualized return": "annualized_return_pct",
    "annualised return": "annualized_return_pct",
    "annualized volatility": "annualized_volatility_pct",
    "annualised volatility": "annualized_volatility_pct",
    "30d volatility": "30d_volatility_pct",
    "30-day volatility": "30d_volatility_pct",
    "max drawdown": "max_drawdown_pct",
    "average drawdown": "avg_drawdown_pct",
    "cvar": "cvar_pct",
    "cdar": "cdar_pct",
}


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

    parsed_plan = parse_modelling_plan_fields(markdown)
    issues.extend(_plan_field_issues(parsed_plan, sections))

    incoming_parsed_metadata = metadata.get("parsed_plan")
    metadata_model_ids = _metadata_model_ids(metadata)
    model_ids = metadata_model_ids or parsed_plan.selected_model_ids
    if not model_ids:
        issues.append("Missing selected_model_ids metadata.")
    else:
        metadata["selected_model_ids"] = model_ids

    unsupported = unsupported_model_ids(model_ids)
    if unsupported:
        issues.append("Unsupported model IDs in AI metadata: " + ", ".join(unsupported))

    future_model_ids = [model_id for model_id in model_ids if model_id in FUTURE_ONLY_MODEL_IDS]
    if future_model_ids:
        issues.append("Future-only model IDs appeared in AI metadata: " + ", ".join(future_model_ids))

    future_names = _future_only_names_in_text(markdown)
    if future_names:
        issues.append("Future-only models appeared in plan text: " + ", ".join(future_names))

    issues.extend(_metadata_text_conflicts(incoming_parsed_metadata, parsed_plan, metadata_model_ids))

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
        issues.extend(_active_input_conflicts(active_inputs, parsed_plan, expected_model_ids))

    if not issues:
        plan_metadata = ModellingPlanMetadata(
            kind=str(metadata.get("kind") or "modelling_plan"),  # type: ignore[arg-type]
            selected_model_ids=model_ids,
            missing_required_fields=list_of_strings(missing_required_fields),
            parsed_plan=parsed_plan,
        )
        metadata = plan_metadata.to_dict()
    return MetadataValidation(valid=not issues, metadata=metadata, issues=issues)


def validate_suggested_model_metadata(metadata: dict[str, Any]) -> MetadataValidation:
    """Validate model suggestions in non-plan chat metadata."""
    model_ids = _metadata_model_ids(metadata)
    issues: list[str] = []
    if model_ids:
        unsupported = unsupported_model_ids(model_ids)
        if unsupported:
            issues.append("Unsupported model IDs in AI metadata: " + ", ".join(unsupported))
        future_model_ids = [model_id for model_id in model_ids if model_id in FUTURE_ONLY_MODEL_IDS]
        if future_model_ids:
            issues.append("Future-only model IDs appeared in AI metadata: " + ", ".join(future_model_ids))

    future_names = _future_only_names_in_text(str(metadata))
    if future_names:
        issues.append("Future-only models appeared in AI metadata: " + ", ".join(future_names))

    if not issues:
        metadata = ConfigurationSuggestionMetadata(
            selected_model_ids=model_ids,
            missing_required_fields=list_of_strings(metadata.get("missing_required_fields")),
        ).to_dict()
    return MetadataValidation(valid=not issues, metadata=metadata, issues=issues)


def validate_review_metadata(metadata: dict[str, Any]) -> MetadataValidation:
    """Validate optional Review Mode response metadata."""
    model_ids = list_of_strings(metadata.get("referenced_model_ids"))
    metric_names = _normalize_metric_names(metadata.get("referenced_metric_names"))
    issues: list[str] = []

    unsupported = unsupported_model_ids(model_ids)
    if unsupported:
        issues.append("Unsupported model IDs in Review metadata: " + ", ".join(unsupported))

    future_model_ids = [model_id for model_id in model_ids if model_id in FUTURE_ONLY_MODEL_IDS]
    if future_model_ids:
        issues.append("Future-only model IDs appeared in Review metadata: " + ", ".join(future_model_ids))

    future_names = _future_only_names_in_text(str(metadata))
    if future_names:
        issues.append("Future-only models appeared in Review metadata: " + ", ".join(future_names))

    if not issues:
        metadata = ReviewResponseMetadata(
            referenced_model_ids=model_ids,
            referenced_metric_names=metric_names,
            referenced_artifact_ids=list_of_strings(metadata.get("referenced_artifact_ids")),
            referenced_output_table_names=list_of_strings(metadata.get("referenced_output_table_names")),
            needs_detailed_context=bool_value(metadata.get("needs_detailed_context")),
        ).to_dict()
    return MetadataValidation(valid=not issues, metadata=metadata, issues=issues)


def parse_modelling_plan_fields(markdown: str) -> ParsedPlanFields:
    """Parse required V1 modelling-plan fields from Markdown headings."""
    sections = markdown_sections(markdown)
    return ParsedPlanFields(
        objective=_parse_choice(sections.get("objective", ""), TREASURY_OBJECTIVES),
        risk_appetite=_parse_choice(sections.get("risk appetite", ""), RISK_APPETITES),
        selected_assets=_parse_list_section(sections.get("selected assets", "")),
        constraints=_parse_list_section(sections.get("constraints", "")),
        selected_model_ids=_model_ids_from_text(sections.get("selected models", "")),
        data_window=_clean_section_value(sections.get("data window", "")),
    )


def looks_like_financial_advice(text: str) -> bool:
    """Detect obvious buy/sell/hold/trade recommendations."""
    advice_pattern = re.compile(
        r"\b(?:you should|you need to|i recommend|we recommend|best to|it is best to)\s+"
        r"(?:buy|sell|hold|trade|invest|buying|selling|holding|trading|investing)\b",
        flags=re.IGNORECASE,
    )
    return bool(advice_pattern.search(text))


def user_requests_financial_advice(text: str) -> bool:
    """Detect direct user requests for investment instructions."""
    request_pattern = re.compile(
        r"\b(?:should i|should we|do you recommend|would you recommend|is it a good time to)\s+"
        r"(?:buy|sell|hold|trade|invest|buying|selling|holding|trading|investing)\b",
        flags=re.IGNORECASE,
    )
    return bool(request_pattern.search(text))


def user_requests_direct_model_choice(text: str) -> bool:
    """Detect direct requests to choose one model on the user's behalf."""
    lowered = text.lower()
    phrases = (
        "which model should i choose",
        "which model should we choose",
        "which model do i choose",
        "which model do we choose",
        "tell me which model to choose",
        "pick a model for me",
        "choose a model for me",
    )
    return any(phrase in lowered for phrase in phrases)


def user_requests_live_data(text: str) -> bool:
    """Detect requests for live or real-time market data."""
    lowered = text.lower()
    return (
        "live coingecko" in lowered
        or "real-time" in lowered
        or "real time" in lowered
        or ("live" in lowered and "price" in lowered)
    )


def user_requests_unsupported_model(text: str) -> bool:
    """Detect requests for models outside the supported V1 set."""
    lowered = text.lower()
    unsupported_names = (
        "black-litterman",
        "black litterman",
        *(name.lower() for name in FUTURE_ONLY_MODEL_NAMES),
    )
    return any(name in lowered for name in unsupported_names)


def _metadata_model_ids(metadata: dict[str, Any]) -> list[str]:
    raw = metadata.get("selected_model_ids")
    if raw is None and isinstance(metadata.get("configuration"), dict):
        raw = metadata["configuration"].get("selected_model_ids")
    if not isinstance(raw, list):
        return []
    return [str(model_id).strip() for model_id in raw if str(model_id).strip()]


def _model_ids_from_text(markdown: str) -> list[str]:
    found: list[str] = []
    text = markdown.lower()

    for display_name, model_id in SUPPORTED_MODEL_NAMES.items():
        if model_id in text or display_name.lower() in text:
            found.append(model_id)
    for token in re.split(r"[\n,;|]+", markdown):
        model_id = model_id_from_text(_strip_bullet(token))
        if model_id:
            found.append(model_id)

    # Stable order for execution metadata.
    ordered = []
    for model_id in SUPPORTED_MODEL_IDS:
        if model_id in found and model_id not in ordered:
            ordered.append(model_id)
    return ordered


def _future_only_names_in_text(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name in FUTURE_ONLY_MODEL_NAMES if name.lower() in lowered]


def selected_model_names(model_ids: list[str]) -> list[str]:
    """Return display names for supported model IDs."""
    return [display_name_for_model_id(model_id) for model_id in model_ids]


def _normalize_metric_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for item in value:
        raw = str(item).strip()
        if not raw:
            continue
        lowered = raw.lower()
        normalized_name = METRIC_NAME_ALIASES.get(lowered, lowered)
        if normalized_name in KNOWN_METRIC_NAMES and normalized_name not in normalized:
            normalized.append(normalized_name)
    return normalized


def _parse_choice(value: str, choices: set[str]) -> str | None:
    text = value.strip().lower()
    for choice in choices:
        if choice.lower() in text:
            return choice
    return None


def _parse_list_section(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) == 1:
        lines = re.split(r",|;", lines[0])
    return [_strip_bullet(line) for line in lines if _strip_bullet(line)]


def _clean_section_value(value: str) -> str | None:
    cleaned = " ".join(_strip_bullet(line) for line in value.splitlines() if line.strip()).strip()
    return cleaned or None


def _strip_bullet(value: str) -> str:
    return re.sub(r"^\s*[-*+\d.)]+\s*", "", value).strip()


def _plan_field_issues(
    parsed_plan: ParsedPlanFields,
    sections: dict[str, str],
) -> list[str]:
    issues: list[str] = []
    if "objective" in sections and not parsed_plan.objective:
        issues.append("Objective must be one supported treasury objective.")
    if "risk appetite" in sections and not parsed_plan.risk_appetite:
        issues.append("Risk Appetite must be one supported risk appetite.")
    if "selected assets" in sections and not parsed_plan.selected_assets:
        issues.append("Selected Assets must list at least 2 assets.")
    if parsed_plan.selected_assets and len(parsed_plan.selected_assets) < 2:
        issues.append("Selected Assets must list at least 2 assets.")
    if len(parsed_plan.selected_assets) > 10:
        issues.append("Selected Assets must list no more than 10 assets.")
    normalised_assets = [_normalise_label(asset) for asset in parsed_plan.selected_assets]
    if len(normalised_assets) != len(set(normalised_assets)):
        issues.append("Selected Assets must not contain duplicates.")
    if "selected models" in sections and not parsed_plan.selected_model_ids:
        issues.append("Selected Models must list at least one supported model.")
    if "constraints" in sections and not _constraints_supported(parsed_plan.constraints):
        issues.append("Constraints must use only supported V1 constraint categories.")
    if "data window" in sections and not _data_window_supported(parsed_plan.data_window):
        issues.append("Data Window must use the last 365 daily observations available from CoinGecko.")
    return issues


def _constraints_supported(constraints: list[str]) -> bool:
    if not constraints:
        return True
    for constraint in constraints:
        lowered = constraint.lower()
        if not any(phrase in lowered for phrase in SUPPORTED_CONSTRAINT_PHRASES):
            return False
    return True


def _data_window_supported(data_window: str | None) -> bool:
    if data_window is None:
        return False
    lowered = data_window.lower()
    return any(phrase in lowered for phrase in DATA_WINDOW_PHRASES)


def _metadata_text_conflicts(
    parsed_metadata: object,
    parsed_plan: ParsedPlanFields,
    metadata_model_ids: list[str],
) -> list[str]:
    issues: list[str] = []
    if metadata_model_ids and parsed_plan.selected_model_ids:
        if set(metadata_model_ids) != set(parsed_plan.selected_model_ids):
            issues.append("Plan text and metadata list different selected model IDs.")

    if isinstance(parsed_metadata, dict):
        if _conflicts(parsed_metadata.get("objective"), parsed_plan.objective):
            issues.append("Plan text and metadata conflict on objective.")
        if _conflicts(parsed_metadata.get("risk_appetite"), parsed_plan.risk_appetite):
            issues.append("Plan text and metadata conflict on risk appetite.")
        parsed_metadata_models = list_of_strings(parsed_metadata.get("selected_model_ids"))
        if parsed_metadata_models and parsed_plan.selected_model_ids:
            if set(parsed_metadata_models) != set(parsed_plan.selected_model_ids):
                issues.append("Plan text and metadata conflict on selected models.")
    return issues


def _active_input_conflicts(
    active_inputs: dict[str, Any],
    parsed_plan: ParsedPlanFields,
    expected_model_ids: list[str],
) -> list[str]:
    issues: list[str] = []
    if parsed_plan.objective and active_inputs.get("treasury_objective") != parsed_plan.objective:
        issues.append("Plan text conflicts with the currently selected treasury objective.")
    if parsed_plan.risk_appetite and active_inputs.get("risk_appetite") != parsed_plan.risk_appetite:
        issues.append("Plan text conflicts with the currently selected risk appetite.")
    if parsed_plan.selected_model_ids and set(parsed_plan.selected_model_ids) != set(expected_model_ids):
        issues.append("Plan text conflicts with the currently selected model IDs.")
    active_assets = _asset_labels(active_inputs.get("selected_assets", []))
    if parsed_plan.selected_assets and active_assets:
        if not all(_asset_matches_active(asset, active_assets) for asset in parsed_plan.selected_assets):
            issues.append("Plan text includes assets outside the current selected assets.")
    return issues


def _asset_labels(assets: object) -> set[str]:
    labels: set[str] = set()
    if not isinstance(assets, list):
        return labels
    for asset in assets:
        if isinstance(asset, dict):
            for key in ("id", "symbol", "name"):
                value = str(asset.get(key, "")).strip()
                if value:
                    labels.add(_normalise_label(value))
        else:
            value = str(asset).strip()
            if value:
                labels.add(_normalise_label(value))
    return labels


def _normalise_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _asset_matches_active(parsed_asset: str, active_assets: set[str]) -> bool:
    parsed = _normalise_label(parsed_asset)
    parsed_parts = set(parsed.split())
    for active in active_assets:
        if parsed == active or active in parsed_parts or active in parsed:
            return True
    return False


def _conflicts(metadata_value: object, parsed_value: str | None) -> bool:
    if not metadata_value or not parsed_value:
        return False
    return str(metadata_value).strip().lower() != parsed_value.strip().lower()
