| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-23 09:16:09 BST |

# Riskfolio-Lib Spec

## Purpose

Define how Allocadabra uses `riskfolio-lib` to run supported models and generate outputs for users.

## Tutorial Inputs Reviewed

Initial transformation requirements were derived from these local tutorial notebooks:

- `/Users/iamjackgale/Downloads/Tutorial_1_Classic_Mean_Risk_Optimization.ipynb`
- `/Users/iamjackgale/Downloads/Tutorial_14_Mean_Ulcer_Index_Portfolio_Optimization.ipynb`
- `/Users/iamjackgale/Downloads/Tutorial_24_Hierarchical_Risk_Parity_(HRP)_Portfolio_Optimization.ipynb`
- `/Users/iamjackgale/Downloads/Tutorial_12_Worst_Case_Mean_Variance_Portfolio_Optimization.ipynb`
- `/Users/iamjackgale/Downloads/Tutorial_37_OWA_Portfolio_Optimization.ipynb`
- `/Users/iamjackgale/Downloads/Tutorial_25_Hierarchical_Equal_Risk_Contribution_(HERC)_Portfolio_Optimization.ipynb`

## Model Roadmap

The full course-aligned model roadmap is:

| Student-facing model | Riskfolio-Lib area | Status |
|---|---|---|
| Mean Variance | Classic mean-risk portfolio optimization | Initial supported model |
| Risk Parity | Risk parity optimization | Initial supported model |
| Hierarchical Risk Parity | Hierarchical clustering portfolio optimization, `HRP` | Initial supported model |
| Worst Case | Worst case mean variance optimization | Later candidate |
| Ordered Weighted Average | OWA portfolio optimization | Later candidate |
| Hierarchical Equal Risk | Hierarchical clustering portfolio optimization, likely `HERC`/`HERC2` | Later candidate |

Initial version should support no more than 3 models per comparison run.

Only Mean Variance, Risk Parity, and Hierarchical Risk Parity are initial build scope. Worst Case, Ordered Weighted Average, and Hierarchical Equal Risk are documented for future inclusion only.

## Initial Model Defaults

### Mean Variance

Purpose:

- Baseline return/risk optimizer for student comparison.

Riskfolio-Lib pattern:

```python
port = rp.Portfolio(returns=Y)
port.assets_stats(method_mu="hist", method_cov="hist")
w = port.optimization(model="Classic", rm="MV", obj="Sharpe", rf=0, l=0, hist=True)
```

Initial defaults:

| Setting | Value |
|---|---|
| `model` | `Classic` |
| `rm` | `MV` |
| `obj` | `Sharpe` |
| `method_mu` | `hist` |
| `method_cov` | `hist` |
| `hist` | `True` |
| `rf` | `0` |
| `l` | `0` |

Required transformations:

- Canonical price dataframe.
- Daily returns dataframe.
- Expected return estimates via `assets_stats`.
- Covariance estimates via `assets_stats`.
- Efficient frontier weights if enabled for output exploration.

### Risk Parity

Purpose:

- Risk-budgeting contrast to Mean Variance.

Riskfolio-Lib pattern:

```python
port = rp.Portfolio(returns=Y)
port.assets_stats(method_mu="hist", method_cov="hist")
w = port.rp_optimization(model="Classic", rm="MV", rf=0, b=None, hist=True)
```

Initial defaults:

| Setting | Value |
|---|---|
| `model` | `Classic` |
| `rm` | `MV` |
| `method_mu` | `hist` |
| `method_cov` | `hist` |
| `hist` | `True` |
| `rf` | `0` |
| `b` | `None` |

Required transformations:

- Canonical price dataframe.
- Daily returns dataframe.
- Expected return estimates via `assets_stats`.
- Covariance estimates via `assets_stats`.
- Risk contribution data for output exploration.

### Hierarchical Risk Parity

Purpose:

- Clustering-based allocation model for comparison with optimizer-based methods.

Riskfolio-Lib pattern:

```python
port = rp.HCPortfolio(returns=Y)
w = port.optimization(
    model="HRP",
    codependence="pearson",
    rm="MV",
    rf=0,
    linkage="single",
    max_k=10,
    leaf_order=True,
)
```

Initial defaults:

| Setting | Value |
|---|---|
| `model` | `HRP` |
| `codependence` | `pearson` |
| `rm` | `MV` |
| `rf` | `0` |
| `linkage` | `single` |
| `max_k` | `10` |
| `leaf_order` | `True` |

Required transformations:

- Canonical price dataframe.
- Daily returns dataframe.
- Correlation/codependence input from returns.
- Covariance matrix for risk contribution output.
- Dendrogram/cluster data if enabled for output exploration.

## Future Candidate Preparation

The following models should not be implemented in the first modelling build. They are documented so that the initial transformation registry and architecture do not block later expansion.

