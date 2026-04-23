| Metadata | Value |
|---|---|
| created | 2026-04-23 12:30:52 BST |
| last_updated | 2026-04-23 12:30:52 BST |
| prompt_used | |

# Backend/Data Agent Brief 1

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
   - `/docs/validation/general-validation.md`
   - `/docs/validation/backend-validation.md`

## Primary Task

- `063`: Document the V1 CoinGecko retry, timeout, and rate-limit policy in `/docs/specs/data-backend/coingecko-api.md` to match implemented client behaviour.

## Scope

- Own `/app/ingestion/**`, `/app/storage/**`, and Backend/Data-owned docs.
- This brief is documentation-first. Only change production code if the spec review reveals a clear mismatch between implementation and intended V1 policy.
- Do not edit Modelling, AI, Frontend, or root dependency files.

## Current Implementation To Document

Document the current V1 policy unless code inspection proves it has changed:

- `timeout_seconds=20`
- `max_retries=2`
- `retry_delay_seconds=1`

Clarify:

- Which CoinGecko calls use the policy.
- How recoverable failures should be surfaced to callers.
- That live API validation requires `COINGECKO_API_KEY`.
- That task `064` separately tracks whether the 2-day price-cache freshness tolerance should change after Streamlit/runtime validation.

## Boundaries

- Do not alter cache freshness policy for task `063`.
- Do not take over Modelling dataset construction.
- Do not add a new test framework.

## Validation

- Run relevant doc checks from `/docs/validation/general-validation.md`.
- If you change code, run `PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app`.
- Update `/docs/tasks.md` only if instructed by Orchestrator; otherwise report task completion/status back.
