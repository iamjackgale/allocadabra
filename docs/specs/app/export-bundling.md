| Metadata | Value |
|---|---|
| created | 2026-04-23 07:18:04 BST |
| last_updated | 2026-04-23 09:22:30 BST |

# Export Bundling Spec

## Purpose

Define the V1 download/export layer for Allocadabra.

This spec gives Backend/Data, Modelling, Frontend, AI/Perplexity, and QA one shared contract for:

- which generated artifacts exist.
- which artifacts are downloadable individually.
- which artifacts are included in `Download All`.
- which file formats are used.
- which agent owns producing each artifact.
- which agent owns packaging, displaying, and validating each artifact.
- how missing or unavailable artifacts are represented.

## Current Decisions

- Exports are available at the end of the workflow, primarily in Review Phase.
- `Download All` returns one `.zip` bundle.
- Bundle filename: `allocadabra-results-YYYYMMDD-HHMM.zip`.
- General/comparative outputs live at the bundle root.
- Model-specific outputs live in `models/{model_id}/`.
- Raw CoinGecko price cache data is not included.
- Only user-facing outputs are included.
- AI chat transcripts are not exportable in V1.
- No `.pdf` export is required in V1.
- Exports should not clear CoinGecko cache, active session state, or model outputs.
- Exports are written once after modelling completes; after that they are displayed and downloaded from storage, not regenerated on demand.
- Export failure must not block entry into Review; failed individual downloads should be disabled with explanations.

## Ownership

| Area | Owner | Notes |
|---|---|---|
| Artifact manifest shape | Backend/Data Agent with Modelling Agent input | Must tell Frontend which artifacts exist, are missing, or are disabled. |
| User input JSON | Backend/Data Agent | Source is final confirmed user inputs only; no app-derived metadata. |
| Modelling plan Markdown | AI/Perplexity Agent produces content; Backend/Data stores/exports | Markdown only; no structured metadata in the exported file. |
| Canonical modelling dataset CSV | Modelling Agent produces; Backend/Data stores/exports | User-facing modelling dataset, not raw CoinGecko cache data. |
| Model output CSVs | Modelling Agent produces; Backend/Data stores/exports | Includes tables and chart data for generated outputs. |
| Chart PNGs | Modelling Agent | Generate during output generation where practical for efficient storage/download. |
| Bundle creation | Backend/Data Agent | Creates zip package from manifest and available files. |
| Download controls | Frontend Agent | Per-section downloads and `Download All`. |
| Validation | QA/Validation Agent | Missing artifact states, bundle contents, file types, and no chat export. |

## Expected Artifact Categories

| Category | Format | V1 Status | Notes |
|---|---|---|---|
| User inputs | `.json` | Required | Captures final confirmed user inputs only. |
| Accepted modelling plan | `.md` | Required | Human-readable AI-generated plan accepted by the user; Markdown only. |
| Canonical modelling dataset | `.csv` | Required if modelling succeeds | User-facing aligned modelling dataset. |
| Summary metrics table | `.csv` | Required if Review succeeds | Side-by-side model comparison metrics. |
| Allocation weights | `.csv` | Required per successful model | Final optimized weights by asset. |
| Allocation over time | `.csv`, `.png` | Required where chart renders | V1 may repeat static weights across 365-day window. |
| Cumulative performance | `.csv`, `.png` | Required where chart renders | Based on successful model outputs. |
| Drawdown | `.csv`, `.png` | Required where chart renders | Based on successful model outputs. |
| Rolling volatility | `.csv`, `.png` | Required where chart renders | Window definition to be confirmed in modelling spec if not already fixed. |
| Risk contribution | `.csv`, `.png` | Required where computable | May not exist for every model. |
| Efficient frontier | `.csv`, `.png` | Optional | Likely Mean Variance only. |
| Dendrogram | `.csv`, `.png` | Optional | Likely HRP only; chart PNG plus underlying cluster/tree data where practical. |
| Failed model reasons | `.json` | Required if partial success enters Review | Must not block exports for successful models. |
| Artifact manifest | `.json` | Required | Included in `Download All`. |
| Missing optional artifact explanation | `.txt` | Required where optional artifact is unavailable | Human-readable placeholder explanation for missing optional artifacts. |

