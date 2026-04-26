"""AI-owned supported-model access aligned to the Modelling contract."""

from __future__ import annotations

import logging
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelDefinition:
    """Supported model definition consumed by the AI layer."""

    model_id: str
    display_name: str


_FALLBACK_V1_MODELS: tuple[ModelDefinition, ...] = (
    ModelDefinition("mean_variance", "Mean Variance"),
    ModelDefinition("risk_parity", "Risk Parity"),
    ModelDefinition("hierarchical_risk_parity", "Hierarchical Risk Parity"),
    ModelDefinition("hierarchical_equal_risk", "Hierarchical Equal Risk"),
)


def load_supported_models() -> tuple[ModelDefinition, ...]:
    """Return supported AI models from the Modelling contract or a fixed V1 fallback.

    Preferred source:
    - `app.processing.data_api.modelling_contract()` for supported model IDs.
    - `app.processing.models.SUPPORTED_MODELS` for modelling-owned display labels.

    Fallback:
    - the fixed V1 set above, used only when importing the Modelling-owned contract
      fails or returns an unexpected shape.
    """
    try:
        from app.processing.data_api import modelling_contract
        from app.processing.models import SUPPORTED_MODELS as modelling_labels

        contract = modelling_contract()
        supported_ids = contract.get("supported_model_ids", [])
        if not isinstance(supported_ids, list) or not all(isinstance(item, str) for item in supported_ids):
            raise ValueError("Modelling contract returned invalid supported_model_ids.")
        if not isinstance(modelling_labels, dict):
            raise ValueError("Modelling labels were not available.")

        definitions: list[ModelDefinition] = []
        for model_id in supported_ids:
            label = modelling_labels.get(model_id)
            if not isinstance(label, str) or not label.strip():
                raise ValueError(f"Missing modelling-owned label for {model_id}.")
            definitions.append(ModelDefinition(model_id=model_id, display_name=label))
        return tuple(definitions)
    except Exception as exc:
        logger.warning("Falling back to fixed V1 AI supported models: %s", exc)
        return _FALLBACK_V1_MODELS
