| Metadata | Value |
|---|---|
| created | 2026-04-21 07:39:45 BST |
| last_updated | 2026-04-22 23:19:04 BST |

# Allocadabra

Making portfolio allocation magical.

Allocadabra is an AI-assisted crypto treasury modelling application for exploring and comparing strategic asset allocation models comprised of digital assets.

This project has been designed to support the [Crypto Treasury Management Academy](https://www.theaccountantquits.com/crypto-treasury-management-academy) as part of [The Accountant Quits](https://www.theaccountantquits.com/). 

The contents of this repo are experimental and in development, and should not be used directly to inform capital allocation decisions. The project is intended for use in an educational setting to learn about strategic asset allocation models; no warranty is given as to the accuracy of information provided by the application.

## Tech Stack

| System | Use |
|---|---|
| Python | Primary implementation language. |
| Streamlit | Local web app runtime and frontend. |
| pandas | Dataset construction and transformations. |
| riskfolio-lib | Portfolio modelling and allocation methods. |
| Plotly | Charts and PNG chart export where practical. |
| Perplexity Agent API | AI-assisted configuration and review. |
| perplexity/sonar | Default LLM model. |
| perplexityai | Python SDK for Perplexity integration. |
| CoinGecko Demo API | Token list and daily price history. |
| Local filesystem cache | Local app state, CoinGecko cache, and generated outputs. |

## Repo Layout

```text
app/                  Core app logic for ingestion, storage, processing, modelling, AI, and exports.
app/ingestion/        CoinGecko data gathering and normalization.
app/processing/       Dataset building, model preparation, model runs, and output analysis.
app/storage/          Local cache/session state management logic.
app/ai/               Perplexity integration and prompt orchestration.
frontend/             Streamlit UI implementation.
scripts/              Command-style entry points for app actions.
storage/cache/        Local stored data only, split by data type.
storage/cache/coingecko/
storage/cache/user-inputs/
storage/cache/model-outputs/
docs/                 Planning, specs, tasks, prompts, validation, and review briefs.
```

## Build Philosophy

This repo is being built through detailed planning before implementation. The project starts with high-level planning, scoped specs, agent prompts, and validation criteria in `docs/`.

Codex is used for agent orchestration. The plan is to use a small team of specialized agents, working from shared specs, to build in parallel across backend/data, modelling, AI, frontend, product/UX, and QA while keeping `docs/` as the source of truth.

## Hackathon

This project is a solo submission for The Accountant Quits [Vibe Coding Hackathon](https://www.linkedin.com/posts/ocf-institute_perplexity-is-sponsoring-our-vibe-coding-activity-7447664728333500416-74RA/). It was built between 20-27 April 2026.

## Author

jackgale.eth

## License

MIT License. See [LICENSE](LICENSE).
