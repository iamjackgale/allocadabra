"""End-to-end modelling output generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.processing.artifacts import ArtifactWriter
from app.processing.dataset import DatasetBuildError, build_canonical_price_dataframe
from app.processing.models import (
    HIERARCHICAL_RISK_PARITY,
    MEAN_VARIANCE,
    RISK_PARITY,
    SUPPORTED_MODELS,
    ModelFailure,
    ModelResult,
    model_failure_from_exception,
    run_supported_model,
)
from app.processing.progress import ProgressCallback, make_progress_event
from app.processing.transformations import (
    allocation_over_time,
    allocation_weights_table,
    build_transformations,
    portfolio_path_tables,
    portfolio_returns,
    risk_contribution_table,
    summary_metrics_for_model,
    summary_metrics_table,
)
from app.storage.paths import MODEL_OUTPUTS_DIR
from app.storage.schemas import SCHEMA_VERSION, utc_now_iso


logger = logging.getLogger(__name__)

MAX_SELECTED_MODELS = 3


def generate_modelling_outputs(
    *,
    selected_assets: list[dict[str, Any]],
    price_history_by_id: dict[str, list[dict[str, Any]]],
    selected_models: list[str] | None = None,
    output_dir: Path = MODEL_OUTPUTS_DIR,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Generate model-owned Review/export artifacts without zip packaging."""
    model_ids = selected_models or list(SUPPORTED_MODELS)
    if len(model_ids) > MAX_SELECTED_MODELS:
        raise ValueError("Compare no more than 3 models in a single run.")

    writer = ArtifactWriter(output_dir)
    _notify_progress(
        progress_callback,
        phase="datasets",
        status="started",
        message="Building the canonical modelling dataset.",
    )
    dataset = build_canonical_price_dataframe(
        selected_assets=selected_assets,
        price_history_by_id=price_history_by_id,
    )
    transformations = build_transformations(dataset.prices)
    _notify_progress(
        progress_callback,
        phase="datasets",
        status="completed",
        message="Modelling dataset has been prepared.",
    )

    canonical = dataset.prices.reset_index()
    writer.write_dataframe(
        df=canonical,
        relative_path="canonical-modelling-dataset.csv",
        artifact_id="canonical_modelling_dataset_csv",
        label="Canonical modelling dataset",
        category="general",
        output_type="canonical_modelling_dataset",
    )

    successes: list[ModelResult] = []
    failures: list[ModelFailure] = []
    metric_rows: list[dict[str, float | str]] = []

    _notify_progress(
        progress_callback,
        phase="modelling",
        status="started",
        message="Running selected portfolio models.",
    )
    for model_id in model_ids:
        try:
            result = run_supported_model(model_id, transformations.daily_returns)
            successes.append(result)
            metric_rows.append(
                summary_metrics_for_model(
                    model_id=model_id,
                    returns=portfolio_returns(transformations.daily_returns, result.weights),
                )
            )
            _write_model_artifacts(
                writer=writer,
                result=result,
                prices=dataset.prices,
                returns=transformations.daily_returns,
                covariance=transformations.covariance_matrix,
                correlation=transformations.correlation_matrix,
            )
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_id, exc)
            failures.append(model_failure_from_exception(model_id=model_id, exc=exc))
    _notify_progress(
        progress_callback,
        phase="modelling",
        status="completed" if successes else "failed",
        message="Selected model runs are complete."
        if successes
        else "No selected model completed successfully.",
    )

    _notify_progress(
        progress_callback,
        phase="analysis",
        status="started",
        message="Preparing summary metrics and review artifacts.",
    )
    if successes:
        metrics = summary_metrics_table(metric_rows)
        writer.write_dataframe(
            df=metrics,
            relative_path="summary-metrics.csv",
            artifact_id="summary_metrics_csv",
            label="Summary metrics",
            category="general",
            output_type="summary_metrics",
        )

    if failures:
        writer.write_json(
            payload={"failed_models": [failure.to_dict() for failure in failures]},
            relative_path="failed-models.json",
            artifact_id="failed_models_json",
            label="Failed model reasons",
            category="failure",
            output_type="failed_models",
            individual_download_enabled=True,
        )
    _notify_progress(
        progress_callback,
        phase="analysis",
        status="completed",
        message="Metrics and chart data are ready.",
    )
    _notify_progress(
        progress_callback,
        phase="outputs",
        status="started",
        message="Finalizing model output artifacts.",
    )
    _notify_progress(
        progress_callback,
        phase="outputs",
        status="completed" if successes else "failed",
        message="Model output artifacts are ready."
        if successes
        else "No models completed successfully.",
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "ok": bool(successes),
        "output_dir": str(output_dir),
        "successful_models": [result.model_id for result in successes],
        "failed_models": [failure.to_dict() for failure in failures],
        "dataset_metadata": dataset.metadata,
        "artifacts": [entry.to_dict() for entry in writer.entries],
    }


