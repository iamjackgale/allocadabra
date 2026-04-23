"""Single active workflow/session state storage."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Literal

from app.storage.json_files import read_json, write_json
from app.storage.paths import ACTIVE_WORKFLOW_FILE, MODEL_OUTPUT_MANIFEST_FILE, ensure_storage_dirs
from app.storage.schemas import SCHEMA_VERSION, metadata_payload, utc_now_iso


logger = logging.getLogger(__name__)

WorkflowPhase = Literal["configuration", "modelling", "review", "interrupted"]


def default_workflow_state() -> dict[str, Any]:
    """Return an empty/default workflow state."""
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": utc_now_iso(),
        "phase": "configuration",
        "user_inputs": {
            "selected_assets": [],
            "treasury_objective": None,
            "risk_appetite": None,
            "constraints": {},
            "selected_models": [],
        },
        "modelling_plan": {
            "status": "none",
            "markdown": None,
            "metadata": {},
            "confirmed_at": None,
        },
        "chat_sessions": {
            "configuration": [],
            "review": [],
        },
        "modelling_run": {
            "status": "idle",
            "started_at": None,
            "completed_at": None,
            "interrupted_at": None,
            "error": None,
        },
        "model_outputs": {
            "status": "none",
            "manifest_path": None,
        },
    }


def get_workflow_state() -> dict[str, Any]:
    """Load the active workflow state, creating defaults when absent."""
    ensure_storage_dirs()
    payload = read_json(ACTIVE_WORKFLOW_FILE, default=None)
    if payload is None:
        payload = default_workflow_state()
        write_json(ACTIVE_WORKFLOW_FILE, payload)
    return _migrate_or_default(payload)


def save_workflow_state(state: dict[str, Any]) -> dict[str, Any]:
    """Persist the active workflow state."""
    ensure_storage_dirs()
    next_state = _migrate_or_default(state)
    next_state["updated_at"] = utc_now_iso()
    write_json(ACTIVE_WORKFLOW_FILE, next_state)
    return next_state


def update_user_inputs(updates: dict[str, Any]) -> dict[str, Any]:
    """Merge user-input updates into active workflow state."""
    state = get_workflow_state()
    state["user_inputs"].update(updates)
    return save_workflow_state(state)


def store_generated_plan(*, markdown: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Store an unconfirmed AI-generated modelling plan."""
    state = get_workflow_state()
    state["modelling_plan"] = {
        "status": "generated",
        "markdown": markdown,
        "metadata": metadata or {},
        "confirmed_at": None,
    }
    return save_workflow_state(state)


def confirm_generated_plan() -> dict[str, Any]:
    """Mark the generated modelling plan as confirmed."""
    state = get_workflow_state()
    plan = state["modelling_plan"]
    if plan.get("status") != "generated" or not plan.get("markdown"):
        raise ValueError("No generated modelling plan is available to confirm.")
    plan["status"] = "confirmed"
    plan["confirmed_at"] = utc_now_iso()
    return save_workflow_state(state)


def abandon_generated_plan() -> dict[str, Any]:
    """Abandon the current plan while preserving user inputs and configuration chat."""
    state = get_workflow_state()
    state["phase"] = "configuration"
    state["modelling_plan"] = {
        "status": "none",
        "markdown": None,
        "metadata": {},
        "confirmed_at": None,
    }
    state["modelling_run"] = {
        "status": "idle",
        "started_at": None,
        "completed_at": None,
        "interrupted_at": None,
        "error": None,
    }
    state["model_outputs"] = {"status": "none", "manifest_path": None}
    clear_model_outputs()
    return save_workflow_state(state)


def mark_modelling_started() -> dict[str, Any]:
    """Move active workflow into Modelling."""
    state = get_workflow_state()
    state["phase"] = "modelling"
    state["modelling_run"] = {
        "status": "running",
        "started_at": utc_now_iso(),
        "completed_at": None,
        "interrupted_at": None,
        "error": None,
    }
    state["model_outputs"] = {"status": "building", "manifest_path": None}
    clear_model_outputs()
    return save_workflow_state(state)


def mark_modelling_interrupted(error: str | None = None) -> dict[str, Any]:
    """Record that a modelling run was interrupted before outputs were ready."""
    state = get_workflow_state()
    state["phase"] = "interrupted"
    state["modelling_run"]["status"] = "interrupted"
    state["modelling_run"]["interrupted_at"] = utc_now_iso()
    state["modelling_run"]["error"] = error
    state["model_outputs"] = {"status": "none", "manifest_path": None}
    clear_model_outputs()
    return save_workflow_state(state)


def mark_review_ready(manifest: dict[str, Any]) -> dict[str, Any]:
    """Store output manifest and move active workflow into Review."""
    ensure_storage_dirs()
    manifest_payload = metadata_payload(**manifest)
    write_json(MODEL_OUTPUT_MANIFEST_FILE, manifest_payload)

    state = get_workflow_state()
    state["phase"] = "review"
    state["chat_sessions"]["configuration"] = []
    state["modelling_run"]["status"] = "complete"
    state["modelling_run"]["completed_at"] = utc_now_iso()
    state["model_outputs"] = {
        "status": "ready",
        "manifest_path": str(MODEL_OUTPUT_MANIFEST_FILE),
    }
    return save_workflow_state(state)


def clear_model_outputs() -> None:
    """Clear the current model-output manifest without touching market data."""
    if MODEL_OUTPUT_MANIFEST_FILE.exists():
        MODEL_OUTPUT_MANIFEST_FILE.unlink()


def return_to_configure_from_review() -> dict[str, Any]:
    """Clear outputs and Review chat while preserving prior configuration choices."""
    state = get_workflow_state()
    state["phase"] = "configuration"
    state["chat_sessions"]["review"] = []
    state["model_outputs"] = {"status": "none", "manifest_path": None}
    state["modelling_run"] = default_workflow_state()["modelling_run"]
    clear_model_outputs()
    return save_workflow_state(state)


def reset_configuration() -> dict[str, Any]:
    """Clear inputs, plans, chats, and outputs without touching CoinGecko cache."""
    clear_model_outputs()
    state = default_workflow_state()
    return save_workflow_state(state)


def start_new_model() -> dict[str, Any]:
    """Alias for the V1 start-new-model lifecycle."""
    return reset_configuration()


def _migrate_or_default(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return default_workflow_state()

    state = deepcopy(default_workflow_state())
    nested_keys = {
        "user_inputs",
        "modelling_plan",
        "chat_sessions",
        "modelling_run",
        "model_outputs",
    }

    for key, value in payload.items():
        if key in nested_keys:
            if isinstance(value, dict):
                state[key].update(value)
            continue
        state[key] = value

    state["schema_version"] = SCHEMA_VERSION
    return state
