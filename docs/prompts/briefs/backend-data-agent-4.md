| Metadata | Value |
|---|---|
| created | 2026-04-25 07:44:37 BST |
| last_updated | 2026-04-25 07:44:37 BST |
| prompt_used | 2026-04-25 07:48:19 BST |

# Backend/Data Agent Brief 4

You are the Backend/Data Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Add this prompt to /briefs if not already included.
3. Fill in the `prompt_used` timestamp above as the first edit.
4. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
5. Confirm whether `COINGECKO_API_KEY` is available through repo-root `.env` or shell environment before running live cache/freshness checks.
6. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/data-backend/coingecko-api.md`
   - `/docs/specs/data-backend/data-storage.md`
   - `/docs/specs/data-backend/session-storage.md`
   - `/docs/specs/app/export-bundling.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/validation/backend-validation.md`
   - `/docs/validation/modelling-validation.md`
   - `/docs/validation/frontend-validation.md`
   - `/docs/validation/general-validation.md`

## Primary Tasks

- `103`: Verify export handoff compatibility between Modelling outputs and Backend/Data bundle and manifest preparation in a real end-to-end app flow.
- `064`: Revisit the 2-day CoinGecko price-cache freshness tolerance after live Streamlit/runtime integration and tighten it if validation shows stale data risk.
- `083`: Support Modelling Agent integration only if the modelling run contract exposes a concrete storage/export adapter gap.

## Current Context

The first Backend/Data implementation is complete:

- CoinGecko API client and cache paths exist.
- Active workflow/session state exists.
- Deterministic validation issue codes exist.
- Export bundle and manifest generation exists.
- `scripts/backend_smoke.py` provides deterministic fixture coverage for cache/session/export paths.

The next Backend/Data task is integration verification, not broad refactoring.

## Task 103 Requirements

Verify that real Modelling-produced artifacts can be handed to Backend/Data export preparation without ad hoc adapters.

Use the current app-layer handoff from `/docs/specs/app/frontend-backend-modelling-integration.md`:

1. Frontend calls `app.processing.run_active_modelling(...)`.
2. Modelling returns:
   - `artifacts`
   - `failed_models`
   - `missing_artifacts`
   - `successful_models`
   - `errors`
   - `output_dir`
3. Frontend calls Backend/Data export preparation with:
   - `modelling_artifacts`
   - `failed_models`
   - `missing_artifacts`
4. Backend/Data prepares:
   - export manifest
   - individual artifact download metadata
   - `Download All` bundle metadata
   - Review-ready workflow state

Check at minimum:

- Modelling artifact descriptors are accepted without field-name translation hacks.
- Required root artifacts are present where modelling succeeds:
  - `user-inputs.json`
  - `modelling-plan.md`
  - `canonical-modelling-dataset.csv`
  - `summary-metrics.csv`
  - `manifest.json`
- Model-specific artifacts land under `models/{model_id}/`.
- Missing optional artifacts produce manifest entries and placeholder text files.
- Failed model reasons are included when partial success occurs.
- Raw CoinGecko cache paths and AI chat transcripts are excluded from `Download All`.
- `get_review_export_manifest()`, `get_review_download_all()`, and `get_review_artifact_download(...)` return frontend-safe shapes.
- Review readiness is marked only after export preparation finishes.

If this reveals a Modelling descriptor mismatch, do not patch `/app/processing/**`. Return a mini spec for the Modelling Agent with the exact mismatch and expected shape.

If this reveals a Frontend orchestration issue, do not patch `/frontend/**`. Return a mini spec for the Frontend Agent with the exact reproduction path.

## Task 064 Requirements

Review the current 2-day CoinGecko price-cache freshness tolerance.

Current V1 policy:

- Cached price history is usable when it has at least 90 valid daily price rows.
- Latest cached UTC date must be no more than 2 days behind current UTC date.
- If stale or insufficient, Backend/Data may refetch the 365-day market-chart window and merge normalized rows into local cache.
