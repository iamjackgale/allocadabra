"""Frontend session state and background modelling runtime helpers."""

from __future__ import annotations

import queue
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import streamlit as st

from app.processing import run_active_modelling
from app.storage import (
    abandon_generated_plan,
    confirm_generated_plan,
    mark_modelling_interrupted,
    mark_modelling_started,
    prepare_review_export_bundle,
)


UI_STATE_KEY = "allocadabra_ui"


def init_ui_state() -> dict[str, Any]:
    """Ensure frontend-only session state exists."""
    if UI_STATE_KEY not in st.session_state:
        st.session_state[UI_STATE_KEY] = {
            "confirmation": None,
            "chat_feedback": {"configuration": None, "review": None},
            "chat_retry_messages": {"configuration": None, "review": None},
            "chat_failure_counts": {"configuration": 0, "review": 0},
            "review_section": "summary_metrics",
            "review_model_id": None,
            "review_gate_pending": False,
            "review_opening_attempted_for": None,
            "token_force_refresh_next": False,
            "modelling_run": {
                "status": "idle",
                "thread": None,
                "queue": None,
                "cancel_event": None,
                "progress_events": [],
                "result": None,
                "output_dir": None,
                "started_at": None,
                "cancel_requested": False,
                "export_prepared": False,
                "interruption_checked": False,
            },
        }
    return st.session_state[UI_STATE_KEY]


def ui_state() -> dict[str, Any]:
    """Return the frontend session state."""
    return init_ui_state()


def modelling_state() -> dict[str, Any]:
    """Return the current modelling runtime state."""
    return ui_state()["modelling_run"]


def set_chat_feedback(mode: str, message: str | None) -> None:
    """Set one ephemeral chat feedback message."""
    state = ui_state()
    state["chat_feedback"][mode] = message


def get_chat_feedback(mode: str) -> str | None:
    """Return one ephemeral chat feedback message."""
    return ui_state()["chat_feedback"].get(mode)


def clear_chat_feedback(mode: str) -> None:
    """Clear ephemeral chat feedback."""
    set_chat_feedback(mode, None)


def register_chat_failure(mode: str, message: str, retry_message: str | None) -> int:
    """Track one recoverable chat failure."""
    state = ui_state()
    state["chat_failure_counts"][mode] += 1
    state["chat_retry_messages"][mode] = retry_message
    if state["chat_failure_counts"][mode] >= 3:
        state["chat_feedback"][mode] = (
            "Repeated failures stopped automatic retries. Please wait and refresh the app."
        )
    else:
        state["chat_feedback"][mode] = message
    return int(state["chat_failure_counts"][mode])


def clear_chat_failure(mode: str) -> None:
    """Clear chat failure counters after success."""
    state = ui_state()
    state["chat_failure_counts"][mode] = 0
    state["chat_retry_messages"][mode] = None
    state["chat_feedback"][mode] = None


def retry_message_for(mode: str) -> str | None:
    """Return the last retryable message for a mode."""
    return ui_state()["chat_retry_messages"].get(mode)


def chat_failure_count(mode: str) -> int:
    """Return consecutive AI failure count for one chat mode."""
    return int(ui_state()["chat_failure_counts"].get(mode, 0))


def request_confirmation(action: str, message: str) -> None:
    """Store a pending confirmation action."""
    ui_state()["confirmation"] = {"action": action, "message": message}


def confirmation_state() -> dict[str, str] | None:
    """Return the pending confirmation action, if any."""
    confirmation = ui_state().get("confirmation")
    return confirmation if isinstance(confirmation, dict) else None


def clear_confirmation() -> None:
    """Clear any pending confirmation action."""
    ui_state()["confirmation"] = None


def set_review_section(section_id: str) -> None:
    """Set the current review section."""
    ui_state()["review_section"] = section_id


def current_review_section() -> str:
    """Return the current review section."""
    return str(ui_state().get("review_section", "summary_metrics"))