### Worst Case

Riskfolio-Lib pattern:

```python
port = rp.Portfolio(returns=Y)
port.assets_stats(method_mu="hist", method_cov="hist")
port.wc_stats(box=box, ellip=ellip, q=q, n_sim=n_sim, window=window, dmu=dmu, dcov=dcov, seed=seed)
w = port.wc_optimization(obj=obj, rf=rf, l=l, Umu=Umu, Ucov=Ucov)
```

Additional requirements:

- Uncertainty-set parameter selection.
- `wc_stats` estimation from returns.
- Potentially heavy simulation settings such as `n_sim`.
- Solver compatibility checks.

Reason to defer:

- Higher parameter complexity and solver/runtime risk.

### Ordered Weighted Average

Riskfolio-Lib pattern:

```python
port = rp.Portfolio(returns=Y)
port.assets_stats(method_mu="hist", method_cov="hist")
owa_w = rp.owa_cvar(len(Y), alpha=alpha)
w = port.owa_optimization(obj=obj, owa_w=owa_w, rf=rf, l=l)
```

Additional requirements:

- OWA weight vectors such as `rp.owa_cvar(...)` or `rp.owa_wr(...)`.
- Tail-risk parameter selection such as `alpha`.
- Potential solver compatibility checks.

Reason to defer:

- More complex explanation and parameterization for a student-facing first version.

### Hierarchical Equal Risk

Riskfolio-Lib pattern:

```python
port = rp.HCPortfolio(returns=Y)
w = port.optimization(
    model="HERC",
    codependence="pearson",
    rm="MV",
    rf=0,
    linkage="ward",
    max_k=10,
    leaf_order=True,
)
```

Additional requirements:

- Hierarchical clustering settings similar to HRP.
- Cluster plot/dendrogram data.
- Clear student-facing distinction from HRP.

Reason to defer:

- Closely related to HRP and better added after the first hierarchical model is stable.

## Required Dataframe Manipulations

All three initial models require:

1. Build canonical price dataframe from cached CoinGecko prices.
2. Select asset price columns for the confirmed scope.
3. Convert price columns to daily percentage returns with `pct_change().dropna()`.
4. Preserve asset metadata mapping between dataframe columns and CoinGecko `id`, `symbol`, and `name`.

Additional tutorial-derived manipulations:

| Manipulation | Used By | Purpose |
|---|---|---|
| `Y.mean()` | HRP output exploration | Risk contribution/charting context. |
| `Y.cov()` | HRP output exploration and risk contribution charts | Covariance matrix for risk contribution visualisations. |
| `port.assets_stats(method_mu="hist", method_cov="hist")` | Mean Variance, Risk Parity | Estimate expected returns and covariance from historical returns. |
| `port.efficient_frontier(...)` | Mean Variance optional exploration | Generate frontier weights for charting. |
| `pd.concat([...], axis=1)` | Optional model/risk-measure comparisons | Combine weights across model variants for comparison tables/charts. |
| `port.wc_stats(...)` | Future Worst Case | Estimate uncertainty-set inputs. |
| `port.wc_optimization(...)` | Future Worst Case | Run worst-case optimization. |
| `rp.owa_cvar(...)` / `rp.owa_wr(...)` | Future OWA | Build OWA tail-weight vectors. |
| `port.owa_optimization(...)` | Future OWA | Run OWA optimization. |
| `rp.plot_clusters(...)` | Future HERC exploration | Generate cluster/dendrogram review context. |

## Output Artifacts

Initial model outputs should support:

- Weights dataframe for each model.
- Comparable summary metrics.
- Allocation weights chart data.
- Allocation-over-time chart data across the 365-day modelling window.
- Cumulative performance chart data.
- Drawdown chart data.
- Rolling volatility chart data.
- Efficient frontier data for Mean Variance where available.
- Risk contribution data for Risk Parity and HRP where available.
- Dendrogram/cluster data for HRP where available.

Model output tables should be exportable as `.csv` after successful model generation. Chart images should be exportable as `.png` in V1.

## Allocation-Over-Time Chart

The review UI should be able to show portfolio allocation over the modelling period where supporting data is available.

Initial support:

- Generate chart-ready allocation series for the 365-day modelling window.
- Use stacked-area style data where each date has asset weights that sum to `1.0`.
- Include one series per asset using the user-facing asset symbol, with metadata mapping back to CoinGecko ID.

Important distinction:

- For models that produce a single static optimized allocation, allocation-over-time can initially be represented as constant weights repeated across the modelling dates.
- If the app later supports rolling optimization or scheduled rebalancing, allocation-over-time should represent recomputed weights at each rebalance date.

V1 decision:

- Show constant optimized weights across the full period for models that produce a single static optimized allocation.

## Side-By-Side Summary Metrics

