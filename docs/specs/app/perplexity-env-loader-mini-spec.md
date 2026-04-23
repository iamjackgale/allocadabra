| Metadata | Value |
|---|---|
| created | 2026-04-23 19:17:24 BST |
| last_updated | 2026-04-23 19:17:24 BST |

# Perplexity Env Loader Mini Spec

## Target Files

- `app/ai/provider.py`
- `docs/validation/ai-validation.md`
- Optional: `docs/specs/ai/ai-model-integration.md`

## Requested Owner

- AI/Perplexity Agent implements the loader in AI-owned code (`app/ai/**`) and updates AI validation docs.
- Orchestrator reviews any changes outside `app/ai/**` if needed.

## Proposed Change

Implement a lightweight `.env` loader used by the Perplexity provider so local runs do not require manually exporting `PERPLEXITY_API_KEY` each time.

Requirements:

- Load `.env` from:
  - `Path.cwd() / ".env"`
  - repo root `.env` (same pattern as `app/ingestion/coingecko.py`)
- Parse `KEY=VALUE` pairs:
  - ignore blank lines and `#` comments
  - strip surrounding quotes on values
  - do not overwrite environment variables that are already set
- Load before reading `PERPLEXITY_API_KEY` in `PerplexityProvider.__init__`.
- Never log the key or the raw `.env` contents.
- Do not add new dependencies (no `python-dotenv`).

Non-goals:

- Do not commit `.env`.
- Do not change Perplexity request behaviour, prompts, or metadata schemas beyond what is required to support task `076`.

## Reason

V1 runs locally with Streamlit + `uv`. Manually exporting `PERPLEXITY_API_KEY` for each terminal/session is error-prone and slows iteration. A small loader aligns Perplexity behaviour with the existing CoinGecko `.env` loading pattern.

## Interface / Contract Impact

- Allows `app.ai.provider.PerplexityProvider` to succeed when `PERPLEXITY_API_KEY` exists only in `.env`.
- Environment variables continue to take precedence over `.env`.
- No changes to frontend-callable AI interfaces.

## Validation

Update `docs/validation/ai-validation.md` with a new smoke check:

- With `PERPLEXITY_API_KEY` unset in the shell and present in `.env`, `uv run python -c "from app.ai.provider import PerplexityProvider; PerplexityProvider(); print('env load ok')"` prints `env load ok`.

Then complete live provider verification (task `076`) using a real API call, without printing secrets.

