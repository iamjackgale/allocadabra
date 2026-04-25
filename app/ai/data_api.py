"""Frontend-callable AI orchestration functions."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Protocol

from app.ai.constants import (
    FIXED_FINANCIAL_ADVICE_REFUSAL,
    GENERIC_SAFE_ERROR,
    PROVIDER_UNAVAILABLE_ERROR,
)
from app.ai.context_selection import select_review_detailed_context
from app.ai.errors import AIIntegrationError, MissingAPIKeyError
from app.ai.models import display_name_for_model_id, normalize_selected_model_ids
from app.ai.parsing import split_visible_text_and_metadata
from app.ai.prompts import (
    build_configuration_input,
    build_modelling_plan_input,
    build_review_input,
    build_review_opening_input,
    configuration_chat_instructions,
    modelling_plan_instructions,
    review_chat_instructions,
    review_opening_instructions,
)
from app.ai.provider import AIProviderResponse, PerplexityProvider
from app.ai.session_hooks import append_chat_message, get_chat_messages
from app.ai.validation import (
    looks_like_financial_advice,
    user_requests_direct_model_choice,
    user_requests_financial_advice,
    user_requests_live_data,
    user_requests_unsupported_model,
    validate_modelling_plan,
    validate_review_metadata,
    validate_suggested_model_metadata,
)
from app.storage.session_state import get_workflow_state, store_generated_plan
from app.storage.validation import RISK_APPETITES, TREASURY_OBJECTIVES, validate_configuration_inputs


logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    """Protocol for injectable AI providers in tests or alternate runtimes."""

    def complete(
        self,
        *,
        instructions: str,
        input_text: str,
        max_output_tokens: int = 1200,
    ) -> AIProviderResponse:
        """Return a model response."""


def send_configuration_chat(
    user_message: str,
    *,
    active_inputs: dict[str, Any] | None = None,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Send one Configuration Mode user chat message."""
    append_chat_message("configuration", "user", user_message)
    state = get_workflow_state()
    inputs = active_inputs or state.get("user_inputs", {})
    recent_messages = get_chat_messages("configuration", limit=8)

    early_response = _configuration_precheck_response(user_message=user_message, active_inputs=inputs)
    if early_response is not None:
        return early_response

    return _complete_chat_turn(
        mode="configuration",
        provider=provider,
        instructions=configuration_chat_instructions(),
        input_text=build_configuration_input(
            user_message=user_message,
            active_inputs=inputs,
            recent_messages=recent_messages,
        ),
        fallback_metadata=_configuration_fallback_metadata(inputs),
    )