Initial result comparison should support the following summary metrics where the required data is available.

| Metric | Initial Support | Data Needed | Notes |
|---|---|---|---|
| Total Return [%] | Yes | Portfolio cumulative return series | Return over the model window. |
| Max Drawdown [%] | Yes | Portfolio cumulative return/drawdown series | Maximum peak-to-trough drawdown. |
| Sharpe Ratio | Yes | Daily returns, risk-free rate | Initial `rf` default is `0`. |
| Calmar Ratio | Yes | Annualized return, max drawdown | Requires max drawdown. |
| Omega Ratio | Yes | Daily returns, threshold | Initial threshold is `0`. |
| Sortino Ratio | Yes | Daily returns, downside deviation, risk-free/target return | Initial target return is `0`. |
| Annualized Return % | Yes | Daily returns or cumulative return series | Annualize daily crypto data with factor `365`. |
| Annualized Volatility % | Yes | Daily returns | Annualize daily crypto data with factor `365`. |
| 30d Volatility % | Yes | Daily returns | Rolling 30-day volatility. |
| Avg Drawdown % | Yes | Drawdown series | Average drawdown over drawdown periods. |
| Kurtosis | Yes | Daily returns | Distribution shape metric. |
| Skewness | Yes | Daily returns | Distribution asymmetry metric. |
| CVaR % | Yes | Daily returns, confidence level | Initial confidence level is `95%`. |
| CDaR % | Yes | Drawdown series, confidence level | Initial confidence level is `95%`. |

Metric notes:

- These metrics are feasible from daily returns, cumulative returns, and drawdown series.
- Approved V1 metric defaults: annualization factor `365`, Omega threshold `0`, Sortino target return `0`, CVaR confidence level `95%`, and CDaR confidence level `95%`.
- Benchmark metrics should not be implemented until the benchmark construction is explicitly defined.
- Metrics should be computed consistently for every successful model output so side-by-side comparisons are fair.
- If a metric cannot be computed for a model, the review output should show a clear missing/unavailable reason rather than silently omitting it.

## Validation And Failure Rules

- Reject comparison runs with more than 3 selected models.
- Reject modelling runs with more than 10 assets.
- Reject model execution if the daily returns dataframe is empty.
- Reject model execution if required model transformations are unavailable.
- Report Riskfolio-Lib solver/optimization failures as user-facing model failure messages.
- If one selected model fails and others succeed, the review UI should show available results and the failed model reason.

## Runtime Risk

`riskfolio-lib` depends on optimization/scientific packages and solvers. The initial implementation must prove that the local Streamlit/Python runtime can install and execute the initial three models before expanding to later candidates.

Pure browser/Pyodide execution is not part of the V1 runtime route unless the Orchestrator Agent changes the architecture.

## Dependency And Solver Ownership

- Use one root `pyproject.toml` as the shared project dependency source.
- The Modelling Agent owns the `riskfolio-lib`, `cvxpy`, and solver feasibility spike.
- The Modelling Agent should propose dependency additions as a mini spec before editing `pyproject.toml`, because the root dependency file is cross-agent shared territory.
- The Orchestrator Agent approves and integrates dependency changes into `pyproject.toml`.
- Start with local Python execution, not Pyodide or pure browser execution.
- Prefer Python `3.11` for the first feasibility spike unless the Modelling Agent proves a newer version works cleanly with `riskfolio-lib`, `cvxpy`, and required solvers.
- The initial dependency mini spec is approved at `/docs/specs/app/modelling-runtime-dependency-mini-spec.md`.

Approved initial modelling/runtime dependencies:

- `pandas`
- `numpy`
- `riskfolio-lib`
- `cvxpy`
- `scipy`
- `scikit-learn`
- `plotly`

Solver policy:

- Do not pin a special solver before the first feasibility spike.
- Test the default solvers installed with `cvxpy`.
- If solver availability blocks Mean Variance or Risk Parity, propose the smallest additional solver dependency with evidence from the spike.

## Relationship To Other Specs

- `/docs/specs/data-backend/dataset-building.md` defines canonical price dataframes and transformations.
- `/docs/specs/data-backend/session-storage.md` defines model output lifecycle.
- `/docs/specs/app/modelling-runtime-dependency-mini-spec.md` defines the approved initial modelling/runtime dependency update.
- `/docs/specs/frontend/model-review.md` will define how outputs are explored and downloaded.
- `/docs/specs/ai/review-agent.md` will define how AI reflects on model trade-offs.

## Open Questions

- Which local solver dependencies are required to execute all three initial `riskfolio-lib` model paths reliably.
- Which optional exploration artifacts to prioritize for the hackathon build.
- Whether Risk Parity should use `rm="MV"` initially or expose `UCI` later as a course extension.
- Benchmark construction for benchmark-return rows such as "BTC ETH MV Return".
