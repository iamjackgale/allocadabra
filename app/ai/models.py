"""Supported model identifiers for AI-facing validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupportedModel:
    """AI-facing supported model descriptor."""

    model_id: str
    display_name: str


SUPPORTED_MODELS: tuple[SupportedModel, ...] = (
    SupportedModel("mean_variance", "Mean Variance"),
    SupportedModel("risk_parity", "Risk Parity"),
    SupportedModel("hierarchical_risk_parity", "Hierarchical Risk Parity"),
)

SUPPORTED_MODEL_IDS = tuple(model.model_id for model in SUPPORTED_MODELS)
DEFAULT_MODEL_IDS = SUPPORTED_MODEL_IDS
SUPPORTED_MODEL_NAMES = {model.display_name: model.model_id for model in SUPPORTED_MODELS}

FUTURE_ONLY_MODEL_NAMES = (
    "Worst Case",
    "Ordered Weighted Average",
    "Hierarchical Equal Risk",
)


def normalize_selected_model_ids(model_ids: object) -> list[str]:
    """Return selected model IDs, defaulting to the V1 supported set when absent."""
    if not isinstance(model_ids, list) or not model_ids:
        return list(DEFAULT_MODEL_IDS)
    return [str(model_id).strip() for model_id in model_ids if str(model_id).strip()]


def unsupported_model_ids(model_ids: list[str]) -> list[str]:
    """Return model IDs outside the supported V1 set."""
    return [model_id for model_id in model_ids if model_id not in SUPPORTED_MODEL_IDS]


def supported_models_for_prompt() -> list[dict[str, str]]:
    """Return supported model descriptors for prompt context."""
    return [
        {"model_id": model.model_id, "display_name": model.display_name}
        for model in SUPPORTED_MODELS
    ]


def display_name_for_model_id(model_id: str) -> str:
    """Return display name for a supported model ID."""
    for model in SUPPORTED_MODELS:
        if model.model_id == model_id:
            return model.display_name
    return model_id
