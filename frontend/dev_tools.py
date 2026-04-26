"""Local-only frontend validation hooks."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from app.storage import get_active_workflow, prepare_review_export_bundle, save_active_workflow
from frontend.runtime import reset_review_ui, set_review_model_id, set_review_section, ui_state


DEV_REVIEW_FIXTURE_PARAM = "alloca_dev_review_fixture"
DEV_NO_AI_ENV_PARAM = "alloca_dev_no_ai_env"
PERPLEXITY_API_KEY_ENV = "PERPLEXITY_API_KEY"

_ORIGINAL_DOTENV_LOADER: Callable[..., Any] | None = None

SYNTHETIC_PLAN_MARKDOWN = (
    "## Objective\nStable Performance\n"
    "## Risk Appetite\nMedium\n"
    "## Selected Assets\nBitcoin, Ethereum\n"
    "## Constraints\nNone\n"
    "## Selected Models\nMean Variance, Risk Parity\n"
    "## Data Window\nLast 365 daily observations"
)


def apply_dev_validation_hooks() -> None:
    """Apply query-param controlled local validation hooks."""
    _apply_missing_ai_key_hook()
    _apply_synthetic_review_fixture()


def _apply_missing_ai_key_hook() -> None:
    if not _query_param_enabled(DEV_NO_AI_ENV_PARAM):
        _restore_dotenv_loader()
        return

    os.environ.pop(PERPLEXITY_API_KEY_ENV, None)
    _suppress_dotenv_loader()
    ui_state()["dev_no_ai_env"] = True
    st.sidebar.caption("Local validation: AI .env loading suppressed for this app process.")


def _apply_synthetic_review_fixture() -> None:
    fixture_value = _query_param_value(DEV_REVIEW_FIXTURE_PARAM)
    if not _truthy(fixture_value):
        return

    state = ui_state()
    loaded_value = state.get("synthetic_review_fixture_loaded_for")
    if loaded_value == fixture_value:
        st.sidebar.caption("Local validation: synthetic Review fixture active.")
        return

    state["synthetic_review_fixture_previous_workflow"] = deepcopy(get_active_workflow())
    _load_synthetic_review_fixture()
    state["synthetic_review_fixture_loaded_for"] = fixture_value
    st.sidebar.caption("Local validation: synthetic Review fixture active.")
    st.rerun()


def _load_synthetic_review_fixture() -> None:
    workflow = deepcopy(get_active_workflow())
    workflow["phase"] = "configuration"
    workflow["user_inputs"] = {
        "selected_assets": [
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        ],
        "treasury_objective": "Stable Performance",
        "risk_appetite": "Medium",
        "constraints": {},
        "selected_models": ["mean_variance", "risk_parity"],
    }
    workflow["modelling_plan"] = {
        "status": "confirmed",
        "markdown": SYNTHETIC_PLAN_MARKDOWN,
        "metadata": {
            "selected_model_ids": ["mean_variance", "risk_parity"],
            "data_window": "Last 365 daily observations",
        },
        "confirmed_at": "2026-04-24T12:00:00Z",
    }
    workflow["chat_sessions"] = {"configuration": [], "review": []}
    workflow["modelling_run"] = {
        "status": "idle",
        "started_at": None,
        "completed_at": None,
        "interrupted_at": None,
        "error": None,
    }
    workflow["model_outputs"] = {"status": "none", "manifest_path": None}
    save_active_workflow(workflow)

    source_dir = _write_synthetic_artifacts()
    prepare_review_export_bundle(
        modelling_artifacts=[
            _artifact_descriptor(
                artifact_id="synthetic_summary_metrics",
                label="Synthetic summary metrics",
                output_type="summary_metrics",
                source_path=source_dir / "summary-metrics.csv",
                filename="summary-metrics.csv",
            ),
            _artifact_descriptor(
                artifact_id="synthetic_mean_variance_allocation_weights",
                label="Mean Variance synthetic allocation weights",
                output_type="allocation_weights",
                model_id="mean_variance",
                source_path=source_dir / "mean-variance-allocation-weights.csv",
                filename="allocation-weights.csv",
            ),
            _artifact_descriptor(
                artifact_id="synthetic_risk_parity_allocation_weights",
                label="Risk Parity synthetic allocation weights",
                output_type="allocation_weights",
                model_id="risk_parity",
                source_path=source_dir / "risk-parity-allocation-weights.csv",
                filename="allocation-weights.csv",
            ),
        ],
        failed_models=[],
        missing_artifacts=[],
    )
    reset_review_ui()
    set_review_section("allocation_weights")
    set_review_model_id("risk_parity")


def _write_synthetic_artifacts() -> Path:
    source_dir = Path("/tmp/allocadabra-synthetic-review-fixture")
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "summary-metrics.csv").write_text(
        "\n".join(
            [
                "model_id,total_return_pct,max_drawdown_pct,sharpe_ratio,calmar_ratio,omega_ratio,sortino_ratio,annualized_return_pct,annualized_volatility_pct,30d_volatility_pct,avg_drawdown_pct,skewness,kurtosis,cvar_pct,cdar_pct",
                "mean_variance,8.4,-18.2,0.72,0.46,1.12,0.91,8.1,21.4,23.2,-6.8,-0.31,4.8,-4.2,-9.4",
                "risk_parity,6.1,-10.5,0.88,0.58,1.18,1.04,6.0,12.6,11.8,-3.9,-0.12,3.6,-2.7,-5.6",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (source_dir / "mean-variance-allocation-weights.csv").write_text(
        "asset,weight\nBitcoin,0.65\nEthereum,0.35\n",
        encoding="utf-8",
    )
    (source_dir / "risk-parity-allocation-weights.csv").write_text(
        "asset,weight\nBitcoin,0.45\nEthereum,0.55\n",
        encoding="utf-8",
    )
    return source_dir


def _artifact_descriptor(
    *,
    artifact_id: str,
    label: str,
    output_type: str,
    source_path: Path,
    filename: str,
    model_id: str | None = None,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "label": label,
        "category": "model" if model_id else "general",
        "model_id": model_id,
        "output_type": output_type,
        "format": "csv",
        "source_path": str(source_path),
        "filename": filename,
        "status": "available",
        "included_in_download_all": True,
        "individual_download_enabled": True,
    }


def _suppress_dotenv_loader() -> None:
    global _ORIGINAL_DOTENV_LOADER
    import app.ai.provider as provider_module

    if _ORIGINAL_DOTENV_LOADER is None:
        _ORIGINAL_DOTENV_LOADER = provider_module.load_dotenv_if_present
    provider_module.load_dotenv_if_present = _noop_dotenv_loader


def _restore_dotenv_loader() -> None:
    global _ORIGINAL_DOTENV_LOADER
    if _ORIGINAL_DOTENV_LOADER is None:
        return

    import app.ai.provider as provider_module

    provider_module.load_dotenv_if_present = _ORIGINAL_DOTENV_LOADER
    _ORIGINAL_DOTENV_LOADER = None


def _noop_dotenv_loader(*_: Any, **__: Any) -> None:
    return None


def _query_param_enabled(name: str) -> bool:
    return _truthy(_query_param_value(name))


def _query_param_value(name: str) -> str | None:
    value = st.query_params.get(name)
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def _truthy(value: str | None) -> bool:
    return bool(value and value.lower() not in {"0", "false", "no", "off"})
