"""Deterministic Backend/Data smoke checks for cache, session, validation, and exports."""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.ingestion.coingecko import CoinGeckoClient, load_dotenv_if_present  # noqa: E402
from app.storage.data_api import (  # noqa: E402
    get_review_artifact_download,
    get_review_download_all,
    get_review_export_manifest,
    prepare_review_export_bundle,
    update_active_inputs,
)
from app.storage.export_bundle import (  # noqa: E402
    MISSING_ARTIFACT_DEFAULT_REASON,
    MODEL_ARTIFACT_PATH_PREFIX,
)
from app.storage.json_files import write_json  # noqa: E402
from app.storage.market_cache import (  # noqa: E402
    get_price_history,
    get_token_options,
    price_cache_status,
    search_token_options,
)
from app.storage.paths import (  # noqa: E402
    COINGECKO_PRICES_DIR,
    MODEL_OUTPUTS_DIR,
    STORAGE_ROOT,
    TOKEN_LIST_FILE,
    ensure_storage_dirs,
)
from app.storage.schemas import metadata_payload  # noqa: E402
from app.storage.session_state import (  # noqa: E402
    confirm_generated_plan,
    get_workflow_state,
    reset_configuration,
    start_new_model,
    store_generated_plan,
)
from app.storage.validation import validate_configuration_inputs  # noqa: E402


def main() -> None:
    with _restored_storage_cache():
        ensure_storage_dirs()
        _smoke_coingecko_cache_read_paths()
        _smoke_session_lifecycle()
        _smoke_validation_issue_shape()
        _smoke_export_bundle()
        _smoke_coingecko_policy_shape()
        _smoke_multi_model_layout()
        _smoke_missing_placeholder_types()
        _smoke_download_all_exclusions()
        _smoke_reconfigure_from_review()
        _smoke_rerun_after_reset()
        _smoke_live_coingecko()
    print("backend smoke ok")


@contextmanager
def _restored_storage_cache():
    with tempfile.TemporaryDirectory(prefix="allocadabra-backend-smoke-") as temp_dir:
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