def set_review_model_id(model_id: str | None) -> None:
    """Set the current review model."""
    ui_state()["review_model_id"] = model_id


def current_review_model_id() -> str | None:
    """Return the current review model ID."""
    value = ui_state().get("review_model_id")
    return str(value) if value else None


def set_review_gate_pending(value: bool) -> None:
    """Control the post-modelling Review Results gate."""
    ui_state()["review_gate_pending"] = value


def review_gate_pending() -> bool:
    """Return whether the modelling success gate is still active."""
    return bool(ui_state().get("review_gate_pending"))


def note_review_opening_attempt(manifest_key: str | None) -> None:
    """Record the manifest path used for a Review opening attempt."""
    ui_state()["review_opening_attempted_for"] = manifest_key


def review_opening_attempted_for() -> str | None:
    """Return the manifest path used for the last Review opening attempt."""
    value = ui_state().get("review_opening_attempted_for")
    return str(value) if value else None


def start_modelling_run(*, force_refresh_prices: bool = False) -> None:
    """Confirm the current plan, enter Modelling, and launch a background run."""
    workflow = st.session_state.get("allocadabra_workflow_snapshot")
    plan_status = None
    if isinstance(workflow, dict):
        plan_status = workflow.get("modelling_plan", {}).get("status")
    if plan_status != "confirmed":
        confirm_generated_plan()
    mark_modelling_started()

    output_dir = Path(tempfile.mkdtemp(prefix="allocadabra-run-", dir="/tmp"))
    event_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    cancel_event = threading.Event()
    thread = threading.Thread(
        target=_modelling_worker,
        kwargs={
            "event_queue": event_queue,
            "output_dir": output_dir,
            "force_refresh_prices": force_refresh_prices,
            "cancel_event": cancel_event,
        },
        daemon=True,
        name="allocadabra-modelling-run",
    )

    state = modelling_state()
    state.update(
        {
            "status": "running",
            "thread": thread,
            "queue": event_queue,
            "cancel_event": cancel_event,
            "progress_events": [],
            "result": None,
            "output_dir": str(output_dir),
            "started_at": time.time(),
            "cancel_requested": False,
            "export_prepared": False,
            "interruption_checked": False,
        }
    )
    set_review_gate_pending(False)
    thread.start()


def drain_modelling_updates() -> None:
    """Drain queued modelling events and finalize run-level transitions."""
    state = modelling_state()
    event_queue = state.get("queue")
    if not isinstance(event_queue, queue.Queue):
        return

    while True:
        try:
            item = event_queue.get_nowait()
        except queue.Empty:
            break

        kind = item.get("kind")
        payload = item.get("payload")
        if kind == "progress" and isinstance(payload, dict):
            state["progress_events"].append(payload)
            continue

        if kind == "result" and isinstance(payload, dict):
            state["result"] = payload
            if state.get("cancel_requested") or _is_cancelled_result(payload):
                state["status"] = "cancelled"
                _cleanup_temp_output_dir(state.get("output_dir"))
                _reset_run_tracking(keep_result=False)
                return

            if payload.get("ok") and not state.get("export_prepared"):
                exports = prepare_review_export_bundle(
                    modelling_artifacts=_artifacts_for_export(payload),
                    failed_models=payload.get("failed_models", []),
                    missing_artifacts=payload.get("missing_artifacts", []),
                )
                state["export_prepared"] = True
                state["exports"] = exports
                state["status"] = "review_ready"
                set_review_gate_pending(True)
                _cleanup_temp_output_dir(state.get("output_dir"))
            else:
                state["status"] = "failed"
                _cleanup_temp_output_dir(state.get("output_dir"))

    thread = state.get("thread")
    if isinstance(thread, threading.Thread) and not thread.is_alive() and state.get("status") == "running":
        state["status"] = "failed"


