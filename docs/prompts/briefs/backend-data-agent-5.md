| Metadata | Value |
|---|---|
| created | 2026-04-25 BST |
| last_updated | 2026-04-25 BST |
| prompt_used | 2026-04-25 BST |

# Backend/Data Agent Brief 5

You are the Backend/Data Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Confirm whether `COINGECKO_API_KEY` is available through repo-root `.env` or shell environment before running live checks.
5. Read:

   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/data-backend/coingecko-api.md`
   - `/docs/specs/data-backend/data-storage.md`
   - `/docs/specs/data-backend/session-storage.md`
   - `/docs/specs/app/export-bundling.md`
   - `/docs/validation/backend-validation.md`
   - `/docs/validation/validation-gap-report-1.md`

## CoinGecko API Note

The current implementation at `app/ingestion/coingecko.py` is already using the correct endpoint
and authentication method:

- **Base URL:** `https://api.coingecko.com/api/v3`
- **Endpoint:** `GET /coins/{coin_id}/market_chart`
- **Auth header:** `x-cg-demo-api-key`
- **Parameters:** `vs_currency=usd`, `interval=daily`, `precision=full`, `days=365`

All of these are correct and supported on the CoinGecko Demo plan. No endpoint or auth changes
are needed. The 401 errors previously seen were due to an invalid API key, not a wrong
configuration. A valid Demo API key has now been placed in `.env` — proceed with live
validation.

## Primary Tasks

- `064`: Revisit the 2-day CoinGecko price-cache freshness tolerance after live validation.
- `135`: Add opt-in live CoinGecko smoke step to `scripts/backend_smoke.py`.
- `136`: Extend backend smoke coverage for export edge cases and session lifecycle transitions.

---

## Task 064 Requirements

**Status:** Previously BLOCKED on missing `COINGECKO_API_KEY`. Key is now available.

Confirm the 2-day CoinGecko price-cache freshness tolerance is appropriate for V1.

**Assessment criteria:**

1. Use the live key to fetch price history for at least one real token (e.g., `bitcoin`).
2. Check the latest date in the returned data against today's UTC date.
3. Assess whether a 2-day tolerance correctly covers the edge case where today's daily candle
   is not yet available at time of request (CoinGecko publishes prior UTC day data 10 minutes
   after midnight UTC).
4. Confirm that `days=365` with `interval=daily` consistently returns daily-granularity
   price points and that the normaliser handles the returned timestamps correctly.

**Acceptable outcomes:**

- **Complete with no change:** Live data confirms the latest daily point arrives within 1–2
  days of today and the current 2-day tolerance is correct. Update `data-storage.md` and
  `backend-validation.md` to document the live evidence. Mark `064` DONE.
- **Complete with tighter tolerance:** If live data reliably shows the latest point is always
  within 1 day, tighten the tolerance to 1 day, update `data-storage.md` and implementation
  code, and mark `064` DONE.
- **Blocked again:** If the key fails or live validation cannot run, document the exact failure
  and leave `064` BLOCKED.

Do not mark `064` complete from static reasoning alone — a live API call confirming the
actual data shape is required.

---

## Task 135 Requirements

Add an opt-in live validation step to `scripts/backend_smoke.py`.

**Step to add (gated on `COINGECKO_API_KEY` presence):**

When `COINGECKO_API_KEY` is set in the environment:

1. Instantiate `CoinGeckoClient`.
2. Call `client.fetch_market_chart("bitcoin")`.
3. Assert the result is a non-empty `list[PricePoint]`.
4. Assert `len(result) >= 90` (minimum dataset requirement).
5. Assert the latest `PricePoint.date` is no more than 2 days before today's UTC date.
6. Print `live coingecko smoke ok` and continue.

When `COINGECKO_API_KEY` is absent:

- Skip the live step with a single printed message: `COINGECKO_API_KEY not set — skipping live coingecko smoke`.
- Do not fail. The existing deterministic steps must still pass and the script must exit `0`.

The script's final line must remain `backend smoke ok` when all applicable steps pass.

Update `/docs/validation/backend-validation.md` with the new step description and the
outcome of your first live run.

---

## Task 136 Requirements

Extend `scripts/backend_smoke.py` to cover export and session lifecycle edge cases
identified in `docs/validation/validation-gap-report-1.md`.

All additions must be deterministic (no live API calls required) and use synthetic
fixture data consistent with the existing smoke script structure.

**Export edge cases to add:**

1. **Multi-model artifact layout.** Prepare an export bundle with synthetic artifacts for
   two models (`mean_variance` and `risk_parity`). Assert that model-specific artifacts
   land under `models/mean_variance/` and `models/risk_parity/` in the manifest paths.
   Assert that root artifacts (`summary-metrics.csv`, `manifest.json`) are not nested under
   a model path.

2. **Missing-placeholder types.** For each supported optional artifact type (allocation
   weights, efficient frontier, chart PNG), assert that when the artifact is absent from the
   modelling output the manifest entry is still present, `available=False`, and the
   placeholder file contains the expected missing-artifact text. Do not hard-code the
   message — import and compare against the constant from the app layer.

3. **Download All zip exclusions.** Assert that `get_review_download_all()` excludes raw
   CoinGecko cache files and AI chat transcripts from the zip manifest entry. Assert that
   it includes all available modelling artifacts.

**Session lifecycle transitions to add:**

4. **Reconfigure from review-ready state.** After calling `prepare_review_export_bundle(...)`,
   call `reset_configuration()`. Assert that `get_workflow_state()` returns a state that is
   no longer review-ready and that `get_review_export_manifest()` returns an empty or
   unavailable result (not a stale manifest from the previous run).

5. **Re-run after reset.** After the reset above, re-call `update_workflow_inputs(...)`,
   `store_generated_plan(...)`, `confirm_modelling_plan(...)`, and
   `prepare_review_export_bundle(...)` with fresh synthetic data. Assert the second
   bundle is independent of the first.

Keep each new step clearly labelled in the script output (e.g., `step 5 — multi-model layout ok`).

---

## Boundaries

Own:

- `/app/storage/**`
- `/app/ingestion/**`
- `scripts/backend_smoke.py`
- Backend/Data-owned validation docs

Do not edit:

- `/app/processing/**`
- `/frontend/**`
- `/app/ai/**`
- Shared dependency files

If a gap requires another agent's code to change, write a mini spec rather than patching
their code.

---

## Validation

Run at minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/storage app/ingestion
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 scripts/backend_smoke.py
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

For task `135`, document whether `COINGECKO_API_KEY` was available and what the live
step returned. Include the latest `PricePoint.date` observed and the count of price
points returned.

For task `064`, document the freshness evidence that supports your conclusion about the
2-day tolerance.

Update `/docs/validation/backend-validation.md` with commands and outcomes.

---

## Reporting Back

When complete, report:

- tasks completed;
- files changed;
- validation commands and outcomes;
- whether live CoinGecko smoke ran and what data shape was returned;
- whether task `064` is closed or still blocked, and why;
- whether any export or session lifecycle gaps were found beyond those listed above;
- any mini specs needed for other agents.
