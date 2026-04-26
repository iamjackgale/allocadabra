"""Reusable transformations and portfolio review metrics."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np
import pandas as pd


ANNUALIZATION_FACTOR = 365
ROLLING_VOL_WINDOW = 30
OMEGA_THRESHOLD = 0.0
SORTINO_TARGET = 0.0
TAIL_CONFIDENCE_LEVEL = 0.95

UNAVAILABLE_MESSAGES = {
    "insufficient_returns": "Not enough return observations are available to compute this metric.",
    "zero_volatility": "Portfolio volatility is zero, so this ratio is not defined.",
    "zero_drawdown": "No drawdown was observed, so this ratio is not defined.",
    "no_negative_returns": "No returns below the target threshold were observed.",
    "tail_sample_unavailable": "The required tail sample is unavailable for this metric.",
    "calculation_failed": "The metric could not be calculated for this model output.",
}


@dataclass(frozen=True)
class TransformationSet:
    """Standard transformation registry output for model and review logic."""

    prices: pd.DataFrame
    daily_returns: pd.DataFrame
    mean_returns: pd.Series
    covariance_matrix: pd.DataFrame
    correlation_matrix: pd.DataFrame
    normalized_price_index: pd.DataFrame


@dataclass(frozen=True)
class MetricUnavailableReason:
    """Stable user-facing reason for a non-computable summary metric."""

    model_id: str
    metric: str
    reason_code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SummaryMetricsResult:
    """Summary metric values plus unavailable metadata."""

    values: dict[str, float | str]
    unavailable_reasons: list[MetricUnavailableReason]


def build_transformations(prices: pd.DataFrame) -> TransformationSet:
    """Build the initial transformation set used by supported models."""
    daily_returns = prices.pct_change(fill_method=None).dropna(how="any")
    if daily_returns.empty:
        raise ValueError("Daily returns are empty after price cleaning.")

    return TransformationSet(
        prices=prices,
        daily_returns=daily_returns,
        mean_returns=daily_returns.mean(),
        covariance_matrix=daily_returns.cov(),
        correlation_matrix=daily_returns.corr(),
        normalized_price_index=normalized_price_index(prices),
    )


def normalized_price_index(prices: pd.DataFrame, start_value: float = 100.0) -> pd.DataFrame:
    """Index each price series to a common starting value."""
    first_valid = prices.apply(lambda column: column.dropna().iloc[0])
    return prices.divide(first_valid).multiply(start_value)


def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Apply static weights to daily asset returns."""
    aligned_weights = weights.reindex(returns.columns).astype(float)
    return returns.dot(aligned_weights).rename("portfolio_return")


def cumulative_performance(returns: pd.Series) -> pd.Series:
    """Compounded portfolio return path from daily returns."""
    return ((1.0 + returns).cumprod() - 1.0).rename("cumulative_return")


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Drawdown path from compounded wealth."""
    wealth = (1.0 + returns).cumprod()
    return (wealth / wealth.cummax() - 1.0).rename("drawdown")


def rolling_volatility(
    returns: pd.Series,
    *,
    window: int = ROLLING_VOL_WINDOW,
    annualization_factor: int = ANNUALIZATION_FACTOR,
) -> pd.Series:
    """Annualized rolling volatility from daily portfolio returns."""
    return (returns.rolling(window).std() * math.sqrt(annualization_factor)).rename(
        "rolling_volatility"
    )


def allocation_over_time(dates: pd.Index, weights: pd.Series) -> pd.DataFrame:
    """Repeat static optimized weights across the modelling dates."""
    frame = pd.DataFrame(
        [weights.reindex(weights.index).astype(float).to_dict() for _ in dates],
        index=dates,
    )
    frame.index.name = "date"
    return frame.reset_index()


def rolling_allocation_over_time(
    returns: pd.DataFrame,
    model_id: str,
    checkpoint_dates: list,
    *,
    min_observations: int = 60,
) -> pd.DataFrame:
    """Re-optimise weights at each monthly checkpoint and return a row per checkpoint."""
    from app.processing.models import run_supported_model

    n_assets = len(returns.columns)
    equal_weights = {asset: 1.0 / n_assets for asset in returns.columns}

    rows = []
    for d in checkpoint_dates:
        returns_slice = returns.loc[returns.index <= d]
        if len(returns_slice) < min_observations:
            weights_dict = equal_weights
        else:
            try:
                result = run_supported_model(model_id, returns_slice)
                weights_dict = result.weights.reindex(returns.columns).astype(float).to_dict()
            except Exception:
                weights_dict = equal_weights
        rows.append({"date": d, **weights_dict})

    return pd.DataFrame(rows, columns=["date"] + list(returns.columns))


def allocation_weights_table(weights: pd.Series) -> pd.DataFrame:
    """CSV-ready final allocation weights table."""
    return pd.DataFrame({"asset": weights.index, "weight": weights.astype(float).values})


def portfolio_path_tables(
    returns: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return cumulative performance, drawdown, and rolling volatility tables."""
    cumulative = cumulative_performance(returns)
    drawdown = drawdown_series(returns)
    rolling = rolling_volatility(returns)
    return (
        _series_to_table(cumulative),
        _series_to_table(drawdown),
        _series_to_table(rolling),
    )