def cancel_modelling_run() -> None:
    """Abandon the current plan and return the workflow to Configuration."""
    state = modelling_state()
    state["cancel_requested"] = True
    state["status"] = "cancel_requested"
    cancel_event = state.get("cancel_event")
    if isinstance(cancel_event, threading.Event):
        cancel_event.set()
    abandon_generated_plan()
    set_review_gate_pending(False)


def clear_modelling_run() -> None:
    """Clear completed or abandoned modelling session state."""
    _reset_run_tracking(keep_result=False)


def has_active_modelling_thread() -> bool:
    """Return whether a background modelling thread is alive."""
    thread = modelling_state().get("thread")
    return isinstance(thread, threading.Thread) and thread.is_alive()


def modelling_elapsed_seconds() -> float:
    """Return approximate modelling elapsed time in seconds."""
    started_at = modelling_state().get("started_at")
    if not isinstance(started_at, (int, float)):
        return 0.0
    return max(0.0, time.time() - float(started_at))


def ensure_interrupted_state(workflow_phase: str) -> None:
    """Mark an orphaned modelling run as interrupted after a refresh."""
    state = modelling_state()
    if workflow_phase != "modelling":
        state["interruption_checked"] = False
        return
    if state.get("interruption_checked"):
        return
    if has_active_modelling_thread():
        state["interruption_checked"] = True
        return

    mark_modelling_interrupted("The previous modelling run was interrupted.")
    state["interruption_checked"] = True


def reset_review_ui() -> None:
    """Clear frontend-only review UI state."""
    state = ui_state()
    state["review_section"] = "summary_metrics"
    state["review_model_id"] = None
    state["review_gate_pending"] = False
    state["review_opening_attempted_for"] = None
    state["chat_feedback"]["review"] = None
    state["chat_retry_messages"]["review"] = None
    state["chat_failure_counts"]["review"] = 0


def bump_token_refresh_nonce() -> None:
    """Trigger a token-list force refresh on the next configuration render."""
    ui_state()["token_force_refresh_next"] = True


def token_refresh_nonce() -> int:
    """Return the current token refresh nonce."""
    force_refresh = bool(ui_state().get("token_force_refresh_next"))
    ui_state()["token_force_refresh_next"] = False
    return int(force_refresh)


def _modelling_worker(
    *,
    event_queue: queue.Queue[dict[str, Any]],
    output_dir: Path,
    force_refresh_prices: bool,
    cancel_event: threading.Event,
) -> None:
    result = run_active_modelling(
        progress_callback=lambda event: event_queue.put({"kind": "progress", "payload": event}),
        cancel_check=cancel_event.is_set,
        force_refresh_prices=force_refresh_prices,
        output_dir=output_dir,
    )
    event_queue.put({"kind": "result", "payload": result})


def _artifacts_for_export(result: dict[str, Any]) -> list[dict[str, Any]]:
    output_dir = Path(str(result.get("output_dir") or ""))
    rows: list[dict[str, Any]] = []
    for artifact in result.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        row = dict(artifact)
        path = row.get("path")
        if isinstance(path, str) and path:
            row["source_path"] = str(output_dir / path)
        rows.append(row)
    return rows


def _cleanup_temp_output_dir(path_value: str | None) -> None:
    if not path_value:
        return
    path = Path(path_value)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _is_cancelled_result(result: dict[str, Any]) -> bool:
    if result.get("cancelled") is True:
        return True
    for error in result.get("errors", []):
        if isinstance(error, dict) and error.get("code") == "modelling_cancelled":
            return True
    return False


def _reset_run_tracking(*, keep_result: bool) -> None:
    state = modelling_state()
    result = state.get("result") if keep_result else None
    state.update(
        {
            "status": "idle",
            "thread": None,
            "queue": None,
            "cancel_event": None,
            "progress_events": [],
            "result": result,
            "output_dir": None,
            "started_at": None,
            "cancel_requested": False,
            "export_prepared": False,
            "interruption_checked": False,
        }
    )
