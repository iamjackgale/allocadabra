"""Reusable transformations and portfolio review metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


ANNUALIZATION_FACTOR = 365
ROLLING_VOL_WINDOW = 30
OMEGA_THRESHOLD = 0.0
SORTINO_TARGET = 0.0
TAIL_CONFIDENCE_LEVEL = 0.95


@dataclass(frozen=True)
class TransformationSet:
    """Standard transformation registry output for model and review logic."""

    prices: pd.DataFrame
    daily_returns: pd.DataFrame
    mean_returns: pd.Series
    covariance_matrix: pd.DataFrame
    correlation_matrix: pd.DataFrame
    normalized_price_index: pd.DataFrame


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
    clean_returns = returns.dropna().astype(float)
    if clean_returns.empty:
        raise ValueError("Portfolio returns are empty.")

    cumulative = cumulative_performance(clean_returns)
    drawdown = drawdown_series(clean_returns)
    total_return = float(cumulative.iloc[-1])
    max_drawdown = float(drawdown.min())
    annual_return = _annualized_return(total_return, len(clean_returns))
    annual_volatility = float(clean_returns.std() * math.sqrt(ANNUALIZATION_FACTOR))
    thirty_day_volatility = float(rolling_volatility(clean_returns).dropna().iloc[-1])
    downside = clean_returns[clean_returns < SORTINO_TARGET] - SORTINO_TARGET
    downside_deviation = float(downside.std() * math.sqrt(ANNUALIZATION_FACTOR))

    return {
        "model_id": model_id,
        "total_return_pct": _pct(total_return),
        "max_drawdown_pct": _pct(max_drawdown),
        "sharpe_ratio": _safe_ratio(annual_return, annual_volatility),
        "calmar_ratio": _safe_ratio(annual_return, abs(max_drawdown)),
        "omega_ratio": _omega_ratio(clean_returns),
        "sortino_ratio": _safe_ratio(annual_return, downside_deviation),
        "annualized_return_pct": _pct(annual_return),
        "annualized_volatility_pct": _pct(annual_volatility),
        "30d_volatility_pct": _pct(thirty_day_volatility),
        "avg_drawdown_pct": _pct(float(drawdown[drawdown < 0].mean())),
        "kurtosis": float(clean_returns.kurtosis()),
        "skewness": float(clean_returns.skew()),
        "cvar_pct": _pct(_tail_mean(clean_returns, lower=True)),
        "cdar_pct": _pct(_tail_mean(drawdown, lower=True)),
    }


def summary_metrics_table(rows: list[dict[str, float | str]]) -> pd.DataFrame:
    """Build the comparison metrics CSV."""
    return pd.DataFrame(rows)


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
    return _safe_ratio(float(gains), float(losses))


def _tail_mean(series: pd.Series, *, lower: bool) -> float:
    clean = series.dropna().astype(float)
    if clean.empty:
        return float("nan")
    quantile = 1.0 - TAIL_CONFIDENCE_LEVEL if lower else TAIL_CONFIDENCE_LEVEL
    threshold = clean.quantile(quantile)
    tail = clean[clean <= threshold] if lower else clean[clean >= threshold]
    return float(tail.mean())


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or denominator == 0:
        return float("nan")
    return float(numerator / denominator)


def _pct(value: float) -> float:
    return float(value * 100.0) if np.isfinite(value) else float("nan")