def _smoke_coingecko_cache_read_paths() -> None:
    write_json(
        TOKEN_LIST_FILE,
        metadata_payload(
            tokens=[
                {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
                {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
            ]
        ),
    )
    tokens = get_token_options()
    assert [token.id for token in tokens] == ["bitcoin", "ethereum"]
    assert [token.id for token in search_token_options("bit")] == ["bitcoin"]

    today = datetime.now(tz=timezone.utc).date()
    price_rows = [
        {
            "id": "bitcoin",
            "date": (today - timedelta(days=90 - index)).isoformat(),
            "price": str(100 + index),
        }
        for index in range(91)
    ]
    _write_price_csv("bitcoin", price_rows)

    points = get_price_history("bitcoin")
    status = price_cache_status("bitcoin", points)
    assert len(points) == 91
    assert status.coin_id == "bitcoin"
    assert status.cache_hit is True
    assert status.stale is False
    assert status.valid_price_count == 91


def _smoke_session_lifecycle() -> None:
    state = reset_configuration()
    assert state["phase"] == "configuration"
    assert state["user_inputs"]["selected_assets"] == []

    state = update_active_inputs(_valid_user_inputs())
    assert state["user_inputs"]["selected_models"] == ["mean_variance"]

    state = store_generated_plan(markdown="# Plan\n\nRun Mean Variance.")
    assert state["modelling_plan"]["status"] == "generated"

    state = confirm_generated_plan()
    assert state["modelling_plan"]["status"] == "confirmed"
    assert state["modelling_plan"]["confirmed_at"]


def _smoke_validation_issue_shape() -> None:
    result = validate_configuration_inputs(
        {
            **_valid_user_inputs(),
            "selected_models": ["mean_variance", "mean_variance", "future_model"],
            "constraints": {
                "global_min_allocation_percent": 60,
                "global_max_allocation_percent": 50,
                "selected_asset_min_allocation": {
                    "asset_ids": ["dogecoin"],
                    "percent": 20,
                },
                "min_assets_in_portfolio": 3,
                "max_assets_in_portfolio": 1,
            },
        }
    )
    issues = [issue.__dict__ for issue in result.issues]
    assert result.valid is False
    for issue in issues:
        assert set(issue) == {"field", "code", "message", "context"}
        assert isinstance(issue["field"], str)
        assert isinstance(issue["code"], str)
        assert isinstance(issue["message"], str)
    codes = {issue["code"] for issue in issues}
    assert "unsupported_model_id" in codes
    assert "duplicate_model_ids" in codes
    assert "constraint_min_greater_than_max" in codes
    assert "constraint_asset_id_not_selected" in codes
    assert "min_assets_constraint_exceeds_selected_assets" in codes
    assert "min_assets_constraint_greater_than_max_assets_constraint" in codes


def _smoke_export_bundle() -> None:
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan\n\nRun Mean Variance.")
    confirm_generated_plan()

    source = Path(tempfile.gettempdir()) / "allocadabra-backend-smoke-summary.csv"
    source.write_text("metric,mean_variance\nreturn,0.1\n", encoding="utf-8")

    result = prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "summary_metrics",
                "label": "Summary metrics",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(source),
                "bundle_path": "summary-metrics.csv",
            },
            {
                "artifact_id": "missing_source_csv",
                "label": "Missing source CSV",
                "category": "model",
                "model_id": "mean_variance",
                "output_type": "allocation_weights",
                "format": "csv",
                "source_path": str(source.with_name("does-not-exist.csv")),
                "bundle_path": "models/mean_variance/missing-source.csv",
            },
        ],
        failed_models=[
            {
                "model_id": "risk_parity",
                "label": "Risk Parity",
                "stage": "model_execution",
                "reason": "Fixture failure.",
            }
        ],
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

    assert result["ok"] is True
    assert result["workflow_state"]["phase"] == "review"
    assert get_workflow_state()["phase"] == "review"

    manifest = result["exports"]["manifest"]
    artifacts = {artifact["artifact_id"]: artifact for artifact in manifest["artifacts"]}
    assert artifacts["summary_metrics"]["status"] == "available"
    assert artifacts["missing_source_csv"]["status"] == "failed"
    assert artifacts["efficient_frontier_png"]["status"] == "missing"
    assert artifacts["failed_models"]["status"] == "available"

    download_all = get_review_download_all()
    assert download_all["ok"] is True
    assert download_all["filename"].startswith("allocadabra-results-")

    available = get_review_artifact_download("summary_metrics")
    missing = get_review_artifact_download("efficient_frontier_png")
    failed = get_review_artifact_download("missing_source_csv")
    assert available["ok"] is True
    assert missing["enabled"] is False
    assert failed["enabled"] is False

    with ZipFile(download_all["path"]) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert "user-inputs.json" in names
    assert "modelling-plan.md" in names
    assert "summary-metrics.csv" in names
    assert "failed-models.json" in names
    assert "missing/efficient_frontier_png.txt" in names
    assert not any(name.startswith("coingecko/") for name in names)
    assert not any("chat" in name.lower() for name in names)
    assert not any(name.startswith(MODEL_ARTIFACT_PATH_PREFIX) for name in names if "missing-source" in name)

    state = start_new_model()
    assert state["phase"] == "configuration"
    assert state["user_inputs"]["selected_assets"] == []


def _smoke_coingecko_policy_shape() -> None:
    client = CoinGeckoClient(api_key="demo-key")
    assert client.timeout_seconds == 20
    assert client.max_retries == 2
    assert client.retry_delay_seconds == 1


# ---------------------------------------------------------------------------
# Task 136 — export edge cases and session lifecycle transitions
# ---------------------------------------------------------------------------

def _smoke_multi_model_layout() -> None:
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan\n\nRun two models.")
    confirm_generated_plan()

    mv_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-mv-weights.csv"
    mv_source.write_text("asset,weight\nbitcoin,0.6\nethereum,0.4\n", encoding="utf-8")
    rp_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-rp-weights.csv"
    rp_source.write_text("asset,weight\nbitcoin,0.5\nethereum,0.5\n", encoding="utf-8")
    root_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-multi-summary.csv"
    root_source.write_text("metric,value\nreturn,0.12\n", encoding="utf-8")

    result = prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "mv_weights",
                "label": "MV allocation weights",
                "category": "model",
                "model_id": "mean_variance",
                "output_type": "allocation_weights",
                "format": "csv",
                "source_path": str(mv_source),
                "bundle_path": "models/mean_variance/allocation-weights.csv",
            },
            {
                "artifact_id": "rp_weights",
                "label": "RP allocation weights",
                "category": "model",
                "model_id": "risk_parity",
                "output_type": "allocation_weights",
                "format": "csv",
                "source_path": str(rp_source),
                "bundle_path": "models/risk_parity/allocation-weights.csv",
            },
            {
                "artifact_id": "summary_metrics",
                "label": "Summary metrics",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(root_source),
                "bundle_path": "summary-metrics.csv",
            },
        ],
    )

    assert result["ok"] is True
    manifest = result["exports"]["manifest"]
    artifacts = {a["artifact_id"]: a for a in manifest["artifacts"]}

    mv_path = artifacts["mv_weights"]["path"]
    rp_path = artifacts["rp_weights"]["path"]
    summary_path = artifacts["summary_metrics"]["path"]
    manifest_path = artifacts["manifest"]["path"]

    assert mv_path.startswith(f"{MODEL_ARTIFACT_PATH_PREFIX}/mean_variance/")
    assert rp_path.startswith(f"{MODEL_ARTIFACT_PATH_PREFIX}/risk_parity/")
    assert not summary_path.startswith(MODEL_ARTIFACT_PATH_PREFIX + "/")
    assert not manifest_path.startswith(MODEL_ARTIFACT_PATH_PREFIX + "/")

    print("step 5 — multi-model layout ok")


