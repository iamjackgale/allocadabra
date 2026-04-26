"""Repeatable AI fixture and missing-key checks for Task 129.

Covers deterministic intercepts, guardrails, metadata shape, and context
selection — all without a live Perplexity connection.

Steps:
  1. Missing-key handling: key absent + dotenv suppressed → ok=False, no traceback.
  2. Configuration readiness intercept: deterministic reply without provider call.
  3. Financial advice guardrail: fixed refusal in Review mode.
  4. Unsupported-model intercept: deflection without provider call.
  5. Metadata shape validation: plan and review metadata validators.
  6. Context-selection smoke: narrowing assertions from ai-validation.md.
  7. Cleanup: reset storage state.

Run: uv run python scripts/ai_smoke_extended.py
Expected final line: ai smoke extended ok
"""

from __future__ import annotations

import os
import sys
from typing import Any


def main() -> None:
    _step1_missing_key_handling()
    _step2_configuration_readiness_intercept()
    _step3_financial_advice_guardrail()
    _step4_unsupported_model_intercept()
    _step5_metadata_shape_validation()
    _step6_context_selection_smoke()
    _cleanup()
    print("ai smoke extended ok")


# ---------------------------------------------------------------------------
# Step 1 — missing-key handling
# ---------------------------------------------------------------------------