def summary_metrics_for_model(
    *,
    model_id: str,
    returns: pd.Series,
) -> dict[str, float | str]:
    """Compute side-by-side metrics for one successful model."""
    return summary_metrics_for_model_with_reasons(model_id=model_id, returns=returns).values


def summary_metrics_for_model_with_reasons(
    *,
    model_id: str,
    returns: pd.Series,
) -> SummaryMetricsResult:
    """Compute side-by-side metrics and explicit unavailable reasons."""
    clean_returns = returns.dropna().astype(float)
    if clean_returns.empty:
        raise ValueError("Portfolio returns are empty.")

    cumulative = cumulative_performance(clean_returns)
    drawdown = drawdown_series(clean_returns)
    total_return = float(cumulative.iloc[-1])
    max_drawdown = float(drawdown.min())
    annual_return = _annualized_return(total_return, len(clean_returns))
    annual_volatility = float(clean_returns.std() * math.sqrt(ANNUALIZATION_FACTOR))
    downside = clean_returns[clean_returns < SORTINO_TARGET] - SORTINO_TARGET
    downside_deviation = float(downside.std() * math.sqrt(ANNUALIZATION_FACTOR))

    reasons: list[MetricUnavailableReason] = []
    values: dict[str, float | str] = {
        "model_id": model_id,
        "total_return_pct": _pct(total_return),
        "max_drawdown_pct": _pct(max_drawdown),
        "annualized_return_pct": _pct(annual_return),
        "annualized_volatility_pct": _pct(annual_volatility),
    }
    values["sharpe_ratio"] = _metric_value(
        model_id=model_id,
        metric="sharpe_ratio",
        reason_code="zero_volatility",
        reasons=reasons,
        compute=lambda: _safe_ratio_or_nan(annual_return, annual_volatility),
    )
    values["calmar_ratio"] = _metric_value(
        model_id=model_id,
        metric="calmar_ratio",
        reason_code="zero_drawdown",
        reasons=reasons,
        compute=lambda: _safe_ratio_or_nan(annual_return, abs(max_drawdown)),
    )
    values["omega_ratio"] = _metric_value(
        model_id=model_id,
        metric="omega_ratio",
        reason_code="no_negative_returns",
        reasons=reasons,
        compute=lambda: _omega_ratio(clean_returns),
    )
    values["sortino_ratio"] = _metric_value(
        model_id=model_id,
        metric="sortino_ratio",
        reason_code="no_negative_returns",
        reasons=reasons,
        compute=lambda: _safe_ratio_or_nan(annual_return, downside_deviation),
    )
    values["30d_volatility_pct"] = _metric_value(
        model_id=model_id,
        metric="30d_volatility_pct",
        reason_code="insufficient_returns",
        reasons=reasons,
        compute=lambda: _pct(_latest_rolling_volatility(clean_returns)),
    )
    values["avg_drawdown_pct"] = _metric_value(
        model_id=model_id,
        metric="avg_drawdown_pct",
        reason_code="zero_drawdown",
        reasons=reasons,
        compute=lambda: _pct(float(drawdown[drawdown < 0].mean())),
    )
    values["kurtosis"] = _metric_value(
        model_id=model_id,
        metric="kurtosis",
        reason_code="insufficient_returns",
        reasons=reasons,
        compute=lambda: float(clean_returns.kurtosis()),
    )
    values["skewness"] = _metric_value(
        model_id=model_id,
        metric="skewness",
        reason_code="insufficient_returns",
        reasons=reasons,
        compute=lambda: float(clean_returns.skew()),
    )
    values["cvar_pct"] = _metric_value(
        model_id=model_id,
        metric="cvar_pct",
        reason_code="tail_sample_unavailable",
        reasons=reasons,
        compute=lambda: _pct(_tail_mean(clean_returns, lower=True)),
    )
    values["cdar_pct"] = _metric_value(
        model_id=model_id,
        metric="cdar_pct",
        reason_code="tail_sample_unavailable",
        reasons=reasons,
        compute=lambda: _pct(_tail_mean(drawdown, lower=True)),
    )
    return SummaryMetricsResult(values=values, unavailable_reasons=reasons)


