"""Serializable app-data functions intended for frontend/app-layer callers."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from app.storage.market_cache import (
    get_price_history,
    get_token_options,
    price_cache_status,
    search_token_options,
)
from app.storage.session_state import get_workflow_state, save_workflow_state, update_user_inputs
from app.storage.validation import validate_configuration_inputs


logger = logging.getLogger(__name__)


def list_token_options(
    *,
    search_term: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Return token options as frontend-serializable dictionaries."""
    if search_term:
        tokens = search_token_options(search_term, force_refresh=force_refresh)
    else:
        tokens = get_token_options(force_refresh=force_refresh)

    return {
        "ok": True,
        "tokens": [token.to_dict() for token in tokens],
        "count": len(tokens),
    }


def fetch_price_history_for_assets(
    asset_ids: list[str],
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Fetch/read normalized price histories for selected asset IDs."""
    prices: dict[str, list[dict[str, str | float]]] = {}
    statuses: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for coin_id in asset_ids:
        try:
            points = get_price_history(coin_id, force_refresh=force_refresh)
            prices[coin_id] = [point.to_dict() for point in points]
            statuses.append(asdict(price_cache_status(coin_id, points)))
        except Exception as exc:  # Frontend needs a recoverable per-asset failure shape.
            logger.warning("Price history unavailable for %s: %s", coin_id, exc)
            errors.append(
                {
                    "id": coin_id,
                    "code": "price_history_unavailable",
                    "message": "Price history could not be fetched for this asset.",
                }
            )

    return {
        "ok": not errors,
        "prices": prices,
        "statuses": statuses,
        "errors": errors,
    }


def get_active_workflow() -> dict[str, Any]:
    """Return the active workflow state."""
    return get_workflow_state()


def update_active_inputs(updates: dict[str, Any]) -> dict[str, Any]:
    """Update active user inputs and return the full workflow state."""
    return update_user_inputs(updates)


def validate_active_configuration() -> dict[str, Any]:
    """Validate the current active user-input state."""
    state = get_workflow_state()
    result = validate_configuration_inputs(state.get("user_inputs", {}))
    return {
        "valid": result.valid,
        "issues": [asdict(issue) for issue in result.issues],
    }


def save_active_workflow(state: dict[str, Any]) -> dict[str, Any]:
    """Persist an edited active workflow state."""
    return save_workflow_state(state)
