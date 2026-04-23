"""Review Mode detailed-context selection rules."""

from __future__ import annotations

from typing import Any

from app.ai.models import SUPPORTED_MODELS


OUTPUT_KEYWORDS = {
    "summary_metrics": ("metric", "metrics", "summary", "return", "volatility", "sharpe"),
    "allocations": ("allocation", "allocations", "weight", "weights", "portfolio"),
    "allocation_over_time": ("allocation over time", "weights over time"),
    "backtested_performance": ("backtest", "backtested", "performance", "equity curve"),
    "cumulative_performance": ("cumulative", "cumulative performance"),
    "drawdown": ("drawdown", "downside"),
    "rolling_volatility": ("rolling volatility", "rolling vol"),
    "efficient_frontier": ("efficient frontier", "frontier"),
    "risk_contributions": ("risk contribution", "risk contributions", "contribution"),
    "transformation_metadata": ("transformation", "methodology", "input data", "returns"),
    "warnings": ("warning", "warnings", "failure", "failed", "error"),
}

OUTPUT_ALIASES = {
    "allocation": "allocations",
    "allocation_weights": "allocations",
    "weights": "allocations",
    "allocation_over_time": "allocation_over_time",
    "allocations_over_time": "allocation_over_time",
    "backtest": "backtested_performance",
    "performance": "backtested_performance",
    "cumulative": "cumulative_performance",
    "risk_contribution": "risk_contributions",
    "risk_contributions": "risk_contributions",
    "summary": "summary_metrics",
    "metrics": "summary_metrics",
    "metric": "summary_metrics",
    "failure": "warnings",
    "failed": "warnings",
    "warnings": "warnings",
}


def select_review_detailed_context(
    *,
    user_message: str,
    visible_context: dict[str, Any] | None,
    available_detailed_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Select only referenced or visible detailed Review context."""
    if not available_detailed_context:
        return {}

    model_ids = _referenced_model_ids(user_message)
    output_types = _referenced_output_types(user_message)

    if visible_context:
        visible_model = _first_present(
            visible_context,
            "visible_model_id",
            "selected_model_id",
            "model_id",
        )
        if visible_model:
            model_ids.add(str(visible_model))

        visible_output = _first_present(
            visible_context,
            "visible_output_type",
            "output_type",
            "visible_section",
            "section",
        )
        if visible_output:
            output_types.add(_normalise_output_type(str(visible_output)))

        for key in ("selected_metric_row", "metric_row"):
            if visible_context.get(key):
                output_types.add("summary_metrics")

        open_expanders = visible_context.get("open_expander_ids")
        if isinstance(open_expanders, list):
            output_types.update(_normalise_output_type(str(item)) for item in open_expanders)

        for key in ("visible_chart_id", "visible_table_id", "artifact_id", "output_table_name"):
            value = visible_context.get(key)
            if value:
                output_types.add(_normalise_output_type(str(value)))

    if len(model_ids) >= 2 and not output_types:
        output_types.update({"summary_metrics", "allocations", "transformation_metadata"})

    if not model_ids and not output_types:
        return {}

    return _filter_context(available_detailed_context, model_ids=model_ids, output_types=output_types)


def _referenced_model_ids(user_message: str) -> set[str]:
    text = user_message.lower()
    model_ids: set[str] = set()
    for model in SUPPORTED_MODELS:
        if model.model_id in text or model.display_name.lower() in text:
            model_ids.add(model.model_id)
    if "hrp" in text:
        model_ids.add("hierarchical_risk_parity")
    return model_ids


def _referenced_output_types(user_message: str) -> set[str]:
    text = user_message.lower()
    output_types: set[str] = set()
    for output_type, keywords in OUTPUT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            output_types.add(output_type)
    return output_types


def _filter_context(
    context: dict[str, Any],
    *,
    model_ids: set[str],
    output_types: set[str],
) -> dict[str, Any]:
    selected: dict[str, Any] = {}

    models = context.get("models")
    if isinstance(models, dict) and model_ids:
        selected_models = _filter_model_map(models, model_ids=model_ids, output_types=output_types)
        if selected_models:
            selected["models"] = selected_models

    top_level_models = _filter_model_map(context, model_ids=model_ids, output_types=output_types)
    for key, value in top_level_models.items():
        selected.setdefault(key, value)

    for output_type in output_types:
        if output_type in context:
            selected[output_type] = context[output_type]
        alias = _normalise_output_type(output_type)
        if alias in context:
            selected[alias] = context[alias]

    return selected


def _filter_model_map(
    model_map: dict[str, Any],
    *,
    model_ids: set[str],
    output_types: set[str],
) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for model_id in model_ids:
        model_payload = model_map.get(model_id)
        if not isinstance(model_payload, dict):
            continue
        if output_types:
            selected_payload = {
                key: value
                for key, value in model_payload.items()
                if _normalise_output_type(key) in output_types
            }
        else:
            selected_payload = model_payload
        if selected_payload:
            selected[model_id] = selected_payload
    return selected


def _normalise_output_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _normalise_output_type(value: str) -> str:
    normalized = _normalise_output_key(value)
    return OUTPUT_ALIASES.get(normalized, normalized)


def _first_present(payload: dict[str, Any], *keys: str) -> object | None:
    for key in keys:
        value = payload.get(key)
        if value:
            return value
    return None
