"""Fixture-backed Review rendering validation for Task 118.

Validates that the synthetic Review fixture can be materialised through the
real export bundle path and that the resulting manifest and artifact files are
structurally correct — all without running Streamlit or requiring API keys.

Steps:
  1. Write synthetic CSVs to a temp directory.
  2. Set up workflow state and call prepare_review_export_bundle(...).
  3. Read and validate the manifest structure.
  4. Validate summary metrics CSV content.
  5. Validate allocation weights CSVs.
  6. Cleanup: reset storage state, remove temp directory.

Run: uv run python scripts/review_fixture_smoke.py
Expected final line: review fixture smoke ok
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_DIR = Path("/tmp/allocadabra-synthetic-review-fixture")

SYNTHETIC_PLAN_MARKDOWN = (
    "## Objective\nStable Performance\n"
    "## Risk Appetite\nMedium\n"
    "## Selected Assets\nBitcoin, Ethereum\n"
    "## Constraints\nNone\n"
    "## Selected Models\nMean Variance, Risk Parity\n"
    "## Data Window\nLast 365 daily observations"
)

V1_METRIC_COLUMNS = [
    "total_return_pct",
    "max_drawdown_pct",
    "sharpe_ratio",
    "calmar_ratio",
    "omega_ratio",
    "sortino_ratio",
    "annualized_return_pct",
    "annualized_volatility_pct",
    "30d_volatility_pct",
    "avg_drawdown_pct",
    "skewness",
    "kurtosis",
    "cvar_pct",
    "cdar_pct",
]


def main() -> None:
    _setup_workflow()
    source_dir = _write_synthetic_artifacts()
    descriptors = _build_artifact_descriptors(source_dir)
    _call_prepare_review_export_bundle(descriptors)
    manifest = _validate_manifest()
    _validate_summary_metrics_csv(manifest)
    _validate_allocation_weights_csvs(manifest)
    _cleanup(source_dir)
    print("review fixture smoke ok")


def _setup_workflow() -> None:
    from app.storage.session_state import (
        confirm_generated_plan,
        reset_configuration,
        store_generated_plan,
    )
    from app.storage.data_api import update_active_inputs

    reset_configuration()
    update_active_inputs({
        "selected_assets": [
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        ],
        "treasury_objective": "Stable Performance",
        "risk_appetite": "Medium",
        "selected_models": ["mean_variance", "risk_parity"],
    })
    store_generated_plan(markdown=SYNTHETIC_PLAN_MARKDOWN)
    confirm_generated_plan()


def _write_synthetic_artifacts() -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    (SOURCE_DIR / "summary-metrics.csv").write_text(
        "\n".join([
            "model_id," + ",".join(V1_METRIC_COLUMNS),
            "mean_variance,8.4,-18.2,0.72,0.46,1.12,0.91,8.1,21.4,23.2,-6.8,-0.31,4.8,-4.2,-9.4",
            "risk_parity,6.1,-10.5,0.88,0.58,1.18,1.04,6.0,12.6,11.8,-3.9,-0.12,3.6,-2.7,-5.6",
        ]) + "\n",
        encoding="utf-8",
    )
    (SOURCE_DIR / "mean-variance-allocation-weights.csv").write_text(
        "asset,weight\nBitcoin,0.65\nEthereum,0.35\n",
        encoding="utf-8",
    )
    (SOURCE_DIR / "risk-parity-allocation-weights.csv").write_text(
        "asset,weight\nBitcoin,0.45\nEthereum,0.55\n",
        encoding="utf-8",
    )
    return SOURCE_DIR


def _build_artifact_descriptors(source_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": "synthetic_summary_metrics",
            "label": "Synthetic summary metrics",
            "category": "general",
            "model_id": None,
            "output_type": "summary_metrics",
            "format": "csv",
            "source_path": str(source_dir / "summary-metrics.csv"),
            "filename": "summary-metrics.csv",
            "status": "available",
            "included_in_download_all": True,
            "individual_download_enabled": True,
        },
        {
            "artifact_id": "synthetic_mean_variance_allocation_weights",
            "label": "Mean Variance synthetic allocation weights",
            "category": "model",
            "model_id": "mean_variance",
            "output_type": "allocation_weights",
            "format": "csv",
            "source_path": str(source_dir / "mean-variance-allocation-weights.csv"),
            "filename": "allocation-weights.csv",
            "status": "available",
            "included_in_download_all": True,
            "individual_download_enabled": True,
        },
        {
            "artifact_id": "synthetic_risk_parity_allocation_weights",
            "label": "Risk Parity synthetic allocation weights",
            "category": "model",
            "model_id": "risk_parity",
            "output_type": "allocation_weights",
            "format": "csv",
            "source_path": str(source_dir / "risk-parity-allocation-weights.csv"),
            "filename": "allocation-weights.csv",
            "status": "available",
            "included_in_download_all": True,
            "individual_download_enabled": True,
        },
    ]


def _call_prepare_review_export_bundle(descriptors: list[dict[str, Any]]) -> None:
    from app.storage.data_api import prepare_review_export_bundle

    result = prepare_review_export_bundle(
        modelling_artifacts=descriptors,
        failed_models=[],
        missing_artifacts=[],
    )
    assert result.get("ok"), f"prepare_review_export_bundle returned ok=False: {result}"


def _validate_manifest() -> dict[str, Any]:
    from app.storage.data_api import get_review_export_manifest
    from app.storage.paths import MODEL_OUTPUTS_DIR

    manifest = get_review_export_manifest()
    assert isinstance(manifest, dict) and manifest, "Manifest must be a non-empty dict"
    assert "artifacts" in manifest, "Manifest missing 'artifacts' key"
    assert isinstance(manifest["artifacts"], list), "Manifest 'artifacts' must be a list"

    artifacts = manifest["artifacts"]

    # Three synthetic IDs must all be present.
    expected_ids = {
        "synthetic_summary_metrics",
        "synthetic_mean_variance_allocation_weights",
        "synthetic_risk_parity_allocation_weights",
    }
    found_ids = {a["artifact_id"] for a in artifacts if a.get("artifact_id") in expected_ids}
    assert found_ids == expected_ids, f"Missing synthetic artifact IDs: {expected_ids - found_ids}"

    # Both model IDs appear in at least one artifact.
    model_ids_in_manifest = {a.get("model_id") for a in artifacts}
    assert "mean_variance" in model_ids_in_manifest, "mean_variance not in any artifact"
    assert "risk_parity" in model_ids_in_manifest, "risk_parity not in any artifact"

    # All available artifact paths exist on disk.
    for artifact in artifacts:
        path = artifact.get("path")
        status = artifact.get("status")
        if path and status == "available":
            resolved = MODEL_OUTPUTS_DIR / path
            assert resolved.exists(), f"Artifact path does not exist on disk: {resolved}"

    # summary_metrics entry has correct output_type and category.
    summary = next(a for a in artifacts if a.get("artifact_id") == "synthetic_summary_metrics")
    assert summary["output_type"] == "summary_metrics", f"Wrong output_type: {summary['output_type']}"
    assert summary["category"] == "general", f"Wrong category: {summary['category']}"

    # Both allocation_weights entries have correct output_type and category.
    alloc_ids = {
        "synthetic_mean_variance_allocation_weights",
        "synthetic_risk_parity_allocation_weights",
    }
    for artifact in artifacts:
        if artifact.get("artifact_id") in alloc_ids:
            assert artifact["output_type"] == "allocation_weights", (
                f"Wrong output_type for {artifact['artifact_id']}: {artifact['output_type']}"
            )
            assert artifact["category"] == "model", (
                f"Wrong category for {artifact['artifact_id']}: {artifact['category']}"
            )

    return manifest


def _validate_summary_metrics_csv(manifest: dict[str, Any]) -> None:
    from app.storage.paths import MODEL_OUTPUTS_DIR

    summary_artifact = next(
        a for a in manifest["artifacts"] if a.get("artifact_id") == "synthetic_summary_metrics"
    )
    csv_path = MODEL_OUTPUTS_DIR / summary_artifact["path"]

    df = pd.read_csv(csv_path)
    assert len(df) == 2, f"Expected 2 rows in summary metrics CSV, got {len(df)}"
    assert "model_id" in df.columns, "summary metrics CSV missing 'model_id' column"
    assert set(df["model_id"]) == {"mean_variance", "risk_parity"}, (
        f"Unexpected model_id values: {set(df['model_id'])}"
    )

    for col in V1_METRIC_COLUMNS:
        assert col in df.columns, f"summary metrics CSV missing V1 column: {col}"

    # No literal nan/NaN strings in any cell (read raw to detect string 'nan').
    df_raw = pd.read_csv(csv_path, keep_default_na=False)
    for col in df_raw.columns:
        for val in df_raw[col]:
            if isinstance(val, str) and val.strip().lower() in ("nan", "null", "none"):
                raise AssertionError(f"Literal nan-like string in column {col!r}: {val!r}")


def _validate_allocation_weights_csvs(manifest: dict[str, Any]) -> None:
    from app.storage.paths import MODEL_OUTPUTS_DIR

    alloc_ids = {
        "synthetic_mean_variance_allocation_weights",
        "synthetic_risk_parity_allocation_weights",
    }
    for artifact in manifest["artifacts"]:
        if artifact.get("artifact_id") not in alloc_ids:
            continue

        csv_path = MODEL_OUTPUTS_DIR / artifact["path"]
        df = pd.read_csv(csv_path)

        assert "asset" in df.columns, f"Missing 'asset' column in {artifact['artifact_id']}"
        assert "weight" in df.columns, f"Missing 'weight' column in {artifact['artifact_id']}"
        assert len(df) == 2, (
            f"Expected 2 rows in {artifact['artifact_id']}, got {len(df)}"
        )

        weights = df["weight"].astype(float)
        assert all(0 <= w <= 1 for w in weights), (
            f"Weights out of [0, 1] range in {artifact['artifact_id']}: {weights.tolist()}"
        )
        assert abs(weights.sum() - 1.0) < 0.001, (
            f"Weights do not sum to 1.0 in {artifact['artifact_id']}: {weights.sum()}"
        )


def _cleanup(source_dir: Path) -> None:
    from app.storage.session_state import reset_configuration

    reset_configuration()
    shutil.rmtree(source_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