def _smoke_missing_placeholder_types() -> None:
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan\n\nRun one model.")
    confirm_generated_plan()

    result = prepare_review_export_bundle(
        missing_artifacts=[
            {
                "artifact_id": "allocation_weights",
                "label": "Allocation weights",
                "output_type": "allocation_weights",
                "model_id": "mean_variance",
                # no "reason" — should default to MISSING_ARTIFACT_DEFAULT_REASON
            },
            {
                "artifact_id": "efficient_frontier",
                "label": "Efficient frontier",
                "output_type": "efficient_frontier",
                "model_id": "mean_variance",
            },
            {
                "artifact_id": "chart_png",
                "label": "Portfolio chart",
                "output_type": "chart_png",
                "model_id": "mean_variance",
            },
        ],
    )

    manifest = result["exports"]["manifest"]
    artifacts = {a["artifact_id"]: a for a in manifest["artifacts"]}

    for art_id in ("allocation_weights", "efficient_frontier", "chart_png"):
        entry = artifacts[art_id]
        assert entry["status"] == "missing", f"{art_id}: expected status=missing, got {entry['status']}"
        assert entry["individual_download_enabled"] is False, f"{art_id}: individual download should be disabled"
        placeholder = MODEL_OUTPUTS_DIR / entry["path"]
        text = placeholder.read_text(encoding="utf-8").strip()
        assert text == MISSING_ARTIFACT_DEFAULT_REASON, (
            f"{art_id}: placeholder text mismatch: {text!r}"
        )

    print("step 6 — missing placeholder types ok")


def _smoke_download_all_exclusions() -> None:
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan\n\nRun exclusion check.")
    confirm_generated_plan()

    mv_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-excl-mv.csv"
    mv_source.write_text("asset,weight\nbitcoin,0.7\nethereum,0.3\n", encoding="utf-8")
    rp_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-excl-rp.csv"
    rp_source.write_text("asset,weight\nbitcoin,0.5\nethereum,0.5\n", encoding="utf-8")
    summary_source = Path(tempfile.gettempdir()) / "allocadabra-smoke-excl-summary.csv"
    summary_source.write_text("metric,value\nreturn,0.09\n", encoding="utf-8")

    result = prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "excl_mv_weights",
                "label": "MV weights",
                "category": "model",
                "model_id": "mean_variance",
                "output_type": "allocation_weights",
                "format": "csv",
                "source_path": str(mv_source),
                "bundle_path": "models/mean_variance/allocation-weights.csv",
            },
            {
                "artifact_id": "excl_rp_weights",
                "label": "RP weights",
                "category": "model",
                "model_id": "risk_parity",
                "output_type": "allocation_weights",
                "format": "csv",
                "source_path": str(rp_source),
                "bundle_path": "models/risk_parity/allocation-weights.csv",
            },
            {
                "artifact_id": "excl_summary",
                "label": "Summary metrics",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(summary_source),
                "bundle_path": "summary-metrics.csv",
            },
        ],
    )

    assert result["ok"] is True
    download_all = get_review_download_all()
    assert download_all["ok"] is True

    with ZipFile(download_all["path"]) as archive:
        names = set(archive.namelist())

    # Exclusions: raw CoinGecko cache and AI chat transcripts must not appear
    assert not any(name.startswith("coingecko/") for name in names)
    assert not any("chat" in name.lower() for name in names)

    # All available modelling artifacts must be present
    assert "models/mean_variance/allocation-weights.csv" in names
    assert "models/risk_parity/allocation-weights.csv" in names
    assert "summary-metrics.csv" in names

    print("step 7 — download all exclusions ok")


