created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 14:17:17 BST

# Dataset Building Spec

## Purpose

Define how a modelling dataset is prepared after the user confirms the AI-generated model plan.

## Runtime Recommendation

Dataset building should use Python and pandas inside the Streamlit/local Python app runtime.

The V1 route is a single local Python web app rather than pure in-browser Python execution. Pyodide/browser-only execution is deferred unless the Orchestrator Agent changes the architecture.

## Inputs

- Selected assets from the active user input state.
- Normalized CoinGecko price history from local market-data cache.
- Confirmed AI-generated modelling plan.
- Confirmed model subset.

## Canonical Price Dataframe

Build one canonical pandas dataframe from cached CoinGecko price data before creating model-specific transformed datasets.

Shape:

| Element | Rule |
|---|---|
| Index | UTC date from normalized CoinGecko price data. |
| Columns | One price column per selected asset. |
| Column display name | `[SYMBOL]_price`. |
| Cell values | Numeric floats. |

Column collision rule:

- CoinGecko symbols are not guaranteed to be unique.
- User-facing column labels should use `[SYMBOL]_price`.
- Internal metadata must map each column to CoinGecko `id`, `symbol`, and `name`.
- If two selected assets share the same symbol, the internal mapping must preserve uniqueness by CoinGecko `id`; the UI/export layer must avoid ambiguous labels.

Date alignment:

- Use the union of all available dates across selected assets.
- Forward-fill missing prices only after an asset's first valid price.
- Do not backfill dates before an asset's first valid price.
- Rows before every retained asset has its first valid price may contain missing values during construction, but model-specific transformations must handle or reject unusable rows.

History window:

- The initial maximum modelling window is 365 daily observations because the CoinGecko price request uses `days=365`.
- Assets do not need the full 365 days of history.
- A selected asset must have at least 90 valid daily prices or it is rejected for modelling.

## Transformation Registry

The repo should expose standard transformation functions. Models should declare which transformations they require instead of embedding ad hoc transformation logic.

Only the first three models are initial build scope:

- Mean Variance.
- Risk Parity.
- Hierarchical Risk Parity.

Worst Case, Ordered Weighted Average, and Hierarchical Equal Risk are documented only to prepare for possible future inclusion. Do not implement or prioritize them until the initial three models are stable.

Initial standard transformations:

| Transformation | Description |
|---|---|
| Price dataframe | Canonical aligned dataframe of daily asset prices. |
| Daily returns | Percentage change from daily prices, equivalent to `data[assets].pct_change().dropna()`. |
| Mean returns | Mean return series derived from daily returns. |
| Covariance matrix | Asset return covariance matrix. |
| Correlation matrix | Asset return correlation matrix. |
| Cumulative returns | Compounded return path for selected assets. |
| Normalized price index | Price series indexed to a common starting value for comparison. |
| Drawdown series | Drawdown path derived from cumulative returns. |
| Rolling volatility | Rolling volatility series, initially including a 30-day window for review metrics. |
| Benchmark return series | Benchmark return/cumulative return series once benchmark construction is defined. |
| Tail-risk inputs | Sorted or thresholded return/drawdown data for CVaR, CDaR, Omega, and Sortino metrics. |
| Worst-case uncertainty stats | Uncertainty-set inputs generated from returns for future worst-case optimization. |
| OWA tail weights | Ordered weighted average vectors such as CVaR or worst-realization weights for future OWA optimization. |
| Cluster tree data | Hierarchical cluster/dendrogram data for HRP and possible future HERC review views. |

## Model Transformation Matrix

The mapping between supported models and required transformations should be represented as a table.

Example structure:

| Model | Build Scope | Price dataframe | Daily returns | Mean returns | Covariance matrix | Correlation matrix | Cumulative returns | Normalized price index | Worst-case uncertainty stats | OWA tail weights | Cluster tree data |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean Variance | Initial | X | X | X | X |  |  |  |  |  |  |
| Risk Parity | Initial | X | X | X | X |  |  |  |  |  |  |
| Hierarchical Risk Parity | Initial | X | X |  | X | X |  |  |  |  | X |
| Worst Case | Future only | X | X | X | X |  |  |  | X |  |  |
| Ordered Weighted Average | Future only | X | X | X | X |  |  |  |  | X |  |
| Hierarchical Equal Risk | Future only | X | X |  | X | X |  |  |  |  | X |

Only rows with `Build Scope = Initial` should be implemented in the first modelling build.

## Validation And Failure Rules

- Reject modelling runs with more than 10 selected assets.
- Reject selected assets with fewer than 90 valid daily prices.
- Reject runs where required price history cannot be fetched or found in cache.
- Reject transformed datasets that are empty after required cleaning.
- Warn or reject when a model-specific transformation produces excessive missing data.
- Errors must be suitable for display in the UI.
- QA/Validation Agent should define test cases and user-facing error expectations for these failures.

## Outputs

- Canonical price dataframe.
- Model-specific transformed datasets.
- Transformation metadata showing source assets, CoinGecko IDs, date range, row counts, dropped rows, and warnings.

Export:

- Dataframes may be exported as `.csv` after the model generation process succeeds.
- The exact set of exported dataframes will be decided later.

## Relationship To Other Specs

- `/docs/specs/data-backend/coingecko-api.md` defines normalized source price data.
- `/docs/specs/data-backend/data-storage.md` defines locally cached market data.
- `/docs/specs/data-backend/session-storage.md` defines active user inputs and current model output storage.
- `/docs/specs/data-backend/riskfolio-lib.md` defines supported models and completes the model transformation matrix.
- `/docs/prompts/agents/qa-validation-agent.md` should include validation coverage for dataset-building errors.

## Open Questions

- Exact local runtime dependency set for `riskfolio-lib`, solvers, charting, and export.
- Exact internal metadata schema for dataframe column-to-asset mapping.
- Exact thresholds for "excessive" missing/forward-filled data beyond the 90 valid price minimum.
