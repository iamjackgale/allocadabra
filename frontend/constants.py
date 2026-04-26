"""Frontend constants, labels, and UI metadata."""

from __future__ import annotations

from app.ai.models import SUPPORTED_MODELS


TREASURY_OBJECTIVES = [
    "Maximize Return",
    "Stable Performance",
    "Risk-Adjusted Returns",
    "Reduce Drawdowns",
    "Diversify Exposure",
]

TREASURY_OBJECTIVE_HELP = {
    "Maximize Return": "Prioritize higher modelled returns, accepting more risk if required.",
    "Stable Performance": "Favor smoother portfolio behaviour over aggressive upside.",
    "Risk-Adjusted Returns": "Look for stronger return efficiency relative to volatility.",
    "Reduce Drawdowns": "Focus on limiting deeper peak-to-trough declines.",
    "Diversify Exposure": "Prefer broader spread across assets and model behaviour.",
}

RISK_APPETITES = [
    "Very Low",
    "Low",
    "Medium",
    "High",
    "Very High",
]

RISK_APPETITE_HELP = {
    "Very Low": "Interpret results with a strong preference for lower volatility and drawdown.",
    "Low": "Lean toward steadier portfolios with limited downside swings.",
    "Medium": "Balance risk control and return-seeking outcomes.",
    "High": "Accept larger swings if the modelled upside improves.",
    "Very High": "Tolerate the widest swings when comparing model trade-offs.",
}

MODEL_LABELS = {model.model_id: model.display_name for model in SUPPORTED_MODELS}

MODEL_HELP = {
    "mean_variance": "Classic optimizer that searches for weights with stronger return and volatility trade-offs.",
    "risk_parity": "Balances portfolio risk contribution across assets instead of maximizing return directly.",
    "hierarchical_risk_parity": "Uses clustering to group related assets before allocating portfolio risk.",
    "hierarchical_equal_risk": "Extends hierarchical clustering to equalise risk contribution across asset clusters.",
}

PHASE_ACCENTS = {
    "configuration": {
        "rgb": "123, 191, 154",
        "solid": "#7bbf9a",
        "muted": "#d8f0e2",
    },
    "modelling": {
        "rgb": "205, 98, 98",
        "solid": "#cd6262",
        "muted": "#f7d7d7",
    },
    "review": {
        "rgb": "123, 191, 154",
        "solid": "#7bbf9a",
        "muted": "#d8f0e2",
    },
}

REVIEW_SECTIONS = [
    ("summary_metrics", "Summary metrics"),
    ("allocation_weights", "Allocation weights"),
    ("allocation_over_time", "Allocation over time"),
    ("cumulative_performance", "Cumulative performance"),
    ("drawdown", "Drawdown"),
    ("rolling_volatility", "Rolling volatility"),
    ("risk_contribution", "Risk contribution"),
    ("efficient_frontier", "Efficient frontier"),
    ("dendrogram", "Dendrogram"),
    ("modelling_plan", "Modelling plan"),
]

PER_MODEL_REVIEW_SECTIONS = {
    "allocation_over_time",
    "cumulative_performance",
    "drawdown",
    "rolling_volatility",
    "risk_contribution",
    "efficient_frontier",
    "dendrogram",
}

SECTION_HELP = {
    "summary_metrics": "Compare model outputs side by side using shared performance and risk metrics.",
    "allocation_weights": "Compare the final optimized asset weights across successful models.",
    "allocation_over_time": "Optimal weights re-calculated monthly over the past 12 months.",
    "cumulative_performance": "Compounded portfolio return path from the modelled daily return series.",
    "drawdown": "Peak-to-trough decline path derived from the modelled cumulative performance.",
    "rolling_volatility": "Annualized rolling 30-day volatility from the modelled portfolio returns.",
    "risk_contribution": "How much each asset contributes to overall modelled portfolio risk.",
    "efficient_frontier": "Mean Variance frontier output when the optimization can produce it.",
    "dendrogram": "Hierarchical clustering structure used by the HRP model.",
    "modelling_plan": "The confirmed plan accepted before modelling started.",
}

CHART_SECTION_DOWNLOAD_FORMAT = {
    "allocation_over_time": "png",
    "cumulative_performance": "png",
    "drawdown": "png",
    "rolling_volatility": "png",
    "risk_contribution": "png",
    "efficient_frontier": "png",
    "dendrogram": "png",
}

METRIC_SPECS = {
    "total_return_pct": {
        "label": "Total return",
        "description": "Return over the full model window. Higher is generally better.",
        "better": "higher",
    },
    "max_drawdown_pct": {
        "label": "Max drawdown",
        "description": "Largest peak-to-trough decline. Lower is generally better.",
        "better": "lower",
    },
    "sharpe_ratio": {
        "label": "Sharpe",
        "description": "Return earned per unit of volatility. Higher is generally better.",
        "better": "higher",
    },
    "calmar_ratio": {
        "label": "Calmar",
        "description": "Annualized return relative to max drawdown. Higher is generally better.",
        "better": "higher",
    },
    "omega_ratio": {
        "label": "Omega",
        "description": "Upside outcomes relative to downside outcomes. Higher is generally better.",
        "better": "higher",
    },
    "sortino_ratio": {
        "label": "Sortino",
        "description": "Return earned relative to downside deviation. Higher is generally better.",
        "better": "higher",
    },
    "annualized_return_pct": {
        "label": "Annualized return",
        "description": "Return scaled to a yearly rate from daily data. Higher is generally better.",
        "better": "higher",
    },
    "annualized_volatility_pct": {
        "label": "Annualized volatility",
        "description": "Yearly volatility estimate from daily returns. Lower is generally better.",
        "better": "lower",
    },
    "30d_volatility_pct": {
        "label": "30d volatility",
        "description": "Latest rolling 30-day annualized volatility. Lower is generally better.",
        "better": "lower",
    },
    "avg_drawdown_pct": {
        "label": "Average drawdown",
        "description": "Average size of drawdown periods. Lower is generally better.",
        "better": "lower",
    },
    "skewness": {
        "label": "Skewness",
        "description": "Distribution asymmetry of modelled returns. Interpretation depends on context.",
        "better": "higher",
    },
    "kurtosis": {
        "label": "Kurtosis",
        "description": "Tail-heaviness of modelled returns. Lower is often easier to tolerate.",
        "better": "lower",
    },
    "cvar_pct": {
        "label": "CVaR",
        "description": "Average loss in the worst tail of returns. Lower is generally better.",
        "better": "lower",
    },
    "cdar_pct": {
        "label": "CDaR",
        "description": "Average loss in the worst tail of drawdowns. Lower is generally better.",
        "better": "lower",
    },
}

OBJECTIVE_RANKING_METRIC = {
    "Maximize Return": ("annualized_return_pct", "higher"),
    "Stable Performance": ("annualized_volatility_pct", "lower"),
    "Risk-Adjusted Returns": ("sharpe_ratio", "higher"),
    "Reduce Drawdowns": ("max_drawdown_pct", "lower"),
    "Diversify Exposure": ("annualized_volatility_pct", "lower"),
}

GENERIC_MISSING_ARTIFACT_MESSAGE = "This artifact was not generated for this run."