def _notify_progress(
    callback: ProgressCallback | None,
    *,
    phase: str,
    status: str,
    message: str,
) -> None:
    if callback is not None:
        callback(
            make_progress_event(
                phase=phase,  # type: ignore[arg-type]
                status=status,  # type: ignore[arg-type]
                message=message,
            )
        )


def _write_model_artifacts(
    *,
    writer: ArtifactWriter,
    result: ModelResult,
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    covariance: pd.DataFrame,
    correlation: pd.DataFrame,
) -> None:
    model_id = result.model_id
    model_dir = f"models/{model_id}"
    portfolio = portfolio_returns(returns, result.weights)
    cumulative, drawdown, rolling = portfolio_path_tables(portfolio)
    allocation_time = allocation_over_time(prices.index, result.weights)
    weights = allocation_weights_table(result.weights)

    writer.write_dataframe(
        df=weights,
        relative_path=f"{model_dir}/allocation-weights.csv",
        artifact_id=f"{model_id}_allocation_weights_csv",
        label=f"{result.label} allocation weights",
        category="model",
        model_id=model_id,
        output_type="allocation_weights",
    )
    _write_chart_pair(
        writer=writer,
        df=allocation_time,
        csv_path=f"{model_dir}/allocation-over-time.csv",
        png_path=f"{model_dir}/allocation-over-time.png",
        artifact_prefix=f"{model_id}_allocation_over_time",
        label=f"{result.label} allocation over time",
        model_id=model_id,
        output_type="allocation_over_time",
        plotter=lambda ax: _plot_stacked_area(ax, allocation_time, "Allocation over time", "Weight"),
    )
    _write_chart_pair(
        writer=writer,
        df=cumulative,
        csv_path=f"{model_dir}/cumulative-performance.csv",
        png_path=f"{model_dir}/cumulative-performance.png",
        artifact_prefix=f"{model_id}_cumulative_performance",
        label=f"{result.label} cumulative performance",
        model_id=model_id,
        output_type="cumulative_performance",
        plotter=lambda ax: _plot_line(ax, cumulative, "cumulative_return", "Cumulative performance"),
    )
    _write_chart_pair(
        writer=writer,
        df=drawdown,
        csv_path=f"{model_dir}/drawdown.csv",
        png_path=f"{model_dir}/drawdown.png",
        artifact_prefix=f"{model_id}_drawdown",
        label=f"{result.label} drawdown",
        model_id=model_id,
        output_type="drawdown",
        plotter=lambda ax: _plot_line(ax, drawdown, "drawdown", "Drawdown"),
    )
    _write_chart_pair(
        writer=writer,
        df=rolling,
        csv_path=f"{model_dir}/rolling-volatility.csv",
        png_path=f"{model_dir}/rolling-volatility.png",
        artifact_prefix=f"{model_id}_rolling_volatility",
        label=f"{result.label} rolling volatility",
        model_id=model_id,
        output_type="rolling_volatility",
        plotter=lambda ax: _plot_line(ax, rolling, "rolling_volatility", "30-day rolling volatility"),
    )

    if model_id in {RISK_PARITY, HIERARCHICAL_RISK_PARITY}:
        _write_risk_contribution(writer, result, covariance)

    if model_id == MEAN_VARIANCE:
        _write_efficient_frontier(writer, result)

    if model_id == HIERARCHICAL_RISK_PARITY:
        _write_dendrogram(writer, result, correlation)


def _write_chart_pair(
    *,
    writer: ArtifactWriter,
    df: pd.DataFrame,
    csv_path: str,
    png_path: str,
    artifact_prefix: str,
    label: str,
    model_id: str,
    output_type: str,
    plotter: object,
) -> None:
    writer.write_dataframe(
        df=df,
        relative_path=csv_path,
        artifact_id=f"{artifact_prefix}_csv",
        label=f"{label} data",
        category="model",
        model_id=model_id,
        output_type=output_type,
        individual_download_enabled=False,
    )
    writer.write_png_from_plot(
        relative_path=png_path,
        artifact_id=f"{artifact_prefix}_png",
        label=f"{label} chart",
        category="model",
        model_id=model_id,
        output_type=output_type,
        plotter=plotter,
    )


def _write_risk_contribution(
    writer: ArtifactWriter,
    result: ModelResult,
    covariance: pd.DataFrame,
) -> None:
    try:
        risk = risk_contribution_table(result.weights, covariance)
    except Exception as exc:
        writer.add_missing(
            artifact_id=f"{result.model_id}_risk_contribution",
            label=f"{result.label} risk contribution",
            category="model",
            model_id=result.model_id,
            output_type="risk_contribution",
            reason=f"Risk contribution could not be computed: {exc}",
        )
        return

    _write_chart_pair(
        writer=writer,
        df=risk,
        csv_path=f"models/{result.model_id}/risk-contribution.csv",
        png_path=f"models/{result.model_id}/risk-contribution.png",
        artifact_prefix=f"{result.model_id}_risk_contribution",
        label=f"{result.label} risk contribution",
        model_id=result.model_id,
        output_type="risk_contribution",
        plotter=lambda ax: _plot_bar(ax, risk, "asset", "risk_contribution", "Risk contribution"),
    )


