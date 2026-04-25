| Metadata | Value |
|---|---|
| created | 2026-04-24 13:46:50 BST |
| last_updated | 2026-04-24 13:46:50 BST |
| prompt_used | 2026-04-24 13:48:32 BST |

# AI/Perplexity Agent Brief 3

You are the AI/Perplexity Agent for Allocadabra.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Confirm `PERPLEXITY_API_KEY` is available through the repo-root `.env` or shell environment for live tests, except when running the explicit missing-key test path.
5. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/ai-live-integration.md`
   - `/docs/specs/ai/ai-model-integration.md`
   - `/docs/specs/ai/parameters-agent.md`
   - `/docs/specs/ai/review-agent.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/validation/ai-validation.md`
   - `/docs/validation/frontend-validation.md`

## Primary Tasks

- `107`: Run live Configuration Mode verification tests `CM-1` through `CM-4`.
- `108`: Run live Review Mode verification tests `RM-1` through `RM-3` using the synthetic Review fixture.
- `109`: Validate live guardrails `GR-1` through `GR-4`.
- `110`: Refine Configuration Mode prompt behaviour based on live UI usage.
- `111`: Refine Review Mode prompt behaviour based on live UI usage.
- `114`: Run a live transcript-quality review for Configuration and Review modes and prepare the gap list for Orchestrator review.

## Current Runtime Paths

Start the app:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Configuration Mode starts at:

```text
http://localhost:8501
```

Synthetic Review fixture:

```text
http://localhost:8501/?alloca_dev_review_fixture=1
```

Frontend-only Review fixture without live Perplexity:

```text
http://localhost:8501/?alloca_dev_review_fixture=frontend-check&alloca_dev_no_ai_env=1
```

Missing-key Configuration Mode path:

```text
http://localhost:8501/?alloca_dev_no_ai_env=1
```

The synthetic Review fixture intentionally writes synthetic outputs through the existing local workflow/export path. It avoids CoinGecko and modelling, but it replaces the active local workflow for that app session. Treat it as a local validation mode, not a read-only overlay.

## Required Live Test Coverage

Use `/docs/specs/app/ai-live-integration.md` as the source of truth.

Configuration Mode:

- `CM-1`: minimal complete configuration.
- `CM-2`: incomplete configuration.
- `CM-3`: invalid or unsupported constraints.
- `CM-4`: missing `PERPLEXITY_API_KEY` path using `?alloca_dev_no_ai_env=1`.

Review Mode:

- `RM-1`: Review opening from the synthetic Review fixture.
- `RM-2`: visible context injection for Risk Parity allocation weights.
- `RM-3`: follow-up chat grounded in the synthetic manifest.

Guardrails:

- `GR-1`: buy/sell financial advice request.
- `GR-2`: direct model-choice request.
- `GR-3`: unsupported live-data/source request.
- `GR-4`: unsupported model request.

Transcript-quality review:

- Run a short representative Configuration transcript.
- Run a short representative Review transcript using the synthetic fixture.
- Assess default response length, educational/neutral tone, recommendation strength, unsupported request handling, metadata quality, and whether the answers stay grounded in app state or synthetic outputs.
- Prepare a concise gap list for Orchestrator review under task `115`.
