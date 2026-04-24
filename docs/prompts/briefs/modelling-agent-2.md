| Metadata | Value |
|---|---|
| created | 2026-04-24 08:04:58 BST |
| last_updated | 2026-04-24 08:04:58 BST |
| prompt_used | 2026-04-24 08:06:44 BST |

# Modelling Agent Brief 2

You are the Modelling Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/data-backend/dataset-building.md`
   - `/docs/specs/data-backend/riskfolio-lib.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md`
   - `/docs/prompts/briefs/frontend-agent-progress-report-1.md`
   - `/docs/validation/general-validation.md`
   - `/docs/validation/modelling-validation.md`
   - `/docs/validation/frontend-validation.md`

## Primary Tasks

- `069`: Harden summary metric unavailable states so non-computable metrics return explicit user-facing unavailable reasons rather than only `NaN` values.
- `070`: Add repeatable modelling validation tests or smoke scripts for dataset failures, model failures, optional missing artifacts, and metric consistency once the project test pattern is selected.

## Why This Matters

The first Frontend pass can render Review outputs, but `NaN` summary metrics are poor user-facing states. The Review table and AI Review context need clear unavailable reasons when a metric cannot be computed.

Repeatable modelling smoke checks are also needed before QA formalizes the test suite.

## Scope

- Own `/app/processing/**` and Modelling-owned validation docs.
- You may update `/docs/specs/data-backend/riskfolio-lib.md` and `/docs/validation/modelling-validation.md`.
- Do not edit Frontend UI code, Backend/Data storage/export code, AI prompt/provider code, or shared dependencies.

## Task 069 Requirements

Harden metric outputs so non-computable metrics are explicit.

Expected behavior:

- Avoid bare `NaN` values in user-facing summary metric artifacts where possible.
- Include stable unavailable metadata for non-computable metrics.
- Preserve numeric values for computable metrics.
- Keep output friendly to both:
  - Frontend Review rendering
  - Review Mode AI context injection

Recommended shape:

- Keep `summary-metrics.csv` numeric-friendly where practical.
- Add a companion artifact or metadata field for unavailable metric reasons if that is cleaner than mixing strings into numeric CSV cells.
- Use stable reason codes and short user-facing messages.

Suggested unavailable reason codes:

- `insufficient_returns`
- `zero_volatility`
- `zero_drawdown`
- `no_negative_returns`
- `tail_sample_unavailable`
- `calculation_failed`

If you choose a different shape, document it clearly in the Riskfolio spec and modelling validation handoff.

## Task 070 Requirements

Add repeatable modelling validation smoke coverage without introducing a heavy test framework unless already present.

Cover at minimum:

- dataset failure for too few assets
- dataset failure for insufficient price history
- unsupported model selection
- partial model failure shape
- optional missing artifact descriptor shape
- metric consistency for a deterministic small synthetic dataset
- unavailable metric reason output for at least one synthetic edge case
- cooperative cancellation smoke check remains valid after task `069`

Preferred implementation:

- Add lightweight smoke commands/scripts if no test framework exists.
- Keep synthetic data small and deterministic.
- Document exact commands and expected output in `/docs/validation/modelling-validation.md`.

## Boundaries

- Do not change the V1 supported model set.
- Do not change Frontend table rendering directly.
- Do not move export bundling into Modelling.
- Do not change Backend/Data manifest packaging unless you return a mini spec first.
