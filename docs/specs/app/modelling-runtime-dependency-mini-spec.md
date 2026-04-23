| Metadata | Value |
|---|---|
| created | 2026-04-23 09:16:09 BST |
| last_updated | 2026-04-23 09:16:09 BST |

# Modelling Runtime Dependency Mini Spec

## Status

Approved by the Orchestrator Agent.

## Target Files

- Root `pyproject.toml`.
- Project setup docs owned by the Orchestrator Agent, where applicable.

## Requested Owner

- Orchestrator Agent approves and integrates shared dependency changes.
- Modelling Agent runs the feasibility spike after dependencies are available.

## Proposed Change

Add the initial modelling/runtime dependencies needed for the local Python Streamlit app:

```toml
requires-python = ">=3.11,<3.12"

dependencies = [
  "pandas",
  "numpy",
  "riskfolio-lib",
  "cvxpy",
  "scipy",
  "scikit-learn",
  "plotly",
]
```

## Solver Note

- Do not pin a special solver yet unless `riskfolio-lib` or `cvxpy` installation proves one is needed.
- The first feasibility spike should test the default solvers installed with `cvxpy`.
- If Mean Variance or Risk Parity fails due to solver availability, the Modelling Agent should propose the smallest additional solver dependency after evidence from the spike.

## Reason

The Modelling Agent needs these dependencies to implement and validate:

- canonical pandas price dataframe transformations.
- Mean Variance via `riskfolio-lib`.
- Risk Parity via `riskfolio-lib`.
- HRP via `riskfolio-lib`.
- summary metrics and chart-ready artifacts.
- local Python runtime feasibility for `riskfolio-lib`, `cvxpy`, and solvers.

## Interface And Contract Impact

- Enables `/app/processing/**` implementation.
- Does not change frontend or storage contracts.
- Does not introduce a backend service.
- Keeps runtime aligned with local Streamlit/Python V1.

## Risks And Dependencies

- `riskfolio-lib` and `cvxpy` may have solver compatibility constraints.
- Python `3.11` is preferred for the first spike; Python `3.12+` should not be assumed until proven.
- `pyproject.toml` is shared cross-agent territory, so Modelling should not edit it directly before Orchestrator approval.

## Orchestrator Decision

- Approved.
- Root `pyproject.toml` should be created using the dependencies in this mini spec.
- Streamlit, Perplexity, and other non-modelling dependencies are outside this mini spec and should be added through their owning agent workflows or a later Orchestrator-approved dependency update.
