"""Reusable chat panel for Configuration and Review phases."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.ai.data_api import (
    generate_review_opening,
    import_modelling_plan,
    send_configuration_chat,
    send_review_chat,
)
from frontend.runtime import (
    chat_failure_count,
    clear_chat_failure,
    get_chat_feedback,
    register_chat_failure,
    retry_message_for,
)


def render_chat_panel(
    *,
    mode: str,
    workflow: dict[str, Any],
    model_output_summary: dict[str, Any] | None = None,
    visible_context: dict[str, Any] | None = None,
    detailed_context: dict[str, Any] | None = None,
    opening_summary: dict[str, Any] | None = None,
) -> None:
    """Render one reusable phase-aware chat panel."""
    messages = workflow.get("chat_sessions", {}).get(mode, [])
    messages = messages if isinstance(messages, list) else []

    st.markdown('<div class="alloca-panel">', unsafe_allow_html=True)
    st.markdown("#### AI chat")
    st.caption(
        "Ask about setup choices during Configuration, or ask about visible outputs during Review."
        if mode == "configuration"
        else "Ask follow-up questions about the current portfolio outputs and trade-offs."
    )

    feedback = get_chat_feedback(mode)
    if feedback:
        st.info(feedback)

    chat_disabled = chat_failure_count(mode) >= 3

    if mode == "review" and not messages and opening_summary:
        _ensure_review_opening(opening_summary, model_output_summary or {})
        st.rerun()

    history = st.container(height=560)
    with history:
        for message in messages:
            role = str(message.get("role") or "assistant")
            with st.chat_message(role):
                st.markdown(str(message.get("content", "")))

    retry_message = retry_message_for(mode)
    if retry_message:
        retry_col, _ = st.columns([1, 3])
        with retry_col:
            if st.button("Retry last message", key=f"{mode}_retry", width="stretch", disabled=chat_disabled):
                with st.spinner("Waiting for AI response..."):
                    _submit_message(
                        mode=mode,
                        prompt=retry_message,
                        model_output_summary=model_output_summary,
                        visible_context=visible_context,
                        detailed_context=detailed_context,
                    )
                st.rerun()

    placeholder = (
        "Ask about supported assets, constraints, or your modelling plan."
        if mode == "configuration"
        else "Ask about the current outputs, metrics, or visible chart."
    )
    prompt = st.chat_input(
        placeholder,
        key=f"{mode}_chat_input",
        height=88,
        disabled=chat_disabled,
    )
    if prompt:
        with st.spinner("Waiting for AI response..."):
            _submit_message(
                mode=mode,
                prompt=prompt,
                model_output_summary=model_output_summary,
                visible_context=visible_context,
                detailed_context=detailed_context,
            )
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _submit_message(
    *,
    mode: str,
    prompt: str,
    model_output_summary: dict[str, Any] | None,
    visible_context: dict[str, Any] | None,
    detailed_context: dict[str, Any] | None,
) -> None:
    if mode == "configuration":
        if _looks_like_modelling_plan(prompt):
            result = import_modelling_plan(prompt)
        else:
            result = send_configuration_chat(prompt)
    else:
        result = send_review_chat(
            prompt,
            model_output_summary=model_output_summary,
            visible_context=visible_context,
            detailed_context=detailed_context,
        )

    if result.get("ok"):
        clear_chat_failure(mode)
        return

    retry_prompt = prompt if mode in {"configuration", "review"} else None
    register_chat_failure(
        mode,
        str(result.get("message", "The AI request could not be completed.")),
        retry_prompt,
    )


def _ensure_review_opening(
    ranking_summary: dict[str, Any],
    model_output_summary: dict[str, Any],
) -> None:
    result = generate_review_opening(
        ranking_summary=ranking_summary,
        model_output_summary=model_output_summary,
    )
    if not result.get("ok"):
        register_chat_failure(
            "review",
            str(result.get("message", "The Review opening could not be generated.")),
            None,
        )


def _looks_like_modelling_plan(prompt: str) -> bool:
    lowered = prompt.lower()
    required = [
        "## objective",
        "## risk appetite",
        "## selected assets",
        "## constraints",
        "## selected models",
        "## data window",
    ]
    return all(heading in lowered for heading in required)
