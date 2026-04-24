"""Repeatable smoke checks for Modelling-owned processing paths."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
import pandas as pd

import app.processing.data_api as data_api
import app.processing.models as models
from app.processing.dataset import DatasetBuildError, build_canonical_price_dataframe
from app.processing.runner import generate_modelling_outputs
from app.processing.transformations import (
    cumulative_performance,
    drawdown_series,
    summary_metrics_for_model_with_reasons,
)


ASSETS = [
    {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    {"id": "solana", "symbol": "sol", "name": "Solana"},
]


def main() -> None:
    _check_dataset_too_few_assets()
    _check_dataset_insufficient_history()
    _check_unsupported_model_selection()
    _check_partial_model_failure_shape()
    _check_optional_missing_artifact_shape()
    _check_metric_consistency()
    _check_unavailable_metric_reasons()
    _check_cooperative_cancellation()
    print("modelling smoke checks passed")


def _check_dataset_too_few_assets() -> None:
    prices = _price_history(ASSETS[:1], days=120)
    _expect_dataset_error(
        selected_assets=ASSETS[:1],
        prices=prices,
        expected="Select at least 2 assets",
    )


def _check_dataset_insufficient_history() -> None:
    prices = _price_history(ASSETS[:2], days=30)
    _expect_dataset_error(
        selected_assets=ASSETS[:2],
        prices=prices,
        expected="fewer than 90 valid daily prices",
    )


def _check_unsupported_model_selection() -> None:
    original_workflow = data_api.get_active_workflow
    original_validate = data_api.validate_active_configuration
    original_fetch = data_api.fetch_price_history_for_assets
    try:
        data_api.get_active_workflow = lambda: {
            "user_inputs": {
                "selected_assets": ASSETS[:2],
                "selected_models": ["mean_variance", "future_model"],
            },
            "modelling_plan": {"status": "confirmed"},
        }
        data_api.validate_active_configuration = lambda: {"valid": True, "issues": []}
        data_api.fetch_price_history_for_assets = lambda ids, force_refresh=False: {
            "ok": True,
            "prices": _price_history(ASSETS[:2], days=120),
            "errors": [],
        }
        result = data_api.run_active_modelling(output_dir=Path("/tmp/allocadabra-unused"))
    finally:
        data_api.get_active_workflow = original_workflow
        data_api.validate_active_configuration = original_validate
        data_api.fetch_price_history_for_assets = original_fetch

    assert result["ok"] is False, result
    assert result["errors"][0]["code"] == "unsupported_models", result
    assert result["successful_models"] == [], result


def _check_partial_model_failure_shape() -> None:
    with TemporaryDirectory() as tmp:
        result = generate_modelling_outputs(
            selected_assets=ASSETS[:3],
            price_history_by_id=_price_history(ASSETS[:3], days=140),
            selected_models=["mean_variance", "unsupported_model"],
            output_dir=Path(tmp),
        )
        failed_path = Path(tmp) / "failed-models.json"
        failed_payload = json.loads(failed_path.read_text(encoding="utf-8"))

    assert result["ok"] is True, result
    assert result["successful_models"] == ["mean_variance"], result
    assert len(result["failed_models"]) == 1, result
    failure = result["failed_models"][0]
    assert failure["model_id"] == "unsupported_model", failure
    assert failure["stage"] == "model_execution", failure
    assert failure["reason"], failure
    assert failed_payload["failed_models"][0]["model_id"] == "unsupported_model"


def _check_optional_missing_artifact_shape() -> None:
    original_frontier = models._efficient_frontier
    try:
        models._efficient_frontier = lambda port, returns: None
        with TemporaryDirectory() as tmp:
            result = generate_modelling_outputs(
                selected_assets=ASSETS[:3],
                price_history_by_id=_price_history(ASSETS[:3], days=140),
                selected_models=["mean_variance"],
                output_dir=Path(tmp),
            )
    finally:
        models._efficient_frontier = original_frontier

    missing = [
        artifact
        for artifact in result["artifacts"]
        if artifact["status"] == "missing" and artifact["output_type"] == "efficient_frontier"
    ]
    assert missing, result["artifacts"]
    artifact = missing[0]
    assert artifact["format"] == "txt", artifact
    assert artifact["reason"], artifact
    assert artifact["individual_download_enabled"] is False, artifact


def _check_metric_consistency() -> None:
    returns = pd.Series(
        [
            0.010,
            -0.005,
            0.004,
            -0.002,
            0.003,
            0.006,
            -0.004,
            0.002,
        ]
        * 5,
        name="portfolio_return",
    )
    result = summary_metrics_for_model_with_reasons(model_id="mean_variance", returns=returns)
    values = result.values
    expected_total = float(cumulative_performance(returns).iloc[-1] * 100.0)
    expected_drawdown = float(drawdown_series(returns).min() * 100.0)
    assert np.isclose(values["total_return_pct"], expected_total), values
    assert np.isclose(values["max_drawdown_pct"], expected_drawdown), values
    assert np.isfinite(values["annualized_return_pct"]), values
    assert np.isfinite(values["annualized_volatility_pct"]), values
    assert "total_return_pct" not in {row.metric for row in result.unavailable_reasons}


def _check_unavailable_metric_reasons() -> None:
    returns = pd.Series([0.001] * 40, name="portfolio_return")
    result = summary_metrics_for_model_with_reasons(model_id="mean_variance", returns=returns)
    reasons = {row.metric: row.reason_code for row in result.unavailable_reasons}
    assert reasons["sharpe_ratio"] == "zero_volatility", reasons
    assert reasons["calmar_ratio"] == "zero_drawdown", reasons
    assert reasons["omega_ratio"] == "no_negative_returns", reasons
    assert reasons["sortino_ratio"] == "no_negative_returns", reasons
    assert reasons["avg_drawdown_pct"] == "zero_drawdown", reasons

    with TemporaryDirectory() as tmp:
        output = generate_modelling_outputs(
            selected_assets=ASSETS[:3],
            price_history_by_id=_monotonic_price_history(ASSETS[:3], days=120),
            selected_models=["mean_variance"],
            output_dir=Path(tmp),
        )
        reason_file = Path(tmp) / "summary-metric-unavailable-reasons.csv"
        reason_table = pd.read_csv(reason_file)

    assert any(
        artifact["output_type"] == "summary_metric_unavailable_reasons"
        for artifact in output["artifacts"]
    ), output["artifacts"]
    assert set(reason_table.columns) == {"model_id", "metric", "reason_code", "message"}
    assert (reason_table["reason_code"] == "no_negative_returns").any(), reason_table


def _check_cooperative_cancellation() -> None:
    original_workflow = data_api.get_active_workflow
    original_validate = data_api.validate_active_configuration
    original_fetch = data_api.fetch_price_history_for_assets
    try:
        data_api.get_active_workflow = lambda: {
            "user_inputs": {
                "selected_assets": ASSETS[:3],
                "selected_models": ["mean_variance"],
            },
            "modelling_plan": {"status": "confirmed"},
        }
        data_api.validate_active_configuration = lambda: {"valid": True, "issues": []}
        data_api.fetch_price_history_for_assets = lambda ids, force_refresh=False: {
            "ok": True,
            "prices": _price_history(ASSETS[:3], days=120),
            "errors": [],
        }
        calls = {"count": 0}

        def cancel_check() -> bool:
            calls["count"] += 1
            return calls["count"] >= 7

        with TemporaryDirectory() as tmp:
            result = data_api.run_active_modelling(
                cancel_check=cancel_check,
                output_dir=Path(tmp),
            )
    finally:
        data_api.get_active_workflow = original_workflow
        data_api.validate_active_configuration = original_validate
        data_api.fetch_price_history_for_assets = original_fetch

    assert result["ok"] is False, result
    assert result["errors"][0]["code"] == "modelling_cancelled", result
    assert result["artifacts"] == [], result
    assert result["progress_events"][-1]["status"] == "failed", result


def _expect_dataset_error(
    *,
    selected_assets: list[dict[str, str]],
    prices: dict[str, list[dict[str, Any]]],
    expected: str,
) -> None:
    try:
        build_canonical_price_dataframe(
            selected_assets=selected_assets,
            price_history_by_id=prices,
        )
    except DatasetBuildError as exc:
        assert expected in str(exc), exc
        return
    raise AssertionError(f"Expected DatasetBuildError containing {expected!r}")


def _price_history(
    assets: list[dict[str, str]],
    *,
    days: int,
) -> dict[str, list[dict[str, Any]]]:
    start = date(2025, 1, 1)
    data: dict[str, list[dict[str, Any]]] = {}
    for asset_index, asset in enumerate(assets):
        price = 100.0 + asset_index * 25.0
        rows: list[dict[str, Any]] = []
        for day in range(days):
            drift = 0.001 + asset_index * 0.0004
            wave = 0.003 * np.sin(day / (5.0 + asset_index))
            price *= 1.0 + drift + wave
            rows.append(
                {
                    "date": (start + timedelta(days=day)).isoformat(),
                    "price": round(price, 8),
                }
            )
        data[asset["id"]] = rows
    return data


def _monotonic_price_history(
    assets: list[dict[str, str]],
    *,
    days: int,
) -> dict[str, list[dict[str, Any]]]:
    start = date(2025, 1, 1)
    data: dict[str, list[dict[str, Any]]] = {}
    for asset_index, asset in enumerate(assets):
        price = 100.0 + asset_index * 25.0
        rows: list[dict[str, Any]] = []
        for day in range(days):
            price *= 1.001 + asset_index * 0.0001
            rows.append(
                {
                    "date": (start + timedelta(days=day)).isoformat(),
                    "price": round(price, 8),
                }
            )
        data[asset["id"]] = rows
    return data


if __name__ == "__main__":
    main()
