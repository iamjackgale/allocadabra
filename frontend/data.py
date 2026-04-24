"""Frontend data helpers for manifests, artifacts, and review summaries."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.ai.models import display_name_for_model_id
from app.storage.data_api import (
    get_review_artifact_download,
    get_review_download_all,
    get_review_export_manifest,
)
from frontend.constants import (
    GENERIC_MISSING_ARTIFACT_MESSAGE,
    METRIC_SPECS,
    MODEL_LABELS,
    OBJECTIVE_RANKING_METRIC,
)


@st.cache_data(show_spinner=False)
def read_csv_file(path: str) -> pd.DataFrame:
    """Read one CSV artifact path."""
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def read_text_file(path: str) -> str:
    """Read one text or markdown artifact path."""
    return Path(path).read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def read_json_file(path: str) -> dict[str, Any]:
    """Read one JSON artifact path."""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def get_review_manifest() -> dict[str, Any] | None:
    """Return the current review export manifest."""
    manifest = get_review_export_manifest()
    return manifest if isinstance(manifest, dict) else None


def get_download_all_payload() -> dict[str, Any]:
    """Return Download All metadata."""
    return get_review_download_all()


def artifacts_from_manifest(manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return manifest artifacts as dictionaries."""
    if not isinstance(manifest, dict):
        return []
    artifacts = manifest.get("artifacts", [])
    return [artifact for artifact in artifacts if isinstance(artifact, dict)]


