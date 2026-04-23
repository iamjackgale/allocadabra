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
from app.ai.models import normalize_selected_model_ids
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
    validate_modelling_plan,
    validate_review_metadata,
    validate_suggested_model_metadata,
)
from app.storage.session_state import get_workflow_state, store_generated_plan
from app.storage.validation import validate_configuration_inputs


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

    return _complete_chat_turn(
        mode="configuration",
        provider=provider,
        instructions=configuration_chat_instructions(),
        input_text=build_configuration_input(
            user_message=user_message,
            active_inputs=inputs,
            recent_messages=recent_messages,
        ),
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

    message = response.text
    if looks_like_financial_advice(message):
        message = FIXED_FINANCIAL_ADVICE_REFUSAL

    append_chat_message("review", "assistant", message, metadata={"kind": "review_opening"})
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

    append_chat_message(mode, "assistant", message, metadata=validation.metadata)
    return {
        "ok": True,
        "message": message,
        "metadata": validation.metadata,
        "workflow": get_workflow_state(),
    }


def _provider(provider: AIProvider | None) -> AIProvider:
    return provider or PerplexityProvider()


def _error_response(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "code": code, "message": message}
