"""Reusable chat panel for Configuration and Review phases."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.ai.data_api import (
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

_GREETING = "Hello, I'm Perplexity. Let's talk about asset allocation modelling. How can I help you?"


def render_chat_panel(
    *,
    mode: str,
    workflow: dict[str, Any],
    model_output_summary: dict[str, Any] | None = None,
    visible_context: dict[str, Any] | None = None,
    detailed_context: dict[str, Any] | None = None,
) -> None:
    """Render one reusable phase-aware chat panel."""
    messages = workflow.get("chat_sessions", {}).get(mode, [])
    messages = messages if isinstance(messages, list) else []

    st.markdown('<div class="alloca-phase">AI ASSISTANT</div>', unsafe_allow_html=True)

    feedback = get_chat_feedback(mode)
    if feedback:
        st.info(feedback)

    chat_disabled = chat_failure_count(mode) >= 3

    history = st.container(height=560)
    with history:
        if not messages:
            with st.chat_message("assistant"):
                st.markdown(_GREETING)
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

    prompt = st.chat_input(
        "Ask the AI about your model.",
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


def _looks_like_modelling_plan(prompt: str) -> bool:
    lowered = prompt.lower()
    required = [
        "### objective",
        "### risk appetite",
        "### selected assets",
        "### constraints",
        "### selected models",
        "### data window",
    ]
    return all(heading in lowered for heading in required)