def _step1_missing_key_handling() -> None:
    import app.ai.provider as provider_module
    from app.ai.data_api import send_configuration_chat
    from app.storage.data_api import update_active_inputs
    from app.storage.session_state import reset_configuration

    # Remove key from env and suppress dotenv so .env file cannot restore it.
    os.environ.pop("PERPLEXITY_API_KEY", None)
    original_loader = provider_module.load_dotenv_if_present
    provider_module.load_dotenv_if_present = lambda *a, **kw: None

    try:
        reset_configuration()
        update_active_inputs({
            "selected_assets": [
                {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
                {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
            ],
            "selected_models": ["mean_variance", "risk_parity"],
            "treasury_objective": "Stable Performance",
            "risk_appetite": "Medium",
        })

        # Use a neutral message that does not trigger any deterministic precheck.
        result = send_configuration_chat("Tell me about diversification across models.")

        assert result.get("ok") is False, (
            f"Expected ok=False with missing key, got: {result}"
        )
        assert isinstance(result.get("message"), str) and result["message"], (
            "Expected non-empty message with missing key error"
        )
        assert "Traceback" not in result["message"], (
            "message contains raw Python traceback text"
        )
    finally:
        # Always restore the original loader, even if assertions fail.
        provider_module.load_dotenv_if_present = original_loader

    reset_configuration()


# ---------------------------------------------------------------------------
# Step 2 — Configuration readiness intercept
# ---------------------------------------------------------------------------

def _step2_configuration_readiness_intercept() -> None:
    from app.ai.data_api import send_configuration_chat
    from app.storage.data_api import update_active_inputs
    from app.storage.session_state import reset_configuration

    reset_configuration()
    update_active_inputs({
        # Only one asset — below the minimum of 2, so selected_assets is missing.
        "selected_assets": [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}],
        "selected_models": ["mean_variance", "risk_parity"],
        # treasury_objective and risk_appetite intentionally absent.
    })

    # "can i run a model" triggers _looks_like_configuration_readiness_check —
    # a deterministic intercept that never reaches the provider.
    result = send_configuration_chat("Can I run a model with what I have set up?")

    assert result.get("ok") is True, (
        f"Readiness intercept expected ok=True, got: {result}"
    )
    metadata = result.get("metadata", {})
    assert metadata.get("kind") == "configuration_suggestion", (
        f"Expected kind='configuration_suggestion', got: {metadata.get('kind')}"
    )
    missing = metadata.get("missing_required_fields", [])
    assert "treasury_objective" in missing, (
        f"treasury_objective not in missing_required_fields: {missing}"
    )
    assert "risk_appetite" in missing, (
        f"risk_appetite not in missing_required_fields: {missing}"
    )

    reset_configuration()


# ---------------------------------------------------------------------------
# Step 3 — Financial advice guardrail in Review mode
# ---------------------------------------------------------------------------

def _step3_financial_advice_guardrail() -> None:
    from app.ai.data_api import get_fixed_financial_advice_refusal, send_review_chat
    from app.storage.session_state import mark_review_ready, reset_configuration

    reset_configuration()
    # Set phase to review with a minimal manifest reference.
    mark_review_ready({"manifest_path": "storage/cache/model-outputs/manifest.json"})

    result = send_review_chat("Should I buy Bitcoin based on these results?")

    assert result.get("ok") is True, (
        f"Financial advice guardrail expected ok=True, got: {result}"
    )
    assert result.get("message") == get_fixed_financial_advice_refusal(), (
        f"Expected fixed financial-advice refusal, got: {result.get('message')!r}"
    )

    reset_configuration()


# ---------------------------------------------------------------------------
# Step 4 — Unsupported-model intercept
# ---------------------------------------------------------------------------

def _step4_unsupported_model_intercept() -> None:
    from app.ai.data_api import get_generic_safe_error, send_configuration_chat
    from app.storage.data_api import update_active_inputs
    from app.storage.session_state import reset_configuration

    reset_configuration()
    update_active_inputs({
        "selected_assets": [
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        ],
        "selected_models": ["mean_variance"],
        "treasury_objective": "Stable Performance",
        "risk_appetite": "Medium",
    })

    # "black-litterman" matches user_requests_unsupported_model — deterministic deflection.
    result = send_configuration_chat("Run Black-Litterman for me.")

    assert result.get("ok") is True, (
        f"Unsupported model intercept expected ok=True, got: {result}"
    )
    message = result.get("message", "")
    # Accept either a deflection (no 'black', or contains 'not supported') or safe error.
    assert (
        "black" not in message.lower()
        or "not supported" in message.lower()
        or message == get_generic_safe_error()
    ), f"Unexpected unsupported-model response: {message!r}"

    reset_configuration()


# ---------------------------------------------------------------------------
# Step 5 — Metadata shape validation
# ---------------------------------------------------------------------------

def _step5_metadata_shape_validation() -> None:
    from app.ai.validation import (
        looks_like_financial_advice,
        validate_modelling_plan,
        validate_review_metadata,
    )

    md = (
        "## Objective\nStable Performance\n"
        "## Risk Appetite\nMedium\n"
        "## Selected Assets\nBTC, ETH\n"
        "## Constraints\nNone\n"
        "## Selected Models\nMean Variance\n"
        "## Data Window\nLast 365 daily observations"
    )

    assert validate_modelling_plan(md, {"selected_model_ids": ["mean_variance"]}).valid is True, (
        "Expected valid plan with mean_variance"
    )
    assert validate_modelling_plan(md, {"selected_model_ids": ["black_litterman"]}).valid is False, (
        "Expected invalid plan with black_litterman"
    )
    assert validate_modelling_plan(md, {"selected_model_ids": ["worst_case"]}).valid is False, (
        "Expected invalid plan with worst_case"
    )

    assert validate_review_metadata({"referenced_model_ids": ["mean_variance"]}).valid is True, (
        "Expected valid review metadata with mean_variance"
    )
    assert validate_review_metadata({"referenced_model_ids": ["hierarchical_equal_risk"]}).valid is False, (
        "Expected invalid review metadata with hierarchical_equal_risk"
    )

    assert looks_like_financial_advice("I recommend buying Bitcoin.") is True, (
        "Expected financial advice detection for 'I recommend buying Bitcoin.'"
    )
    assert looks_like_financial_advice("The portfolio has a Sharpe ratio of 0.72.") is False, (
        "Expected no financial advice detection for neutral string"
    )


# ---------------------------------------------------------------------------
# Step 6 — Context-selection smoke
# ---------------------------------------------------------------------------

def _step6_context_selection_smoke() -> None:
    from app.ai.context_selection import select_review_detailed_context

    # Single-model, single-output-type selection.
    ctx: dict[str, Any] = {
        "models": {
            "mean_variance": {"allocations": [1], "drawdown": [2]},
            "risk_parity": {"allocations": [3]},
        }
    }
    out = select_review_detailed_context(
        user_message="Why do Mean Variance weights differ?",
        visible_context=None,
        available_detailed_context=ctx,
    )
    assert out == {"models": {"mean_variance": {"allocations": [1]}}}, (
        f"Single-model context selection mismatch: {out}"
    )

    # Multi-model comparison: both models, comparison-relevant output types only.
    ctx2: dict[str, Any] = {
        "models": {
            "mean_variance": {
                "summary_metrics": [1],
                "allocations": [2],
                "transformation_metadata": [3],
                "drawdown": [4],
            },
            "risk_parity": {
                "summary_metrics": [5],
                "allocations": [6],
                "transformation_metadata": [7],
            },
        }
    }
    out2 = select_review_detailed_context(
        user_message="Why do Mean Variance and Risk Parity differ?",
        visible_context=None,
        available_detailed_context=ctx2,
    )
    assert set(out2.get("models", {})) == {"mean_variance", "risk_parity"}, (
        f"Multi-model context missing model keys: {set(out2.get('models', {}))}"
    )
    assert set(out2["models"]["mean_variance"]) == {
        "summary_metrics", "allocations", "transformation_metadata"
    }, f"Unexpected mean_variance context keys: {set(out2['models']['mean_variance'])}"


# ---------------------------------------------------------------------------
# Step 7 — Cleanup
# ---------------------------------------------------------------------------

def _cleanup() -> None:
    from app.storage.session_state import reset_configuration

    reset_configuration()


if __name__ == "__main__":
    main()
