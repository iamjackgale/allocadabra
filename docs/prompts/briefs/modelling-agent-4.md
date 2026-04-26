| Metadata | Value |
|---|---|
| created | 2026-04-26 BST |
| last_updated | 2026-04-26 BST |
| prompt_used | 2026-04-26 BST |

# Modelling Agent Brief 4

You are the Modelling Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Read:

   - `/docs/tasks.md`
   - `/docs/specs/data-backend/riskfolio-lib.md`
   - `/app/processing/models.py`
   - `/frontend/constants.py`
   - `/app/ai/prompts.py`

## Primary Task

- `142`: Add Hierarchical Equal Risk Contribution (HERC) as a fourth supported model alongside
  Mean Variance, Risk Parity, and Hierarchical Risk Parity.

---

## Background

### Current models

`app/processing/models.py` defines three models:

```python
MEAN_VARIANCE = "mean_variance"
RISK_PARITY = "risk_parity"
HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"

SUPPORTED_MODELS: dict[str, str] = {
    MEAN_VARIANCE: "Mean Variance",
    RISK_PARITY: "Risk Parity",
    HIERARCHICAL_RISK_PARITY: "Hierarchical Risk Parity",
}
```

`run_supported_model` dispatches to `_run_hrp` for `hierarchical_risk_parity`:

```python
def run_supported_model(model_id: str, returns: pd.DataFrame) -> ModelResult:
    ...
    if model_id == MEAN_VARIANCE:
        return _run_mean_variance(returns)
    if model_id == RISK_PARITY:
        return _run_risk_parity(returns)
    return _run_hrp(returns)
```

`_run_hrp` uses `rp.HCPortfolio.optimization(model="HRP")`.

### Why HERC

HERC (Hierarchical Equal Risk Contribution) uses the same `rp.HCPortfolio` interface as
HRP — only the `model=` argument changes to `"HERC"`. It produces meaningfully different
allocations (risk contributions are equalised rather than weights equalised), requires no
new user-facing parameters, and slots in with near-zero risk of breaking existing models.

---

## Task 142 Requirements

### Step 1 — Add the constant and SUPPORTED_MODELS entry in `models.py`

```python
HIERARCHICAL_EQUAL_RISK = "hierarchical_equal_risk"
```

Add `HIERARCHICAL_EQUAL_RISK: "Hierarchical Equal Risk"` to `SUPPORTED_MODELS`.

### Step 2 — Add `_run_herc` implementation

```python
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
```

Use the same parameters as `_run_hrp` — only `model="HERC"` differs.

HERC does not produce an efficient frontier (no `efficient_frontier` field on
`HCPortfolio`), so leave `efficient_frontier` at its default of `None`.

### Step 3 — Update the dispatch in `run_supported_model`

Add a branch before the final fallback:

```python
if model_id == HIERARCHICAL_EQUAL_RISK:
    return _run_herc(returns)
```

The `_normalize_weights` and `model_failure_from_exception` helpers already handle
any `model_id` present in `SUPPORTED_MODELS`, so no changes are needed there.

### Step 4 — Add the label to `frontend/constants.py`

Locate `MODEL_LABELS` (or equivalent) in `frontend/constants.py`. Add:

```python
"hierarchical_equal_risk": "Hierarchical Equal Risk",
```

If the frontend derives labels from `SUPPORTED_MODELS` dynamically (e.g. by importing
from `app/processing/models.py`), no change is needed — confirm and document which
approach is in use.

### Step 5 — Update the AI prompt

In `app/ai/prompts.py`, find the section that lists supported models for the AI agent.
Add `hierarchical_equal_risk` (label: "Hierarchical Equal Risk") to the list. The AI
agent uses this to suggest appropriate models in the generated modelling plan.

Do not change any other prompt content — only extend the model list.

---

## Boundaries

Own:

- `/app/processing/models.py`
- `/frontend/constants.py`
- `/app/ai/prompts.py`

Do not edit:

- `/app/processing/runner.py`
- `/app/processing/transformations.py`
- `/app/processing/dataset.py`
- `/app/storage/**`
- `/app/ingestion/**`
- Shared dependency files

---

## Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/processing app/ai frontend
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

Then run a live smoke to confirm the new model executes without error:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/modelling_smoke.py
```

Inspect the output and confirm:

- `hierarchical_equal_risk` appears in the results alongside the existing three models.
- The HERC weights sum to approximately 1.0.
- The HERC weights differ from the HRP weights (confirming HERC is not simply
  repeating the HRP result — even small differences are sufficient).
- No existing model's weights changed (non-regression).

Document the model IDs present in the smoke output, the HERC weight sum, and whether
HERC/HRP weight difference was observed in `docs/validation/modelling-validation.md`.

---

## Reporting Back

When complete, report:

- task completed;
- files changed;
- validation commands and outcomes;
- the four model IDs present in the smoke output;
- HERC weight sum and whether it differs from HRP;
- any frontend/AI prompt changes needed (or confirmation that none were required).