def generate_modelling_plan(
    *,
    active_inputs: dict[str, Any] | None = None,
    latest_user_message: str | None = None,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Generate, validate, and store an AI modelling plan."""
    state = get_workflow_state()
    inputs = dict(active_inputs or state.get("user_inputs", {}))
    inputs["selected_models"] = normalize_selected_model_ids(inputs.get("selected_models"))

    deterministic = validate_configuration_inputs(inputs)
    if not deterministic.valid:
        logger.info("Blocked modelling-plan generation due to deterministic validation")
        return {
            "ok": False,
            "code": "invalid_configuration",
            "message": "The configuration must be completed before generating a modelling plan.",
            "issues": [asdict(issue) for issue in deterministic.issues],
        }

    try:
        response = _provider(provider).complete(
            instructions=modelling_plan_instructions(),
            input_text=build_modelling_plan_input(
                active_inputs=inputs,
                latest_user_message=latest_user_message,
            ),
            max_output_tokens=1600,
        )
        markdown, metadata = split_visible_text_and_metadata(response.text)
    except MissingAPIKeyError as exc:
        return _error_response("missing_api_key", str(exc))
    except (AIIntegrationError, ValueError) as exc:
        logger.warning("AI modelling-plan generation failed: %s", exc)
        return _error_response("provider_unavailable", PROVIDER_UNAVAILABLE_ERROR)

    if looks_like_financial_advice(markdown):
        logger.warning("Discarded modelling plan because it looked like financial advice")
        return _error_response("unsafe_response", FIXED_FINANCIAL_ADVICE_REFUSAL)

    validation = validate_modelling_plan(markdown, metadata, active_inputs=inputs)
    if not validation.valid:
        append_chat_message("configuration", "assistant", markdown)
        return {
            "ok": False,
            "code": "invalid_metadata",
            "message": GENERIC_SAFE_ERROR,
            "markdown": markdown,
            "metadata": {},
            "issues": validation.issues,
        }

    store_generated_plan(markdown=markdown, metadata=validation.metadata)
    workflow = append_chat_message(
        "configuration",
        "assistant",
        markdown,
        metadata={"kind": "modelling_plan", **validation.metadata},
    )
    return {
        "ok": True,
        "markdown": markdown,
        "metadata": validation.metadata,
        "workflow": workflow,
    }


def import_modelling_plan(
    markdown: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and store a pasted modelling plan."""
    try:
        visible_markdown, parsed_metadata = split_visible_text_and_metadata(markdown)
    except ValueError as exc:
        logger.info("Rejected pasted modelling plan metadata: %s", exc)
        return {
            "ok": False,
            "code": "invalid_plan_metadata",
            "message": "The pasted modelling plan metadata is not valid JSON.",
            "issues": [str(exc)],
        }

    plan_metadata = metadata or parsed_metadata
    validation = validate_modelling_plan(visible_markdown, plan_metadata)

    if looks_like_financial_advice(visible_markdown):
        return _error_response("unsafe_response", FIXED_FINANCIAL_ADVICE_REFUSAL)

    if not validation.valid:
        return {
            "ok": False,
            "code": "invalid_plan",
            "message": "The pasted modelling plan is incomplete or invalid.",
            "issues": validation.issues,
        }

    store_generated_plan(markdown=visible_markdown, metadata=validation.metadata)
    workflow = append_chat_message(
        "configuration",
        "assistant",
        visible_markdown,
        metadata={"kind": "imported_modelling_plan", **validation.metadata},
    )
    return {
        "ok": True,
        "markdown": visible_markdown,
        "metadata": validation.metadata,
        "workflow": workflow,
    }


def send_review_chat(
    user_message: str,
    *,
    model_output_summary: dict[str, Any] | None = None,
    visible_context: dict[str, Any] | None = None,
    detailed_context: dict[str, Any] | None = None,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Send one Review Mode user chat message."""
    state = get_workflow_state()
    if state.get("phase") != "review":
        return _error_response(
            "review_not_ready",
            "Review Mode is available only after modelling outputs are ready.",
        )

    append_chat_message("review", "user", user_message)
    recent_messages = get_chat_messages("review", limit=8)

    early_response = _review_precheck_response(user_message=user_message)
    if early_response is not None:
        return early_response

    selected_detailed_context = select_review_detailed_context(
        user_message=user_message,
        visible_context=visible_context,
        available_detailed_context=detailed_context,
    )

    return _complete_chat_turn(
        mode="review",
        provider=provider,
        instructions=review_chat_instructions(),
        input_text=build_review_input(
            user_message=user_message,
            workflow_state=state,
            model_output_summary=model_output_summary,
            visible_context=visible_context,
            detailed_context=selected_detailed_context,
            recent_messages=recent_messages,
        ),
    )


def generate_review_opening(
    *,
    ranking_summary: dict[str, Any],
    model_output_summary: dict[str, Any],
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Generate and store the first Review Mode comparison message."""
    state = get_workflow_state()
    if state.get("phase") != "review":
        return _error_response(
            "review_not_ready",
            "Review Mode is available only after modelling outputs are ready.",
        )

    try:
        response = _provider(provider).complete(
            instructions=review_opening_instructions(),
            input_text=build_review_opening_input(
                workflow_state=state,
                ranking_summary=ranking_summary,
                model_output_summary=model_output_summary,
            ),
            max_output_tokens=900,
        )
    except MissingAPIKeyError as exc:
        return _error_response("missing_api_key", str(exc))
    except AIIntegrationError as exc:
        logger.warning("AI review opening failed: %s", exc)
        return _error_response("provider_unavailable", PROVIDER_UNAVAILABLE_ERROR)

    message, metadata = split_visible_text_and_metadata(response.text)
    if looks_like_financial_advice(message):
        message = FIXED_FINANCIAL_ADVICE_REFUSAL
        metadata = {}

    validation = validate_review_metadata(metadata)
    opening_metadata = {**validation.metadata, "kind": "review_opening"} if validation.valid else {"kind": "review_opening"}
    append_chat_message("review", "assistant", message, metadata=opening_metadata)
    return {"ok": True, "message": message}


def get_fixed_financial_advice_refusal() -> str:
    """Return the standard fixed no-financial-advice refusal."""
    return FIXED_FINANCIAL_ADVICE_REFUSAL


def get_generic_safe_error() -> str:
    """Return the generic safe error message for unusable AI output."""
    return GENERIC_SAFE_ERROR


def _complete_chat_turn(
    *,
    mode: str,
    provider: AIProvider | None,
    instructions: str,
    input_text: str,
    fallback_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        response = _provider(provider).complete(
            instructions=instructions,
            input_text=input_text,
            max_output_tokens=1000,
        )
        message, metadata = split_visible_text_and_metadata(response.text)
    except MissingAPIKeyError as exc:
        return _error_response("missing_api_key", str(exc))
    except (AIIntegrationError, ValueError) as exc:
        logger.warning("AI chat turn failed: %s", exc)
        return _error_response("provider_unavailable", PROVIDER_UNAVAILABLE_ERROR)

    if looks_like_financial_advice(message):
        message = FIXED_FINANCIAL_ADVICE_REFUSAL
        metadata = {}

    validation = (
        validate_review_metadata(metadata)
        if mode == "review"
        else validate_suggested_model_metadata(metadata)
    )
    if not validation.valid:
        append_chat_message(mode, "assistant", message)
        return {
            "ok": False,
            "code": "invalid_metadata",
            "message": GENERIC_SAFE_ERROR,
            "assistant_message": message,
            "issues": validation.issues,
        }

    metadata = validation.metadata or dict(fallback_metadata or {})
    append_chat_message(mode, "assistant", message, metadata=metadata)
    return {
        "ok": True,
        "message": message,
        "metadata": metadata,
        "workflow": get_workflow_state(),
    }


def _provider(provider: AIProvider | None) -> AIProvider:
    return provider or PerplexityProvider()


def _error_response(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "code": code, "message": message}


def _configuration_fallback_metadata(active_inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "configuration_suggestion",
        "selected_model_ids": normalize_selected_model_ids(active_inputs.get("selected_models")),
        "missing_required_fields": _missing_required_fields(active_inputs),
    }


def _missing_required_fields(active_inputs: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if len(active_inputs.get("selected_assets") or []) < 2:
        missing.append("selected_assets")
    if active_inputs.get("treasury_objective") not in TREASURY_OBJECTIVES:
        missing.append("treasury_objective")
    if active_inputs.get("risk_appetite") not in RISK_APPETITES:
        missing.append("risk_appetite")
    if not normalize_selected_model_ids(active_inputs.get("selected_models")):
        missing.append("selected_models")
    return missing


def _configuration_precheck_response(
    *,
    user_message: str,
    active_inputs: dict[str, Any],
) -> dict[str, Any] | None:
    if _looks_like_configuration_readiness_check(user_message):
        return _store_safe_configuration_reply(
            _configuration_readiness_reply(active_inputs),
            active_inputs=active_inputs,
        )
    if user_requests_financial_advice(user_message):
        return _store_safe_configuration_reply(FIXED_FINANCIAL_ADVICE_REFUSAL, active_inputs=active_inputs)
    if user_requests_direct_model_choice(user_message):
        return _store_safe_configuration_reply(
            "I cannot tell you which model to choose. I can compare the supported models in educational terms and explain how Mean Variance, Risk Parity, and Hierarchical Risk Parity differ so you can decide within the app.",
            active_inputs=active_inputs,
        )
    if user_requests_live_data(user_message):
        return _store_safe_configuration_reply(
            "Configuration Mode does not provide live market data in chat. It uses the app's historical 365-day daily observation window, so I can help with setup choices but not live price feeds.",
            active_inputs=active_inputs,
        )
    if user_requests_unsupported_model(user_message):
        return _store_safe_configuration_reply(
            "That model is not supported in V1. Allocadabra currently supports Mean Variance, Risk Parity, and Hierarchical Risk Parity only.",
            active_inputs=active_inputs,
        )
    return None


def _review_precheck_response(*, user_message: str) -> dict[str, Any] | None:
    if user_requests_financial_advice(user_message):
        return _store_safe_review_reply(FIXED_FINANCIAL_ADVICE_REFUSAL)
    if user_requests_direct_model_choice(user_message):
        return _store_safe_review_reply(
            "I cannot tell you which model to choose. I can explain which supported model best matches your stated objective and risk appetite in this run, and why, without turning that comparison into a recommendation."
        )
    if user_requests_live_data(user_message):
        return _store_safe_review_reply(
            "V1 chat cannot provide live CoinGecko price data. I can only discuss the app's current run, its historical 365-day data window, and the generated review outputs already visible in the app."
        )
    if user_requests_unsupported_model(user_message):
        return _store_safe_review_reply(
            "That model is not available in V1. This app currently supports Mean Variance, Risk Parity, and Hierarchical Risk Parity only, and I cannot simulate unsupported model outputs in chat."
        )
    return None


def _store_safe_configuration_reply(message: str, *, active_inputs: dict[str, Any]) -> dict[str, Any]:
    metadata = _configuration_fallback_metadata(active_inputs)
    workflow = append_chat_message("configuration", "assistant", message, metadata=metadata)
    return {"ok": True, "message": message, "metadata": metadata, "workflow": workflow}


def _store_safe_review_reply(message: str) -> dict[str, Any]:
    metadata = {"kind": "review_response", "referenced_model_ids": [], "referenced_metric_names": [], "referenced_artifact_ids": [], "referenced_output_table_names": [], "needs_detailed_context": False}
    workflow = append_chat_message("review", "assistant", message, metadata=metadata)
    return {"ok": True, "message": message, "metadata": metadata, "workflow": workflow}


def _looks_like_configuration_readiness_check(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "ready to model",
            "ready to run",
            "can i run a model",
            "can i run this",
            "can i run with what i have",
            "is this ready",
            "does my configuration look ready",
        )
    )


def _configuration_readiness_reply(active_inputs: dict[str, Any]) -> str:
    missing_fields = _missing_required_fields(active_inputs)
    model_names = ", ".join(
        display_name_for_model_id(model_id)
        for model_id in normalize_selected_model_ids(active_inputs.get("selected_models"))
    )
    assets = ", ".join(str(asset.get("name") or asset.get("symbol") or asset) for asset in active_inputs.get("selected_assets") or [])
    objective = str(active_inputs.get("treasury_objective") or "not set")
    risk = str(active_inputs.get("risk_appetite") or "not set")
    constraints_summary = _effective_constraint_summary(active_inputs)

    if missing_fields:
        labels = {
            "selected_assets": "at least 2 selected assets",
            "treasury_objective": "a treasury objective",
            "risk_appetite": "a risk appetite",
            "selected_models": "at least 1 supported model",
        }
        missing_text = ", ".join(labels[field] for field in missing_fields)
        return (
            "Not yet. To run a model, the current setup still needs "
            f"{missing_text}. Right now the selected assets are {assets or 'not set'}, "
            f"the treasury objective is {objective}, the risk appetite is {risk}, "
            f"and the selected supported models are {model_names or 'not set'}."
        )

    return (
        "Yes. From a technical perspective, this configuration is ready to model: "
        f"selected assets {assets}, treasury objective {objective}, risk appetite {risk}, "
        f"selected supported models {model_names}, and {constraints_summary}."
    )


def _effective_constraint_summary(active_inputs: dict[str, Any]) -> str:
    constraints = dict(active_inputs.get("constraints") or {})
    selected_assets = list(active_inputs.get("selected_assets") or [])
    selected_asset_count = len(selected_assets)

    global_min = constraints.get("global_min_allocation_percent")
    global_max = constraints.get("global_max_allocation_percent")
    min_assets = constraints.get("min_assets_in_portfolio")
    max_assets = constraints.get("max_assets_in_portfolio")
    selected_asset_min = constraints.get("selected_asset_min_allocation")
    selected_asset_max = constraints.get("selected_asset_max_allocation")

    defaults_only = (
        global_min in (None, 0)
        and global_max in (None, 100)
        and min_assets in (None, 0)
        and max_assets in (None, 0, selected_asset_count)
        and selected_asset_min in (None, {})
        and selected_asset_max in (None, {})
    )
    if defaults_only:
        return "no additional optional constraints selected"

    return "supported optional constraints applied"
