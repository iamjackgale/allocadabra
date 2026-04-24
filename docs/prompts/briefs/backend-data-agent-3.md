| Metadata | Value |
|---|---|
| created | 2026-04-24 13:10:15 BST |
| last_updated | 2026-04-24 13:10:15 BST |
| prompt_used | |

# Backend/Data Agent Brief 3

You are the Backend/Data Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/data-backend/coingecko-api.md`
   - `/docs/specs/data-backend/data-storage.md`
   - `/docs/specs/data-backend/session-storage.md`
   - `/docs/specs/app/export-bundling.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/backend-validation.md`
   - `/docs/validation/frontend-validation.md`

## Primary Task

- `082`: Add focused backend validation tests or smoke scripts for cache, session lifecycle, and export bundle behavior once the project test pattern is selected.

## Current Direction

Do not introduce a full test framework in this pass unless the repo already has one by the time you start.

Treat `082` as repeatable Backend/Data smoke coverage:

- lightweight scripts, commands, or documented smoke checks are acceptable
- avoid live external API dependency unless explicitly marked optional
- keep checks deterministic and safe for local development

## Required Coverage

Cover at minimum:

- CoinGecko token cache/list read path using local or mocked data where possible.
- Price cache status/fetch path using local or mocked data where possible.
- Active workflow/session lifecycle:
  - default state
  - update inputs
  - confirm/store modelling plan if supported by current callables
  - mark Review ready
  - reset/start new model path
- Deterministic validation issue shape from task `092`.
- Export bundle creation from fixture modelling artifacts:
  - manifest creation
  - unavailable/missing artifact handling
  - `Download All` metadata
  - individual artifact download metadata

## Optional Coverage

Only add these if they are low-effort and do not make smoke checks brittle:

- Missing `COINGECKO_API_KEY` failure path.
- CoinGecko retry/timeout policy shape.
- Export behavior when chart/data files are missing.

## Scope

- Own `/app/storage/**`, `/app/ingestion/**`, and Backend/Data-owned validation docs.
- You may add Backend-owned smoke scripts if you choose an appropriate location.
- Do not edit Frontend UI code, Modelling execution code, AI provider/prompt code, or shared dependencies.

## Implementation Guidance

- Prefer small deterministic fixture data over real network calls.
- Keep generated smoke artifacts under temporary directories or existing ignored cache paths.
- Do not require secrets for the default smoke path.
- If a smoke check reveals a real contract mismatch with Frontend or Modelling, document it and return a mini spec rather than patching their owned folders.

## Validation

- Run `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app/storage app/ingestion`.
- Run `uv lock --check`.
- Run any new smoke scripts or commands you add.
- Run a conflict-marker scan before reporting back.
- Update `/docs/validation/backend-validation.md` with exact commands and expected outputs.

## Reporting Back

When done, report:

- files changed
- smoke scripts or commands added
- coverage achieved
- any checks that remain optional/live-only
- any future QA task recommendations
