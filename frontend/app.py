"""Single-page Streamlit app for Allocadabra."""

from __future__ import annotations

import streamlit as st

from app.storage import get_active_workflow
from frontend.chat import render_chat_panel
from frontend.configuration import render_configuration_panel
from frontend.modelling import render_modelling_page
from frontend.review import render_review_page
from frontend.runtime import drain_modelling_updates, ensure_interrupted_state, init_ui_state, modelling_state, review_gate_pending
from frontend.theme import apply_theme, render_footer, render_mobile_overlay


def main() -> None:
    """Render the single-base-url Streamlit application."""
    st.set_page_config(
        page_title="Allocadabra",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_ui_state()
    drain_modelling_updates()
    workflow = get_active_workflow()
    st.session_state["allocadabra_workflow_snapshot"] = workflow
    ensure_interrupted_state(str(workflow.get("phase", "configuration")))
    workflow = get_active_workflow()
    st.session_state["allocadabra_workflow_snapshot"] = workflow

    phase = _resolve_phase(workflow)
    apply_theme(phase)
    render_mobile_overlay()

    if phase == "configuration":
        chat_col, config_col = st.columns([0.92, 1.08], gap="large")
        with chat_col:
            render_chat_panel(mode="configuration", workflow=workflow)
        with config_col:
            render_configuration_panel(workflow)
    elif phase == "modelling":
        render_modelling_page(workflow)
    else:
        render_review_page(workflow)

    render_footer()


def _resolve_phase(workflow: dict[str, object]) -> str:
    run_state = modelling_state()
    workflow_phase = str(workflow.get("phase", "configuration"))
    if workflow_phase == "review" and review_gate_pending():
        return "modelling"
    if workflow_phase in {"modelling", "interrupted", "review"}:
        return "review" if workflow_phase == "review" else "modelling"
    if run_state.get("status") in {"running", "failed", "review_ready"}:
        return "modelling"
    return "configuration"


if __name__ == "__main__":
    main()