def _write_efficient_frontier(writer: ArtifactWriter, result: ModelResult) -> None:
    if result.efficient_frontier is None or result.efficient_frontier.empty:
        writer.add_missing(
            artifact_id=f"{result.model_id}_efficient_frontier",
            label=f"{result.label} efficient frontier",
            category="model",
            model_id=result.model_id,
            output_type="efficient_frontier",
            reason="Efficient frontier data was unavailable for this model run.",
        )
        return

    _write_chart_pair(
        writer=writer,
        df=result.efficient_frontier,
        csv_path=f"models/{result.model_id}/efficient-frontier.csv",
        png_path=f"models/{result.model_id}/efficient-frontier.png",
        artifact_prefix=f"{result.model_id}_efficient_frontier",
        label=f"{result.label} efficient frontier",
        model_id=result.model_id,
        output_type="efficient_frontier",
        plotter=lambda ax: _plot_frontier_weights(ax, result.efficient_frontier),
    )


def _write_dendrogram(
    writer: ArtifactWriter,
    result: ModelResult,
    correlation: pd.DataFrame,
) -> None:
    try:
        linkage = _cluster_linkage(correlation)
    except Exception as exc:
        writer.add_missing(
            artifact_id=f"{result.model_id}_dendrogram",
            label=f"{result.label} dendrogram",
            category="model",
            model_id=result.model_id,
            output_type="dendrogram",
            reason=f"Dendrogram data could not be computed: {exc}",
        )
        return

    writer.write_dataframe(
        df=linkage["data"],
        relative_path=f"models/{result.model_id}/dendrogram.csv",
        artifact_id=f"{result.model_id}_dendrogram_csv",
        label=f"{result.label} dendrogram data",
        category="model",
        model_id=result.model_id,
        output_type="dendrogram",
        individual_download_enabled=False,
    )
    writer.write_png_from_plot(
        relative_path=f"models/{result.model_id}/dendrogram.png",
        artifact_id=f"{result.model_id}_dendrogram_png",
        label=f"{result.label} dendrogram chart",
        category="model",
        model_id=result.model_id,
        output_type="dendrogram",
        plotter=lambda ax: _plot_dendrogram(ax, linkage["matrix"], list(correlation.columns)),
    )


def _cluster_linkage(correlation: pd.DataFrame) -> dict[str, object]:
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform

    distance = (1.0 - correlation.fillna(0).clip(-1, 1)).clip(lower=0)
    matrix = linkage(squareform(distance.to_numpy(), checks=False), method="single")
    data = pd.DataFrame(
        matrix,
        columns=["cluster_a", "cluster_b", "distance", "sample_count"],
    )
    data.insert(0, "merge_step", range(1, len(data) + 1))
    return {"matrix": matrix, "data": data}


def _plot_line(ax: object, df: pd.DataFrame, value_column: str, title: str) -> None:
    ax.plot(pd.to_datetime(df["date"]), df[value_column])
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(value_column.replace("_", " ").title())
    ax.grid(True, alpha=0.25)


def _plot_stacked_area(ax: object, df: pd.DataFrame, title: str, ylabel: str) -> None:
    dates = pd.to_datetime(df["date"])
    value_columns = [column for column in df.columns if column != "date"]
    ax.stackplot(dates, [df[column] for column in value_columns], labels=value_columns)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left", fontsize="small")


def _plot_bar(ax: object, df: pd.DataFrame, x_column: str, y_column: str, title: str) -> None:
    ax.bar(df[x_column], df[y_column])
    ax.set_title(title)
    ax.set_xlabel(x_column.replace("_", " ").title())
    ax.set_ylabel(y_column.replace("_", " ").title())
    ax.tick_params(axis="x", rotation=35)


def _plot_frontier_weights(ax: object, df: pd.DataFrame) -> None:
    assets = [column for column in df.columns if column != "frontier_point"]
    for asset in assets:
        ax.plot(df["frontier_point"], df[asset], label=asset)
    ax.set_title("Efficient frontier weights")
    ax.set_xlabel("Frontier point")
    ax.set_ylabel("Weight")
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.25)


def _plot_dendrogram(ax: object, matrix: object, labels: list[str]) -> None:
    from scipy.cluster.hierarchy import dendrogram

    dendrogram(matrix, labels=labels, ax=ax)
    ax.set_title("Hierarchical clustering dendrogram")
    ax.tick_params(axis="x", rotation=35)
