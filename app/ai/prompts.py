"""Prompt builders for Configuration and Review AI modes."""

from __future__ import annotations

import json
from typing import Any

from app.ai.constants import STANDARD_GUARDRAILS
from app.ai.models import supported_models_for_prompt


def configuration_chat_instructions() -> str:
    """Return Configuration Mode chat instructions."""
    return f"""{STANDARD_GUARDRAILS}

Mode: Configuration Mode.
Help with asset selection, treasury objective clarification, risk appetite clarification, supported constraints, technical app-use questions, and modelling-plan preparation.
Do not receive or discuss model outputs.
Do not directly mutate app state. Suggest changes the user can apply.
If the user asks for unsupported models, softly refuse and mention only supported models."""


def modelling_plan_instructions() -> str:
    """Return modelling-plan generation instructions."""
    return f"""{STANDARD_GUARDRAILS}

Mode: Configuration Mode modelling-plan generation.
Generate Markdown with exactly these headings: Objective, Risk Appetite, Selected Assets, Constraints, Selected Models, Data Window.
Respect the currently selected model IDs. Do not independently change the selected model subset.
Use the last 365 daily observations available from CoinGecko as the data window.
Do not add an Educational Caveats heading in V1.
After the visible Markdown, add one fenced metadata block using this format:
```allocadabra-metadata
{{"kind":"modelling_plan","selected_model_ids":["mean_variance"],"missing_required_fields":[]}}
```
The metadata block is for the app and must contain valid JSON."""


def review_chat_instructions() -> str:
    """Return Review Mode chat instructions."""
    return f"""{STANDARD_GUARDRAILS}

Mode: Review Mode.
Explain model outputs, summary metrics, chart artifacts, warnings, failures, and trade-offs neutrally.
Reference individual assets only to explain model outputs, never as buy/sell/hold advice.
Do not update or rewrite the V1 ranking.
Do not trigger model rebuilds; suggest returning to Configuration or Modelling if setup changes are needed."""


def review_opening_instructions() -> str:
    """Return Review Mode opening-comparison instructions."""
    return f"""{review_chat_instructions()}

Write a short neutral opening comparison in chat.
Compare models only against the user's stated objective and risk appetite.
Mention failed models neutrally when present.
Include a brief reminder that the comparison is not financial advice and no warranty is given as to the accuracy of the information."""


def build_configuration_input(
    *,
    user_message: str,
    active_inputs: dict[str, Any],
    recent_messages: list[dict[str, Any]],
) -> str:
    """Build Configuration Mode input context."""
    return _json_context(
        {
            "latest_user_message": user_message,
            "active_user_inputs": active_inputs,
            "recent_configuration_chat": _message_context(recent_messages),
            "supported_models": supported_models_for_prompt(),
            "app_constraints": {
                "min_assets": 2,
                "max_assets": 10,
                "max_compared_models": 3,
                "data_window": "last 365 daily observations available from CoinGecko",
                "minimum_valid_daily_prices": 90,
            },
        }
    )


def build_modelling_plan_input(
    *,
    active_inputs: dict[str, Any],
    latest_user_message: str | None = None,
) -> str:
    """Build modelling-plan generation input context."""
    return _json_context(
        {
            "latest_relevant_user_message": latest_user_message,
            "active_user_inputs": active_inputs,
            "supported_models": supported_models_for_prompt(),
            "required_markdown_headings": [
                "Objective",
                "Risk Appetite",
                "Selected Assets",
                "Constraints",
                "Selected Models",
                "Data Window",
            ],
        }
    )


def build_review_input(
    *,
    user_message: str,
    workflow_state: dict[str, Any],
    model_output_summary: dict[str, Any] | None,
    visible_context: dict[str, Any] | None,
    detailed_context: dict[str, Any] | None,
    recent_messages: list[dict[str, Any]],
) -> str:
    """Build Review Mode chat input context."""
    return _json_context(
        {
            "latest_user_message": user_message,
            "confirmed_modelling_plan": workflow_state.get("modelling_plan", {}),
            "user_preferences": workflow_state.get("user_inputs", {}),
            "model_output_summary": model_output_summary or {},
            "visible_review_context": visible_context or {},
            "detailed_context": detailed_context or {},
            "recent_review_chat": _message_context(recent_messages),
        }
    )


def build_review_opening_input(
    *,
    workflow_state: dict[str, Any],
    ranking_summary: dict[str, Any],
    model_output_summary: dict[str, Any],
) -> str:
    """Build Review Mode opening-comparison context."""
    return _json_context(
        {
            "confirmed_modelling_plan": workflow_state.get("modelling_plan", {}),
            "user_preferences": workflow_state.get("user_inputs", {}),
            "deterministic_ranking_summary": ranking_summary,
            "model_output_summary": model_output_summary,
        }
    )


def _json_context(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2, default=str)


def _message_context(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"role": str(message.get("role", "")), "content": str(message.get("content", ""))}
        for message in messages
    ]
