"""Riskfolio-Lib model execution for the initial supported model set."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd


logger = logging.getLogger(__name__)

MEAN_VARIANCE = "mean_variance"
RISK_PARITY = "risk_parity"
HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"
HIERARCHICAL_EQUAL_RISK = "hierarchical_equal_risk"

SUPPORTED_MODELS: dict[str, str] = {
    MEAN_VARIANCE: "Mean Variance",
    RISK_PARITY: "Risk Parity",
    HIERARCHICAL_RISK_PARITY: "Hierarchical Risk Parity",
    HIERARCHICAL_EQUAL_RISK: "Hierarchical Equal Risk",
}


class ModelExecutionError(RuntimeError):
    """Raised when one model cannot produce usable weights."""


@dataclass(frozen=True)
class ModelResult:
    """Successful model execution output."""

    model_id: str
    label: str
    weights: pd.Series
    raw_weights: pd.DataFrame
    efficient_frontier: pd.DataFrame | None = None


@dataclass(frozen=True)
class ModelFailure:
    """User-facing model failure reason."""

    model_id: str
    label: str
    stage: str
    reason: str
    exception_type: str

    def to_dict(self) -> dict[str, str]:
        return {
            "model_id": self.model_id,
            "label": self.label,
            "stage": self.stage,
            "reason": self.reason,
            "exception_type": self.exception_type,
        }


def run_supported_model(model_id: str, returns: pd.DataFrame) -> ModelResult:
    """Run one supported Riskfolio-Lib model and return normalized weights."""
    if model_id not in SUPPORTED_MODELS:
        raise ModelExecutionError(f"Unsupported model: {model_id}.")
    if returns.empty:
        raise ModelExecutionError("Daily returns are empty.")

    if model_id == MEAN_VARIANCE:
        return _run_mean_variance(returns)
    if model_id == RISK_PARITY:
        return _run_risk_parity(returns)
    if model_id == HIERARCHICAL_EQUAL_RISK:
        return _run_herc(returns)
    return _run_hrp(returns)


def model_failure_from_exception(
    *,
    model_id: str,
    exc: Exception,
    stage: str = "model_execution",
) -> ModelFailure:
    """Create a UI-safe model failure object."""
    label = SUPPORTED_MODELS.get(model_id, model_id.replace("_", " ").title())
    return ModelFailure(
        model_id=model_id,
        label=label,
        stage=stage,
        reason=_friendly_reason(exc),
        exception_type=type(exc).__name__,
    )


def _run_mean_variance(returns: pd.DataFrame) -> ModelResult:
    import riskfolio as rp

    port = rp.Portfolio(returns=returns)
    port.assets_stats(method_mu="hist", method_cov="hist")
    raw_weights = port.optimization(
        model="Classic",
        rm="MV",
        obj="Sharpe",
        rf=0,
        l=0,
        hist=True,
    )
    weights = _normalize_weights(MEAN_VARIANCE, raw_weights)
    efficient_frontier = _efficient_frontier(port, returns)
    return ModelResult(
        model_id=MEAN_VARIANCE,
        label=SUPPORTED_MODELS[MEAN_VARIANCE],
        weights=weights,
        raw_weights=raw_weights,
        efficient_frontier=efficient_frontier,
    )


def _run_risk_parity(returns: pd.DataFrame) -> ModelResult:
    import riskfolio as rp

    port = rp.Portfolio(returns=returns)
    port.assets_stats(method_mu="hist", method_cov="hist")
    raw_weights = port.rp_optimization(
        model="Classic",
        rm="MV",
        rf=0,
        b=None,
        hist=True,
    )
    return ModelResult(
        model_id=RISK_PARITY,
        label=SUPPORTED_MODELS[RISK_PARITY],
        weights=_normalize_weights(RISK_PARITY, raw_weights),
        raw_weights=raw_weights,
    )


def _run_herc(returns: pd.DataFrame) -> ModelResult:
    import riskfolio as rp

    port = rp.HCPortfolio(returns=returns)
    raw_weights = port.optimization(
        model="HERC",
        codependence="pearson",
        rm="MV",
        rf=0,
        linkage="single",
        max_k=10,
        leaf_order=True,
    )
    return ModelResult(
        model_id=HIERARCHICAL_EQUAL_RISK,
        label=SUPPORTED_MODELS[HIERARCHICAL_EQUAL_RISK],
        weights=_normalize_weights(HIERARCHICAL_EQUAL_RISK, raw_weights),
        raw_weights=raw_weights,
    )


def _run_hrp(returns: pd.DataFrame) -> ModelResult:
    import riskfolio as rp

    port = rp.HCPortfolio(returns=returns)
    raw_weights = port.optimization(
        model="HRP",
        codependence="pearson",
        rm="MV",
        rf=0,
        linkage="single",
        max_k=10,
        leaf_order=True,
    )
    return ModelResult(
        model_id=HIERARCHICAL_RISK_PARITY,
        label=SUPPORTED_MODELS[HIERARCHICAL_RISK_PARITY],
        weights=_normalize_weights(HIERARCHICAL_RISK_PARITY, raw_weights),
        raw_weights=raw_weights,
    )


def _normalize_weights(model_id: str, raw_weights: pd.DataFrame | None) -> pd.Series:
    if raw_weights is None or raw_weights.empty:
        raise ModelExecutionError(f"{SUPPORTED_MODELS[model_id]} returned no weights.")

    weights = raw_weights.iloc[:, 0].astype(float)
    if not weights.notna().all():
        raise ModelExecutionError(f"{SUPPORTED_MODELS[model_id]} returned invalid weights.")

    total = float(weights.sum())
    if total <= 0:
        raise ModelExecutionError(f"{SUPPORTED_MODELS[model_id]} returned zero total weight.")

    weights = weights / total
    if (weights < -1e-8).any():
        raise ModelExecutionError(f"{SUPPORTED_MODELS[model_id]} returned negative weights.")
    return weights.clip(lower=0).rename("weight")


def _efficient_frontier(port: object, returns: pd.DataFrame) -> pd.DataFrame | None:
    try:
        frontier = port.efficient_frontier(
            model="Classic",
            rm="MV",
            points=50,
            rf=0,
            hist=True,
        )
    except Exception as exc:
        logger.warning("Efficient frontier unavailable: %s", exc)
        return None

    if frontier is None or frontier.empty:
        return None

    frame = frontier.astype(float).T.reset_index(drop=True)
    frame.insert(0, "frontier_point", range(1, len(frame) + 1))
    mean_returns = returns.mean() * 365
    covariance = returns.cov() * 365
    asset_columns = [column for column in frame.columns if column != "frontier_point"]
    expected_returns: list[float] = []
    volatilities: list[float] = []
    for _, row in frame[asset_columns].iterrows():
        weights = row.astype(float)
        expected_returns.append(float(weights.dot(mean_returns.reindex(asset_columns))))
        variance = float(weights.dot(covariance.loc[asset_columns, asset_columns]).dot(weights))
        volatilities.append(max(variance, 0.0) ** 0.5)
    frame.insert(1, "annualized_return", expected_returns)
    frame.insert(2, "annualized_volatility", volatilities)
    return frame


def _friendly_reason(exc: Exception) -> str:
    if isinstance(exc, ModelExecutionError):
        return str(exc)
    return (
        "This model could not be completed with the selected data and current solver "
        "configuration."
    )