Every chart output must have an underlying `.csv` data artifact even if the Review UI only displays the chart.

## Bundle Structure

`Download All` creates:

```text
allocadabra-results-YYYYMMDD-HHMM.zip
```

Internal structure:

```text
manifest.json
user-inputs.json
modelling-plan.md
canonical-modelling-dataset.csv
summary-metrics.csv
failed-models.json
missing/
  <artifact-id>.txt
models/
  mean_variance/
    allocation-weights.csv
    allocation-over-time.csv
    allocation-over-time.png
    cumulative-performance.csv
    cumulative-performance.png
    drawdown.csv
    drawdown.png
    rolling-volatility.csv
    rolling-volatility.png
    efficient-frontier.csv
    efficient-frontier.png
  risk_parity/
    allocation-weights.csv
    allocation-over-time.csv
    allocation-over-time.png
    cumulative-performance.csv
    cumulative-performance.png
    drawdown.csv
    drawdown.png
    rolling-volatility.csv
    rolling-volatility.png
    risk-contribution.csv
    risk-contribution.png
  hierarchical_risk_parity/
    allocation-weights.csv
    allocation-over-time.csv
    allocation-over-time.png
    cumulative-performance.csv
    cumulative-performance.png
    drawdown.csv
    drawdown.png
    rolling-volatility.csv
    rolling-volatility.png
    risk-contribution.csv
    risk-contribution.png
    dendrogram.csv
    dendrogram.png
```

Rules:

- General/comparative outputs live at the bundle root.
- Model-specific outputs live in `models/{model_id}/`.
- Optional artifacts that are unavailable should be represented by `manifest.json` plus a placeholder explanation under `missing/`.
- Raw CoinGecko cache files are excluded.
- AI chat transcripts are excluded.

## Artifact Manifest

The manifest should be generated once after modelling completes and stored with the model outputs.

Required top-level fields:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | integer | Start at `1`. |
| `created_at` | string | ISO timestamp when outputs were finalized. |
| `bundle_filename` | string | Example: `allocadabra-results-20260423-0922.zip`. |
| `artifacts` | array | One entry per available, failed, or missing artifact. |

Artifact entry fields:

| Field | Type | Notes |
|---|---|---|
| `artifact_id` | string | Stable unique ID used by UI/download logic. |
| `label` | string | User-facing name. |
| `category` | string | `general`, `model`, `manifest`, `missing`, or `failure`. |
| `model_id` | string/null | Required for model-specific artifacts. |
| `output_type` | string | Example: `summary_metrics`, `allocation_weights`, `drawdown`. |
| `format` | string | `json`, `md`, `csv`, `png`, or `txt`. |
| `path` | string/null | Path relative to model-output storage or bundle root. |
| `status` | string | `available`, `missing`, `failed`, or `disabled`. |
| `reason` | string/null | Required unless `status` is `available`. |
| `included_in_download_all` | boolean | Usually `true` for all user-facing artifacts. |
| `individual_download_enabled` | boolean | Drives per-section download buttons. |

## Individual Downloads

- Individual section downloads return one visible artifact only.
- Do not create nested or per-section zip files in V1.
- For chart sections, the default visible artifact is the `.png`.
- The underlying chart `.csv` must still exist as an artifact and be included in `Download All`.
- Missing artifacts should show disabled download controls with an explanation from the manifest.

## Review Entry And Failure Handling

- Export creation happens after modelling outputs are finalized and before Review is fully ready.
- Export failure does not block Review entry.
- Failed individual artifacts appear in the manifest with `status="failed"` or `status="disabled"` and a user-facing reason.
- `Download All` should include all available artifacts, failed model reasons, placeholder `.txt` files for missing optional artifacts, and the manifest.
- If the zip bundle itself cannot be created, the `Download All` control should be disabled with a user-facing explanation while individual available artifacts may remain downloadable.

## Implementation Handoff

- Backend/Data Agent can now implement export bundle creation, manifest writing, unavailable-artifact handling, and download bundle manifests.
- Modelling Agent should produce model output files and chart PNG/CSV artifacts matching this spec.
- Frontend Agent should drive download controls from the manifest.
- QA/Validation Agent should validate bundle contents, individual disabled states, manifest schema, and no raw CoinGecko/chat transcript leakage.