def _smoke_reconfigure_from_review() -> None:
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan\n\nReview-ready run.")
    confirm_generated_plan()

    source = Path(tempfile.gettempdir()) / "allocadabra-smoke-reconfigure.csv"
    source.write_text("metric,value\nreturn,0.08\n", encoding="utf-8")
    prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "reconfig_summary",
                "label": "Summary metrics",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(source),
                "bundle_path": "summary-metrics.csv",
            },
        ],
    )

    assert get_workflow_state()["phase"] == "review"

    reset_configuration()

    state = get_workflow_state()
    assert state["phase"] != "review", (
        f"Phase should not be 'review' after reset, got {state['phase']!r}"
    )
    manifest = get_review_export_manifest()
    assert manifest is None, f"Manifest should be absent after reset, got: {manifest!r}"

    print("step 8 — reconfigure from review-ready ok")


def _smoke_rerun_after_reset() -> None:
    # First run
    reset_configuration()
    update_active_inputs(_valid_user_inputs())
    store_generated_plan(markdown="# Plan A")
    confirm_generated_plan()

    source_a = Path(tempfile.gettempdir()) / "allocadabra-smoke-run-a.csv"
    source_a.write_text("run,a\nreturn,0.10\n", encoding="utf-8")
    result_a = prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "run_a_summary",
                "label": "Run A summary",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(source_a),
                "bundle_path": "summary-metrics.csv",
            },
        ],
    )
    assert result_a["ok"] is True

    # Reset between runs
    reset_configuration()

    # Second run with fresh synthetic data
    inputs_b = {**_valid_user_inputs(), "treasury_objective": "Capital preservation"}
    update_active_inputs(inputs_b)
    store_generated_plan(markdown="# Plan B")
    confirm_generated_plan()

    source_b = Path(tempfile.gettempdir()) / "allocadabra-smoke-run-b.csv"
    source_b.write_text("run,b\nreturn,0.05\n", encoding="utf-8")
    result_b = prepare_review_export_bundle(
        modelling_artifacts=[
            {
                "artifact_id": "run_b_summary",
                "label": "Run B summary",
                "category": "general",
                "output_type": "summary_metrics",
                "format": "csv",
                "source_path": str(source_b),
                "bundle_path": "summary-metrics.csv",
            },
        ],
    )
    assert result_b["ok"] is True

    # Second bundle must be independent: different artifact IDs, no bleed from first run
    b_artifact_ids = {a["artifact_id"] for a in result_b["exports"]["manifest"]["artifacts"]}
    assert "run_b_summary" in b_artifact_ids
    assert "run_a_summary" not in b_artifact_ids

    # Zip reflects only the second run
    with ZipFile(get_review_download_all()["path"]) as archive:
        zip_names = set(archive.namelist())
    assert "summary-metrics.csv" in zip_names

    print("step 9 — re-run after reset ok")


# ---------------------------------------------------------------------------
# Task 135 — opt-in live CoinGecko smoke
# ---------------------------------------------------------------------------

def _smoke_live_coingecko() -> None:
    load_dotenv_if_present()
    if not os.environ.get("COINGECKO_API_KEY"):
        print("COINGECKO_API_KEY not set — skipping live coingecko smoke")
        return

    client = CoinGeckoClient()
    result = client.fetch_market_chart("bitcoin")

    assert isinstance(result, list) and len(result) > 0, "fetch_market_chart returned empty list"
    assert len(result) >= 90, f"Expected >= 90 price points, got {len(result)}"

    today_utc = datetime.now(tz=timezone.utc).date()
    latest_date_str = max(point.date for point in result)
    latest_date = date.fromisoformat(latest_date_str)
    days_behind = (today_utc - latest_date).days
    assert days_behind <= 2, (
        f"Latest price point {latest_date_str} is {days_behind} days behind today ({today_utc}); "
        "expected <= 2 days"
    )

    print("live coingecko smoke ok")
    print(f"  latest={latest_date_str}, count={len(result)}, days_behind={days_behind}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_user_inputs() -> dict[str, object]:
    return {
        "selected_assets": [
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        ],
        "treasury_objective": "Best risk-adjusted returns",
        "risk_appetite": "Medium",
        "constraints": {
            "global_min_allocation_percent": 0,
            "global_max_allocation_percent": 100,
            "min_assets_in_portfolio": 0,
            "max_assets_in_portfolio": 3,
        },
        "selected_models": ["mean_variance"],
    }


def _write_price_csv(coin_id: str, rows: list[dict[str, str]]) -> None:
    path = COINGECKO_PRICES_DIR / f"{coin_id}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "date", "price"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
