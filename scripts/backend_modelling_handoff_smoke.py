"""Backend/Data verification for the Modelling -> export handoff."""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.ingestion.coingecko import PricePoint  # noqa: E402
from app.processing.data_api import run_active_modelling  # noqa: E402
from app.processing.runner import generate_modelling_outputs  # noqa: E402
from app.storage.data_api import (  # noqa: E402
    get_review_artifact_download,
    get_review_download_all,
    get_review_export_manifest,
    prepare_review_export_bundle,
    update_active_inputs,
)
from app.storage.market_cache import price_cache_status  # noqa: E402
from app.storage.paths import COINGECKO_PRICES_DIR, MODEL_OUTPUTS_DIR, STORAGE_ROOT  # noqa: E402
from app.storage.session_state import (  # noqa: E402
    confirm_generated_plan,
    get_workflow_state,
    reset_configuration,
    store_generated_plan,
)


ASSETS = [
    {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    {"id": "solana", "symbol": "sol", "name": "Solana"},
]


def main() -> None:
    with _restored_storage_cache():
        _check_active_modelling_export_handoff()
        _check_partial_success_and_missing_artifact_handoff()
        _check_price_cache_freshness_policy()
    print("backend modelling handoff smoke ok")


@contextmanager
def _restored_storage_cache():
    with tempfile.TemporaryDirectory(prefix="allocadabra-handoff-smoke-") as temp_dir:
        backup = Path(temp_dir) / "storage-cache-backup"
        had_storage = STORAGE_ROOT.exists()
        if had_storage:
            shutil.copytree(STORAGE_ROOT, backup)

        try:
            yield
        finally:
            if STORAGE_ROOT.exists():
                shutil.rmtree(STORAGE_ROOT)
            if had_storage:
                shutil.copytree(backup, STORAGE_ROOT)
            else:
                STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def _check_active_modelling_export_handoff() -> None:
    reset_configuration()
    _write_price_cache(ASSETS, days=140)
    _prepare_confirmed_workflow(
        selected_models=["mean_variance", "risk_parity", "hierarchical_risk_parity"]
    )

    modelling = run_active_modelling(output_dir=MODEL_OUTPUTS_DIR)
    assert modelling["ok"] is True, modelling
    assert modelling["errors"] == [], modelling
    assert set(modelling["successful_models"]) == {
        "mean_variance",
        "risk_parity",
        "hierarchical_risk_parity",
    }
    assert modelling["artifacts"], modelling
    assert "output_dir" in modelling
    assert get_workflow_state()["phase"] != "review"

    public_handoff_artifacts = [
        artifact
        for artifact in modelling["artifacts"]
        if artifact.get("output_type") != "failed_models"
    ]
    exported = prepare_review_export_bundle(
        modelling_artifacts=public_handoff_artifacts,
        failed_models=modelling["failed_models"],
        missing_artifacts=modelling["missing_artifacts"],
    )
    assert exported["ok"] is True, exported
    assert exported["workflow_state"]["phase"] == "review"

    manifest = get_review_export_manifest()
    assert isinstance(manifest, dict)
    artifacts = {artifact["artifact_id"]: artifact for artifact in manifest["artifacts"]}
    required_ids = {
        "user_inputs",
        "modelling_plan",
        "canonical_modelling_dataset_csv",
        "summary_metrics_csv",
        "manifest",
    }
    assert required_ids.issubset(artifacts), sorted(artifacts)
    assert artifacts["canonical_modelling_dataset_csv"]["path"] == "canonical-modelling-dataset.csv"
    assert artifacts["summary_metrics_csv"]["path"] == "summary-metrics.csv"

    model_paths = {
        artifact["path"]
        for artifact in manifest["artifacts"]
        if artifact.get("category") == "model" and artifact.get("status") == "available"
    }
    for model_id in modelling["successful_models"]:
        assert any(path.startswith(f"models/{model_id}/") for path in model_paths), model_paths

    summary_download = get_review_artifact_download("summary_metrics_csv")
    assert summary_download["ok"] is True
    assert summary_download["enabled"] is True
    assert summary_download["artifact"]["path"] == "summary-metrics.csv"

    bundle = get_review_download_all()
    assert bundle["ok"] is True
    assert bundle["enabled"] is True
    assert bundle["filename"].startswith("allocadabra-results-")

    with ZipFile(bundle["path"]) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert "user-inputs.json" in names
    assert "modelling-plan.md" in names
    assert "canonical-modelling-dataset.csv" in names
    assert "summary-metrics.csv" in names
    assert any(name.startswith("models/mean_variance/") for name in names)
    assert any(name.startswith("models/risk_parity/") for name in names)
    assert any(name.startswith("models/hierarchical_risk_parity/") for name in names)
    assert not any(name.startswith("coingecko/") for name in names)
    assert not any("chat" in name.lower() for name in names)


def _check_partial_success_and_missing_artifact_handoff() -> None:
    reset_configuration()
    _prepare_confirmed_workflow(selected_models=["mean_variance"])

    modelling = generate_modelling_outputs(
        selected_assets=ASSETS,
        price_history_by_id=_price_history(ASSETS, days=140),
        selected_models=["mean_variance", "unsupported_model"],
        output_dir=MODEL_OUTPUTS_DIR,
    )
    assert modelling["ok"] is True, modelling
    assert modelling["successful_models"] == ["mean_variance"]
    assert len(modelling["failed_models"]) == 1

    public_handoff_artifacts = [
        artifact
        for artifact in modelling["artifacts"]
        if artifact.get("output_type") != "failed_models"
    ]
    exported = prepare_review_export_bundle(
        modelling_artifacts=public_handoff_artifacts,
        failed_models=modelling["failed_models"],
        missing_artifacts=[
            {
                "artifact_id": "efficient_frontier_png",
                "label": "Efficient frontier chart",
                "output_type": "efficient_frontier",
                "model_id": "mean_variance",
                "reason": "This artifact was not generated for this run.",
            }
        ],
    )
    assert exported["workflow_state"]["phase"] == "review"
    manifest = exported["exports"]["manifest"]
    artifacts = {artifact["artifact_id"]: artifact for artifact in manifest["artifacts"]}
    assert artifacts["failed_models"]["status"] == "available"
    assert artifacts["efficient_frontier_png"]["status"] == "missing"
    assert artifacts["efficient_frontier_png"]["individual_download_enabled"] is False

    missing_download = get_review_artifact_download("efficient_frontier_png")
    assert missing_download["enabled"] is False
    assert missing_download["reason"] == "This artifact was not generated for this run."

    bundle = get_review_download_all()
    assert bundle["ok"] is True
    with ZipFile(bundle["path"]) as archive:
        names = set(archive.namelist())
    assert "failed-models.json" in names
    assert "missing/efficient_frontier_png.txt" in names


def _check_price_cache_freshness_policy() -> None:
    today = datetime.now(tz=timezone.utc).date()
    fresh = [
        PricePoint(id="bitcoin", date=(today - timedelta(days=2 + offset)).isoformat(), price=1.0)
        for offset in range(90)
    ]
    stale = [
        PricePoint(id="bitcoin", date=(today - timedelta(days=3 + offset)).isoformat(), price=1.0)
        for offset in range(90)
    ]
    assert price_cache_status("bitcoin", fresh).stale is False
    assert price_cache_status("bitcoin", stale).stale is True


def _prepare_confirmed_workflow(*, selected_models: list[str]) -> None:
    update_active_inputs(
        {
            "selected_assets": ASSETS,
            "treasury_objective": "Best risk-adjusted returns",
            "risk_appetite": "Medium",
            "constraints": {
                "global_min_allocation_percent": 0,
                "global_max_allocation_percent": 100,
                "min_assets_in_portfolio": 0,
                "max_assets_in_portfolio": 3,
            },
            "selected_models": selected_models,
        }
    )
    store_generated_plan(markdown="# Plan\n\nRun the selected supported models.")
    confirm_generated_plan()


def _write_price_cache(assets: list[dict[str, str]], *, days: int) -> None:
    COINGECKO_PRICES_DIR.mkdir(parents=True, exist_ok=True)
    for asset in assets:
        path = COINGECKO_PRICES_DIR / f"{asset['id']}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "date", "price"])
            writer.writeheader()
            writer.writerows(_price_history_rows(asset, days=days))


def _price_history(
    assets: list[dict[str, str]],
    *,
    days: int,
) -> dict[str, list[dict[str, object]]]:
    return {asset["id"]: _price_history_rows(asset, days=days) for asset in assets}


def _price_history_rows(asset: dict[str, str], *, days: int) -> list[dict[str, object]]:
    today = datetime.now(tz=timezone.utc).date()
    start = today - timedelta(days=days - 1)
    asset_offset = {"bitcoin": 0.0, "ethereum": 20.0, "solana": 40.0}[asset["id"]]
    price = 100.0 + asset_offset
    rows: list[dict[str, object]] = []
    for day in range(days):
        seasonal = 1.0 + ((day % 9) - 4) * 0.001
        trend = 1.001 + asset_offset / 100000.0
        price *= trend * seasonal
        rows.append(
            {
                "id": asset["id"],
                "date": (start + timedelta(days=day)).isoformat(),
                "price": round(price, 6),
            }
        )
    return rows


if __name__ == "__main__":
    main()