def artifact_lookup(artifacts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return artifacts keyed by artifact_id."""
    return {
        str(artifact["artifact_id"]): artifact
        for artifact in artifacts
        if artifact.get("artifact_id")
    }


def find_artifacts(
    artifacts: list[dict[str, Any]],
    *,
    output_type: str,
    model_id: str | None = None,
    format_: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Filter artifacts by output type and optional model, format, and status."""
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact.get("output_type") != output_type:
            continue
        if model_id is not None and artifact.get("model_id") != model_id:
            continue
        if format_ is not None and artifact.get("format") != format_:
            continue
        if status is not None and artifact.get("status") != status:
            continue
        rows.append(artifact)
    return rows


def first_artifact(
    artifacts: list[dict[str, Any]],
    *,
    output_type: str,
    model_id: str | None = None,
    format_: str | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """Return the first matching artifact."""
    matches = find_artifacts(
        artifacts,
        output_type=output_type,
        model_id=model_id,
        format_=format_,
        status=status,
    )
    return matches[0] if matches else None


def get_artifact_file_info(artifact_id: str) -> dict[str, Any]:
    """Return resolved file metadata for one review artifact."""
    metadata = get_review_artifact_download(artifact_id)
    return metadata if isinstance(metadata, dict) else {}


def load_artifact_dataframe(artifact_id: str) -> pd.DataFrame | None:
    """Load a CSV artifact into a dataframe."""
    metadata = get_artifact_file_info(artifact_id)
    path = metadata.get("path")
    if not metadata.get("ok") or not isinstance(path, str):
        return None
    return read_csv_file(path)


def load_artifact_text(artifact_id: str) -> str | None:
    """Load a text or markdown artifact."""
    metadata = get_artifact_file_info(artifact_id)
    path = metadata.get("path")
    if not metadata.get("ok") or not isinstance(path, str):
        return None
    return read_text_file(path)


def load_artifact_json(artifact_id: str) -> dict[str, Any]:
    """Load a JSON artifact."""
    metadata = get_artifact_file_info(artifact_id)
    path = metadata.get("path")
    if not metadata.get("ok") or not isinstance(path, str):
        return {}
    return read_json_file(path)


def failed_models_from_manifest(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load failed model reasons from the manifest when present."""
    artifact = first_artifact(artifacts, output_type="failed_models", format_="json")
    if not artifact:
        return []
    payload = load_artifact_json(str(artifact["artifact_id"]))
    rows = payload.get("failed_models", [])
    return [row for row in rows if isinstance(row, dict)]


def successful_model_ids(
    artifacts: list[dict[str, Any]],
    workflow: dict[str, Any],
    failed_models: list[dict[str, Any]],
) -> list[str]:
    """Return successful model IDs in configured run order."""
    configured = workflow.get("user_inputs", {}).get("selected_models", [])
    configured_ids = [str(model_id) for model_id in configured if str(model_id)]
    failed_ids = {str(row.get("model_id")) for row in failed_models if row.get("model_id")}
    present_ids = {
        str(artifact.get("model_id"))
        for artifact in artifacts
        if artifact.get("model_id") and artifact.get("status") in {"available", "missing"}
    }
    ordered = [
        model_id
        for model_id in configured_ids
        if model_id in present_ids and model_id not in failed_ids
    ]
    if ordered:
        return ordered
    return sorted(present_ids)


def summary_metrics_matrix(
    artifacts: list[dict[str, Any]],
    model_order: list[str],
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Return raw summary metrics and a display matrix."""
    artifact = first_artifact(artifacts, output_type="summary_metrics", format_="csv", status="available")
    if not artifact:
        return None, None

    raw = load_artifact_dataframe(str(artifact["artifact_id"]))
    if raw is None or raw.empty:
        return raw, None

    raw = raw.copy()
    raw["model_label"] = raw["model_id"].map(MODEL_LABELS).fillna(raw["model_id"])
    metric_order = [key for key in METRIC_SPECS if key in raw.columns]
    labels = {key: spec["label"] for key, spec in METRIC_SPECS.items()}
    matrix = (
        raw.set_index("model_label")[metric_order]
        .T.rename(index=labels)
        .reindex([labels[key] for key in metric_order])
    )
    matrix = matrix[[display_name_for_model_id(model_id) for model_id in model_order if display_name_for_model_id(model_id) in matrix.columns]]
    return raw, matrix


def allocation_weights_matrix(
    artifacts: list[dict[str, Any]],
    model_order: list[str],
) -> pd.DataFrame | None:
    """Return comparative allocation weights by asset and model."""
    frames: list[pd.DataFrame] = []
    for model_id in model_order:
        artifact = first_artifact(
            artifacts,
            output_type="allocation_weights",
            model_id=model_id,
            format_="csv",
            status="available",
        )
        if not artifact:
            continue
        df = load_artifact_dataframe(str(artifact["artifact_id"]))
        if df is None or df.empty:
            continue
        frame = df.rename(columns={"weight": display_name_for_model_id(model_id)}).copy()
        frames.append(frame)

    if not frames:
        return None

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="asset", how="outer")
    return merged.fillna(0.0)


def model_output_dataframe(
    artifacts: list[dict[str, Any]],
    *,
    model_id: str,
    output_type: str,
) -> pd.DataFrame | None:
    """Return one model-specific CSV artifact."""
    artifact = first_artifact(
        artifacts,
        output_type=output_type,
        model_id=model_id,
        format_="csv",
        status="available",
    )
    if not artifact:
        return None
    return load_artifact_dataframe(str(artifact["artifact_id"]))


def preferred_download_artifact(
    artifacts: list[dict[str, Any]],
    *,
    output_type: str,
    model_id: str | None = None,
) -> dict[str, Any] | None:
    """Return the preferred visible download artifact for one section."""
    preferred_formats = ["png", "csv", "md", "json", "txt"]
    for format_ in preferred_formats:
        artifact = first_artifact(
            artifacts,
            output_type=output_type,
            model_id=model_id,
            format_=format_,
            status="available",
        )
        if artifact:
            return artifact
    return None


def build_ranking_summary(
    raw_summary: pd.DataFrame | None,
    *,
    objective: str | None,
    risk_appetite: str | None,
    failed_models: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a deterministic ranking summary for the review opening."""
    if raw_summary is None or raw_summary.empty:
        return {
            "objective": objective,
            "risk_appetite": risk_appetite,
            "best_model_id": None,
            "best_metric": None,
            "ordering": [],
            "failed_models": failed_models,
        }

    metric_name, direction = OBJECTIVE_RANKING_METRIC.get(
        objective or "",
        ("sharpe_ratio", "higher"),
    )
    if metric_name not in raw_summary.columns:
        metric_name = "sharpe_ratio"
        direction = "higher"

    ranking = raw_summary[["model_id", metric_name]].copy()
    ranking = ranking[ranking[metric_name].notna()]
    ascending = direction == "lower"
    ranking = ranking.sort_values(metric_name, ascending=ascending, kind="stable")
    ordering = [
        {
            "model_id": str(row["model_id"]),
            "label": display_name_for_model_id(str(row["model_id"])),
            "metric": metric_name,
            "value": float(row[metric_name]),
        }
        for _, row in ranking.iterrows()
    ]
    best_model_id = ordering[0]["model_id"] if ordering else None
    return {
        "objective": objective,
        "risk_appetite": risk_appetite,
        "best_model_id": best_model_id,
        "best_metric": metric_name,
        "best_metric_label": METRIC_SPECS.get(metric_name, {}).get("label", metric_name),
        "ordering": ordering,
        "failed_models": failed_models,
    }


def summary_for_review_ai(
    raw_summary: pd.DataFrame | None,
    *,
    model_order: list[str],
    failed_models: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the review summary payload for AI calls."""
    rows = raw_summary.to_dict("records") if raw_summary is not None else []
    return {
        "successful_models": [
            {"model_id": model_id, "label": display_name_for_model_id(model_id)}
            for model_id in model_order
        ],
        "summary_metrics": rows,
        "failed_models": failed_models,
    }


def metric_display_value(value: float | int | str | None) -> str:
    """Format one metric value for human display."""
    if value is None:
        return "Unavailable"
    if isinstance(value, str):
        return value
    numeric = float(value)
    if math.isnan(numeric):
        return "Unavailable"
    return f"{numeric:.2f}"


def metric_row_styles(row: pd.Series, better: str) -> list[str]:
    """Return dataframe style strings for one metric row."""
    numeric = pd.to_numeric(row, errors="coerce")
    valid = numeric.dropna()
    styles = [""] * len(row)
    if valid.empty:
        return styles

    best_value = valid.min() if better == "lower" else valid.max()
    worst_value = valid.max() if better == "lower" else valid.min()

    for index, value in enumerate(numeric):
        if pd.isna(value):
            styles[index] = "color: #6b7280;"
        elif value == best_value:
            styles[index] = "background-color: rgba(74, 222, 128, 0.28);"
        elif value == worst_value and len(valid) > 1:
            styles[index] = "background-color: rgba(248, 113, 113, 0.24);"
        else:
            styles[index] = "background-color: rgba(250, 204, 21, 0.20);"
    return styles


def missing_artifact_reason(artifact: dict[str, Any] | None) -> str:
    """Return a user-facing missing-artifact explanation."""
    if not artifact:
        return GENERIC_MISSING_ARTIFACT_MESSAGE
    return str(artifact.get("reason") or GENERIC_MISSING_ARTIFACT_MESSAGE)
