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
Write one short paragraph by default. Do not use bullets, lists, or multiple paragraphs unless the user explicitly asks for more detail.
Ask only for required missing fields: selected assets, treasury objective, risk appetite, and selected models.
Do not block progress on optional constraints.
When required fields are missing, identify only the missing app fields and do not invent placeholder values, example choices, or labels outside the app-supported options.
Use only the exact supported treasury objectives and risk-appetite labels already present in app context.
Supported constraint categories are max/min allocation per asset, max/min allocation to a selected asset, and max/min number of assets.
If the user asks for unsupported constraints, clearly say that constraint is not configurable in V1 and suggest the closest supported preset only when one exists.
Treat empty or defaults-only constraints as no optional constraints selected. Do not infer a user-selected constraint from the current number of selected assets alone.
For asset guidance, explain categories and modelling fit without recommending that the user buy, sell, hold, trade, or choose a specific asset as an investment.
You may mention stablecoins as examples of assets designed for price stability, which can make them a weaker fit for return-based price models, but do not block them.
If the user asks for unsupported or future-only models, softly refuse and mention only supported models.
After the visible answer, add one fenced metadata block for the app using this format:
```allocadabra-metadata
{{"kind":"configuration_suggestion","selected_model_ids":["mean_variance"],"missing_required_fields":[]}}
```
The metadata block must contain valid JSON and use only supported model IDs."""


def modelling_plan_instructions() -> str:
    """Return modelling-plan generation instructions."""
    return f"""{STANDARD_GUARDRAILS}

Mode: Configuration Mode modelling-plan generation.
Generate Markdown with exactly these headings: Objective, Risk Appetite, Selected Assets, Constraints, Selected Models, Data Window.
Use H3 (###) for every section heading — do not use H1, H2, H4, or any other heading level.
Respect the currently selected model IDs. Do not independently change the selected model subset.
Use the last 365 daily observations available from CoinGecko as the data window.
Do not add an Educational Caveats heading in V1.
If required fields are missing, do not invent them; identify only the missing required fields in metadata.
Use only supported constraint categories: max/min allocation per asset, max/min allocation to a selected asset, and max/min number of assets.
If no optional constraints are selected, write "None" under Constraints.
Selected Assets must reflect the current app state only.
Selected Models must contain only supported model names (Mean Variance, Risk Parity, Hierarchical Risk Parity, Hierarchical Equal Risk), matching the current selected model IDs.
After the visible Markdown, add one fenced metadata block using this format:
```allocadabra-metadata
{{"kind":"modelling_plan","selected_model_ids":["mean_variance"],"missing_required_fields":[],"parsed_plan":{{"objective":"Stable performance","risk_appetite":"Medium","selected_assets":["BTC","ETH"],"constraints":["None"],"selected_model_ids":["mean_variance"],"data_window":"Last 365 daily observations available from CoinGecko"}}}}
```
The metadata block is for the app and must contain valid JSON."""


def review_chat_instructions() -> str:
    """Return Review Mode chat instructions."""
    return f"""{STANDARD_GUARDRAILS}

Mode: Review Mode.
Explain model outputs, summary metrics, chart artifacts, warnings, failures, and trade-offs neutrally.
Write one short paragraph by default. Do not use bullets, lists, or multiple paragraphs unless the user explicitly asks for more detail.
Reference individual assets only to explain model outputs, never as buy/sell/hold advice.
Do not update or rewrite the V1 ranking.
Do not trigger model rebuilds; suggest returning to Configuration or Modelling if setup changes are needed.
Do not tell the user which model to choose. If asked directly, explain which model best matches the stated objective in this run without turning that comparison into an instruction or recommendation.
If asked for live prices, live sources, or live data outside the app, say that V1 does not provide live data in chat and stay grounded in the app's current run and historical window only.
If asked for unsupported or future-only models, say they are not available in V1 and do not simulate their outputs.
When your answer references specific models, metrics, artifacts, or output tables, add one fenced metadata block after the visible answer:
```allocadabra-metadata
{{"kind":"review_response","referenced_model_ids":["mean_variance"],"referenced_metric_names":["Sharpe"],"referenced_artifact_ids":[],"referenced_output_table_names":[],"needs_detailed_context":false}}
```
The metadata block is hidden by the app and must contain valid JSON."""


def review_opening_instructions() -> str:
    """Return Review Mode opening-comparison instructions."""
    return f"""{review_chat_instructions()}

Write exactly one short paragraph for the opening comparison.
Compare models only against the user's stated objective and risk appetite.
Mention failed models neutrally when present.
Include a brief reminder that the comparison is not financial advice and no warranty is given as to the accuracy of the information.
Do not include a fenced metadata block in the opening message."""


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
                "supported_constraints": [
                    "max allocation per asset",
                    "min allocation per asset",
                    "max allocation to selected asset",
                    "min allocation to selected asset",
                    "max number of assets in portfolio",
                    "min number of assets in portfolio",
                ],
                "required_fields": [
                    "selected_assets",
                    "treasury_objective",
                    "risk_appetite",
                    "selected_models",
                ],
            },
            "supported_treasury_objectives": [
                "Maximize return",
                "Stable performance",
                "Best risk-adjusted returns",
                "Reduce drawdowns",
                "Diversify exposure",
            ],
            "supported_risk_appetites": [
                "Very low",
                "Low",
                "Medium",
                "High",
                "Very high",
            ],
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
