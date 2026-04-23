| Metadata | Value |
|---|---|
| created | 2026-04-23 07:18:04 BST |
| last_updated | 2026-04-23 07:18:04 BST |

# Export Bundling Spec

## Purpose

Define the V1 download/export layer for Allocadabra.

This spec should give Backend/Data, Modelling, Frontend, AI/Perplexity, and QA one shared contract for:

- which generated artifacts exist.
- which artifacts are downloadable individually.
- which artifacts are included in `Download All`.
- which file formats are used.
- which agent owns producing each artifact.
- which agent owns packaging, displaying, and validating each artifact.
- how missing or unavailable artifacts are represented.

## Current Decisions

- Exports are available at the end of the workflow, primarily in Review Phase.
- User inputs export as `.json`.
- Accepted AI modelling plan exports as `.md`.
- Model output tables export as `.csv`.
- Chart images export as `.png`.
- `Download All` should return one bundle containing all available generated artifacts.
- AI chat transcripts are not exportable in V1.
- No `.pdf` export is required in V1.
- Exports should not clear CoinGecko cache, active session state, or model outputs.

## Preliminary Ownership

| Area | Likely Owner | Notes |
|---|---|---|
| Artifact manifest shape | Backend/Data Agent with Modelling Agent input | Must tell Frontend which artifacts exist, are missing, or are disabled. |
| User input JSON | Backend/Data Agent | Source is active session state. |
| Modelling plan Markdown | AI/Perplexity Agent produces content; Backend/Data stores/exports | Must export exactly as displayed. |
| Model output CSVs | Modelling Agent produces; Backend/Data stores/exports | Includes tables and chart data where exposed for download. |
| Chart PNGs | Modelling Agent or Frontend Agent, to be decided | Depends whether charts are generated server-side during modelling or rendered/exported from Review UI. |
| Bundle creation | Backend/Data Agent | Likely creates zip package from manifest and available files. |
| Download controls | Frontend Agent | Per-section downloads and `Download All`. |
| Validation | QA/Validation Agent | Missing artifact states, bundle contents, file types, and no chat export. |

## Expected Artifact Categories

| Category | Format | V1 Status | Notes |
|---|---|---|---|
| User inputs | `.json` | Required | Captures the final confirmed configuration inputs. |
| Accepted modelling plan | `.md` | Required | Human-readable AI-generated plan accepted by the user. |
| Summary metrics table | `.csv` | Required if Review succeeds | Side-by-side model comparison metrics. |
| Allocation weights | `.csv` | Required per successful model | Final optimized weights by asset. |
| Allocation over time | `.csv`, `.png` | Required where chart renders | V1 may repeat static weights across 365-day window. |
| Cumulative performance | `.csv`, `.png` | Required where chart renders | Based on successful model outputs. |
| Drawdown | `.csv`, `.png` | Required where chart renders | Based on successful model outputs. |
| Rolling volatility | `.csv`, `.png` | Required where chart renders | Window definition to be confirmed in modelling spec if not already fixed. |
| Risk contribution | `.csv`, `.png` | Required where computable | May not exist for every model. |
| Efficient frontier | `.csv`, `.png` | Optional | Likely Mean Variance only. |
| Dendrogram | `.png` | Optional | Likely HRP only; underlying cluster data format to be decided. |
| Failed model reasons | `.json` or included manifest | Required if partial success enters Review | Must not block exports for successful models. |

## Bundle Rules To Define

- Bundle file name.
- Internal folder structure.
- Manifest file name and schema.
- Whether per-model outputs are grouped by model or by output type.
- Whether optional/missing artifacts appear in the manifest only or as placeholder files.
- Whether disabled UI download buttons are driven directly by the manifest.
- Whether `Download All` includes failed model reasons.
- Whether `Download All` includes raw cached CoinGecko price data or only generated modelling outputs.

## Open Questions

To be answered with the Orchestrator/user before implementation ownership is finalized.
