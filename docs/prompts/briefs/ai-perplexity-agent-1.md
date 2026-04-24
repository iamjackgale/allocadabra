| Metadata | Value |
|---|---|
| created | 2026-04-23 12:29:28 BST |
| last_updated | 2026-04-23 12:29:28 BST |
| prompt_used | 2026-04-23 19:27:08 BST |

# AI/Perplexity Agent Brief 1

You are the AI/Perplexity Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review all specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/ai/ai-model-integration.md`
   - `/docs/specs/ai/parameters-agent.md`
   - `/docs/specs/ai/review-agent.md`
   - `/docs/specs/app/ai-runtime-dependency-mini-spec.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/ai-validation.md`

## Primary Tasks

- `071`: Strengthen modelling-plan import parsing and validation.
- `072`: Add typed structured metadata helpers/schemas for app-actable AI outputs.
- `080`: Strengthen Configuration Mode prompts around unsupported constraints, missing required fields, and asset-guidance boundaries.
- `075`: Extend AI validation coverage for invalid metadata, unsupported models, future-only models, text/metadata conflicts, financial-advice replacement, and Review context-selection edge cases.

## Secondary Tasks

If primary work is complete:

- `073`: Improve Review Mode detailed-context selection.
- `074`: Extract and validate optional Review response metadata.
- `077`: Update AI prompt/spec docs if prompt behavior changes.

## Blocked

- `076`: Live Perplexity provider verification is blocked until `PERPLEXITY_API_KEY` is configured.
- `081`: Supported-model registry alignment waits until Modelling exposes a stable registry/export.

## Scope

- Own `/app/ai/**`.
- You may update AI validation docs.
- Do not edit frontend rendering, modelling execution, storage/export packaging, or root dependency files.
- `perplexityai` is already present in `pyproject.toml` and `uv.lock`.

## Expected Direction

- Replace loose dict handling with typed helpers, dataclasses, or equivalent structured validation helpers.
- Strengthen pasted modelling-plan parsing for:
  - objective
  - risk appetite
  - selected assets
  - constraints
  - selected models
  - data window
- Reject unsupported or future-only models in app-actable metadata.
- Detect and reject conflicts between user-facing text and structured metadata.
- Keep user-facing Markdown readable and avoid exposing raw metadata.
- Improve Configuration Mode prompts so the agent:
  - asks only for required missing fields,
  - handles unsupported constraints clearly,
  - gives asset guidance without making financial recommendations.

## Guardrails

- No financial advice.
- No live web search in V1.
- No unsupported model names in app-actable metadata.
- Fixed V1 supported models remain:
  - Mean Variance
  - Risk Parity
  - Hierarchical Risk Parity

## Validation

- Run relevant commands from `/docs/validation/general-validation.md`.
- Add or update `/docs/validation/ai-validation.md` with new smoke checks.
- Do not run live Perplexity calls unless `PERPLEXITY_API_KEY` is available.
- Update `/docs/tasks.md` only if instructed by Orchestrator; otherwise report task completion/status back.
