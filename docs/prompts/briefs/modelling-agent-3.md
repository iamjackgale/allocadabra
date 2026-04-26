| Metadata | Value |
|---|---|
| created | 2026-04-26 BST |
| last_updated | 2026-04-26 BST |
| prompt_used |  |

# Modelling Agent Brief 3

You are the Modelling Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Read:

   - `/docs/tasks.md`
   - `/docs/specs/data-backend/dataset-building.md`
   - `/app/processing/transformations.py`
   - `/app/processing/runner.py`
   - `/app/processing/models.py`

## Primary Task

- `140`: Replace the static allocation-over-time chart with a rolling 13-checkpoint
  monthly re-optimisation chart so the allocation chart shows genuine weight variation
  over time rather than repeated flat bands.

---

## Background

### Current behaviour

`transformations.allocation_over_time(dates, weights)` repeats a single set of
optimised weights (computed once from the full dataset) across every date in the
365-day window. The chart shows flat horizontal bands — the same allocation every day.

Call site in `runner._write_model_artifacts`:

```python
allocation_time = allocation_over_time(prices.index, result.weights)
```

### Required behaviour

Run the optimizer 13 times per model — once at each of 13 monthly checkpoints spanning
the past 12 months — and use those 13 weight snapshots to build the chart. The chart
will then show how the optimal allocation to each asset changes month to month.

---

## Task 140 Requirements

### Step 1 — Define the 13 checkpoint dates

Compute 13 dates in the runner (or pass the run date through):

- **Today**: the latest date present in the `returns` DataFrame (use
  `returns.index.max()` rather than `datetime.today()` to stay anchored to actual
  data).
- **12 months ago**: same day-of-month as today, 12 months earlier.
- **11 intermediate months**: same day-of-month, one per calendar month between the
  two endpoints.

```
checkpoints = [today - relativedelta(months=i) for i in range(13)]  # i=0..12
checkpoints.sort()  # oldest first so the chart reads left-to-right
```

Use `dateutil.relativedelta` (already available via the dependency tree) or an
equivalent month-subtraction that correctly handles month-end dates (e.g. January 31
minus 1 month → January 31 clamped to February 28/29).

If a checkpoint date falls on a weekend or a day with no price observation, use the
nearest available date that is on or before the checkpoint (i.e. `returns.index[
returns.index <= checkpoint].max()`). Skip the checkpoint entirely if no such date
exists in the index.

### Step 2 — Add `rolling_allocation_over_time` to `transformations.py`

New function signature:

```python
def rolling_allocation_over_time(
    returns: pd.DataFrame,
    model_id: str,
    checkpoint_dates: list,
    *,
    min_observations: int = 60,
) -> pd.DataFrame:
```

For each checkpoint date `d` in `checkpoint_dates` (oldest first):

1. Slice: `returns_slice = returns.loc[returns.index <= d]`
2. If `len(returns_slice) < min_observations`, fall back to equal weights
   (`1 / n_assets` for each asset).
3. Otherwise call `run_supported_model(model_id, returns_slice)` inside a try/except.
   On any exception, fall back to equal weights.
4. Append a row `{"date": d, **weights_dict}` to the output.

Return a DataFrame with columns `["date", asset_1, asset_2, ...]` and one row per
checkpoint, sorted by date ascending. The `date` column should contain Python
`datetime.date` values (or a datetime index) consistent with how `allocation_over_time`
currently formats its index.

**Important:** these extra optimizer calls are visualization-only. Any failure must
fall back silently to equal weights — never raise, never block artifact writing.

### Step 3 — Update the call site in `runner._write_model_artifacts`

Replace:

```python
allocation_time = allocation_over_time(prices.index, result.weights)
```

With:

```python
checkpoint_dates = _monthly_checkpoints(returns)
allocation_time = rolling_allocation_over_time(returns, model_id, checkpoint_dates)
```

Add a small private helper `_monthly_checkpoints(returns: pd.DataFrame) -> list`
to `runner.py` that computes the 13 dates as described in Step 1.

Remove the now-unused `allocation_over_time` import from `runner.py`. Leave
`allocation_over_time` in `transformations.py` if it is referenced by tests or other
callers; otherwise you may remove it.

### Step 4 — Update the subtitle in the frontend constant

In `frontend/constants.py` (or wherever the Review section descriptions live), find
the copy that currently reads:

> "V1 repeats each model's final optimized weights across the 365-day window."

Replace it with:

> "Optimal weights re-calculated monthly over the past 12 months."

If this string is defined in the frontend layer rather than the modelling layer, write
a one-line mini spec for the Frontend Agent and return it in your report rather than
editing `/frontend/**` directly.

---

## Boundaries

Own:

- `/app/processing/transformations.py`
- `/app/processing/runner.py`

Do not edit:

- `/app/processing/models.py` (call `run_supported_model` as-is)
- `/app/processing/dataset.py`
- `/frontend/**` — return a mini spec if a copy change is needed there
- `/app/storage/**`
- Shared dependency files

---

## Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/processing
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

Then run a live smoke to confirm the new chart is generated:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/modelling_smoke.py
```

Inspect the generated `allocation-over-time.csv` for at least one model and confirm:

- It has 13 rows (or fewer if early checkpoints had no data).
- The `date` column contains 13 distinct monthly dates.
- Asset weight columns sum to approximately 1.0 per row.
- At least one asset has a different weight in the first row vs the last row
  (confirming genuine variation, not repeated static weights).

Document the CSV row count, date range, and whether variation was observed in
`docs/validation/modelling-validation.md`.

---

## Reporting Back

When complete, report:

- task completed;
- files changed;
- validation commands and outcomes;
- the date range and row count of the generated `allocation-over-time.csv`;
- whether weight variation was observed across checkpoints;
- any mini spec needed for the Frontend Agent for the copy change.