def summary_metrics_table(rows: list[dict[str, float | str]]) -> pd.DataFrame:
    """Build the comparison metrics CSV."""
    frame = pd.DataFrame(rows)
    for column in frame.columns:
        if column == "model_id":
            continue
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.replace([np.inf, -np.inf], np.nan).where(pd.notna(frame), None)


def summary_metric_unavailable_table(
    rows: list[MetricUnavailableReason],
) -> pd.DataFrame:
    """Build the companion CSV explaining unavailable summary metrics."""
    columns = ["model_id", "metric", "reason_code", "message"]
    return pd.DataFrame([row.to_dict() for row in rows], columns=columns)


def risk_contribution_table(weights: pd.Series, covariance: pd.DataFrame) -> pd.DataFrame:
    """Variance risk contribution by asset for a static allocation."""
    aligned_weights = weights.reindex(covariance.columns).astype(float)
    cov = covariance.loc[aligned_weights.index, aligned_weights.index]
    marginal = cov.dot(aligned_weights)
    portfolio_variance = float(aligned_weights.dot(marginal))
    if not np.isfinite(portfolio_variance) or portfolio_variance <= 0:
        raise ValueError("Portfolio variance is not positive.")
    contribution = aligned_weights * marginal / portfolio_variance
    return pd.DataFrame(
        {
            "asset": contribution.index,
            "weight": aligned_weights.values,
            "risk_contribution": contribution.values,
        }
    )


def _series_to_table(series: pd.Series) -> pd.DataFrame:
    frame = series.to_frame()
    frame.index.name = "date"
    return frame.reset_index()


def _annualized_return(total_return: float, observations: int) -> float:
    if observations <= 0 or total_return <= -1:
        return float("nan")
    return float((1.0 + total_return) ** (ANNUALIZATION_FACTOR / observations) - 1.0)


def _omega_ratio(returns: pd.Series) -> float:
    excess = returns - OMEGA_THRESHOLD
    gains = excess[excess > 0].sum()
    losses = abs(excess[excess < 0].sum())
    return _safe_ratio_or_nan(float(gains), float(losses))


def _tail_mean(series: pd.Series, *, lower: bool) -> float:
    clean = series.dropna().astype(float)
    if clean.empty:
        return float("nan")
    quantile = 1.0 - TAIL_CONFIDENCE_LEVEL if lower else TAIL_CONFIDENCE_LEVEL
    threshold = clean.quantile(quantile)
    tail = clean[clean <= threshold] if lower else clean[clean >= threshold]
    return float(tail.mean())


def _metric_value(
    *,
    model_id: str,
    metric: str,
    reason_code: str,
    reasons: list[MetricUnavailableReason],
    compute: Callable[[], float],
) -> float:
    try:
        value = float(compute())
    except Exception:
        reasons.append(_unavailable_reason(model_id, metric, "calculation_failed"))
        return float("nan")
    if np.isfinite(value):
        return value
    reasons.append(_unavailable_reason(model_id, metric, reason_code))
    return float("nan")


def _unavailable_reason(
    model_id: str,
    metric: str,
    reason_code: str,
) -> MetricUnavailableReason:
    return MetricUnavailableReason(
        model_id=model_id,
        metric=metric,
        reason_code=reason_code,
        message=UNAVAILABLE_MESSAGES.get(reason_code, UNAVAILABLE_MESSAGES["calculation_failed"]),
    )


def _latest_rolling_volatility(returns: pd.Series) -> float:
    rolling = rolling_volatility(returns).dropna()
    if rolling.empty:
        return float("nan")
    return float(rolling.iloc[-1])


def _safe_ratio_or_nan(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or denominator == 0:
        return float("nan")
    return float(numerator / denominator)


def _pct(value: float) -> float:
    return float(value * 100.0) if np.isfinite(value) else float("nan")
