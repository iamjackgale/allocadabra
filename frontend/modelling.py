"""Modelling phase screen and live progress rendering."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.storage import abandon_generated_plan
from frontend.runtime import (
    cancel_modelling_run,
    clear_confirmation,
    clear_modelling_run,
    confirmation_state,
    drain_modelling_updates,
    modelling_elapsed_seconds,
    modelling_state,
    request_confirmation,
    review_gate_pending,
    set_review_gate_pending,
    start_modelling_run,
)


PROGRESS_PHASES = [
    "validation",
    "ingestion",
    "datasets",
    "modelling",
    "analysis",
    "outputs",
]


def render_modelling_page(workflow: dict[str, Any]) -> None:
    """Render the Modelling phase or its recovery/success states."""
    state = modelling_state()

    if workflow.get("phase") == "interrupted":
        _render_interrupted_state()
        return

    if workflow.get("phase") == "review" and review_gate_pending():
        _render_review_gate()
        return

    st.markdown('<div class="alloca-panel">', unsafe_allow_html=True)
    st.markdown('<div class="alloca-phase-center">MODELLING</div>', unsafe_allow_html=True)
    st.caption("Do not close or refresh the app while modelling is active.")

    if state.get("status") in {"running", "cancel_requested"}:
        _render_live_modelling_fragment(workflow)
    else:
        _render_run_result(workflow)

    st.markdown("</div>", unsafe_allow_html=True)


@st.fragment(run_every="1s")
def _render_live_modelling_fragment(workflow: dict[str, Any]) -> None:
    drain_modelling_updates()
    state = modelling_state()
    if state.get("status") == "review_ready":
        st.rerun()

    progress_events = list(state.get("progress_events", []))
    _render_progress(progress_events)
    _render_live_status(progress_events)

    if st.button("Cancel", width="stretch"):
        request_confirmation(
            "cancel_modelling",
            "This abandons the current modelling run, deletes partial outputs, and returns to Configuration with your previous options selected.",
        )
        st.rerun()

    _render_confirmation_panel()
    _render_plan_preview(workflow)


def _render_run_result(workflow: dict[str, Any]) -> None:
    state = modelling_state()
    result = state.get("result") or {}
    progress_events = list(result.get("progress_events") or state.get("progress_events") or [])
    _render_progress(progress_events)
    _render_live_status(progress_events)

    if result.get("errors"):
        st.error(str(result.get("user_message", "Modelling could not be completed.")))
        for error in result.get("errors", []):
            if isinstance(error, dict):
                st.caption(f"- {error.get('message', 'Modelling error')}")
    else:
        st.warning("No models completed successfully. You can retry the run or cancel back to Configuration.")

    cols = st.columns(2)
    with cols[0]:
        if st.button("Retry Run", type="primary", width="stretch"):
            start_modelling_run()
            st.rerun()
    with cols[1]:
        if st.button("Cancel", width="stretch"):
            request_confirmation(
                "cancel_modelling",
                "This abandons the current modelling run, deletes partial outputs, and returns to Configuration with your previous options selected.",
            )

    _render_confirmation_panel()
    _render_plan_preview(workflow)


def _render_progress(progress_events: list[dict[str, Any]]) -> None:
    completed = {
        str(event.get("phase"))
        for event in progress_events
        if event.get("status") == "completed"
    }
    failed = {
        str(event.get("phase"))
        for event in progress_events
        if event.get("status") == "failed"
    }
    current_index = 0
    for index, phase in enumerate(PROGRESS_PHASES):
        if phase in completed:
            current_index = index + 1
        elif phase in failed:
            current_index = index + 1
            break

    st.progress(current_index / len(PROGRESS_PHASES))
    labels = st.columns(len(PROGRESS_PHASES))
    for column, phase in zip(labels, PROGRESS_PHASES):
        with column:
            if phase in failed:
                st.error(phase.title())
            elif phase in completed:
                st.success(phase.title())
            else:
                st.caption(phase.title())


def _render_live_status(progress_events: list[dict[str, Any]]) -> None:
    latest = progress_events[-1]["message"] if progress_events else "Waiting to start."
    dots = "." * ((int(modelling_elapsed_seconds()) % 3) + 1)
    st.markdown(f"### {latest}{dots}")
    st.caption(f"Approximate elapsed time: {_format_elapsed(modelling_elapsed_seconds())}")


def _render_interrupted_state() -> None:
    st.markdown('<div class="alloca-panel">', unsafe_allow_html=True)
    st.markdown('<div class="alloca-phase-center">MODELLING</div>', unsafe_allow_html=True)
    st.warning(
        "The previous modelling run was interrupted. You can return to Configuration with your previous options selected, or restart the run."
    )
    cols = st.columns(2)
    with cols[0]:
        if st.button("Return To Configuration", width="stretch"):
            abandon_generated_plan()
            clear_modelling_run()
            st.rerun()
    with cols[1]:
        if st.button("Restart Run", type="primary", width="stretch"):
            start_modelling_run()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_review_gate() -> None:
    st.markdown('<div class="alloca-panel">', unsafe_allow_html=True)
    st.markdown('<div class="alloca-phase-center">MODELLING</div>', unsafe_allow_html=True)
    st.success("Review artifacts are ready.")
    st.markdown("### Review Results")
    st.caption("Modelling completed. Failed models, if any, will be marked in Review.")
    if st.button("Review Results", type="primary", width="stretch"):
        set_review_gate_pending(False)
        clear_modelling_run()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_plan_preview(workflow: dict[str, Any]) -> None:
    markdown = str(workflow.get("modelling_plan", {}).get("markdown") or "")
    if not markdown:
        return
    with st.expander("Confirmed modelling plan"):
        st.markdown(markdown)


def _render_confirmation_panel() -> None:
    confirmation = confirmation_state()
    if not confirmation or confirmation.get("action") != "cancel_modelling":
        return
    st.warning(confirmation["message"])
    cols = st.columns(2)
    with cols[0]:
        if st.button("Confirm cancellation", type="primary", width="stretch"):
            clear_confirmation()
            cancel_modelling_run()
            st.rerun()
    with cols[1]:
        if st.button("Continue modelling", width="stretch"):
            clear_confirmation()
            st.rerun()


def _format_elapsed(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m {secs:02d}s"
    return f"{minutes:d}m {secs:02d}s"
