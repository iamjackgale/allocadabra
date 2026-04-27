| Metadata | Value |
|---|---|
| created | 2026-04-21 07:39:45 BST |
| last_updated | 2026-04-27 BST |

# Allocadabra

Making portfolio allocation magical.

Allocadabra is an AI-assisted crypto treasury modelling application for exploring and comparing strategic asset allocation models comprised of digital assets.

This project has been designed to support the [Crypto Treasury Management Academy](https://www.theaccountantquits.com/crypto-treasury-management-academy) as part of [The Accountant Quits](https://www.theaccountantquits.com/).

The contents of this repo are experimental and in development, and should not be used directly to inform capital allocation decisions. The project is intended for use in an educational setting to learn about strategic asset allocation models; no warranty is given as to the accuracy of information provided by the application.

---

## Getting Started

### Prerequisites

- **Python 3.12** (the project pins `>=3.12,<3.13`)
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — fast Python package and project manager

Install `uv` if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```

### 1. Clone the repo

```bash
git clone https://github.com/iamjackgale/allocadabra.git
cd allocadabra
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv` in the project root and installs all pinned dependencies from `uv.lock`. No separate `pip install` step is needed.

### 3. Configure API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Open `.env` and set the following:

```env
PERPLEXITY_API_KEY=<your Perplexity API key>
COINGECKO_API_KEY=<your CoinGecko Demo API key>
```

| Key | Where to get it | Required? |
|---|---|---|
| `PERPLEXITY_API_KEY` | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) | Yes — AI configuration and review assistant |
| `COINGECKO_API_KEY` | [coingecko.com/en/developers/dashboard](https://www.coingecko.com/en/developers/dashboard) (free Demo plan) | Yes — token list and price history |

### 4. Run the app

```bash
uv run streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Usage

1. **Configure** — Select up to 10 digital assets from the CoinGecko token list and set your treasury objective, risk appetite, constraints, and which models to run (2–3 from Mean Variance, Risk Parity, Hierarchical Risk Parity, and Hierarchical Equal Risk Contribution).
2. **Generate Plan** — The AI assistant reads your configuration and produces a structured modelling plan. Review and confirm it before running.
3. **Run Models** — The app fetches 365 days of daily price data from CoinGecko, builds return series, and runs the selected portfolio optimisation models via riskfolio-lib.
4. **Review** — Compare model outputs across summary metrics, allocation weights, rolling allocation charts, efficient frontier (where available), and drawdown analysis. Use the Review AI assistant to explore results.
5. **Export** — Download individual artifacts or a full ZIP bundle of all outputs.

---

## Tech Stack

| System | Use |
|---|---|
| Python | Primary implementation language. |
| uv | Dependency and virtual environment management. |
| pyproject.toml | Human-edited dependency source. |
| uv.lock | Committed lockfile for reproducible installs. |
| Streamlit | Local web app runtime and frontend. |
| pandas | Dataset construction and transformations. |
| riskfolio-lib | Portfolio modelling and allocation methods. |
| Plotly | Charts and PNG chart export. |
| Perplexity Agent API | AI-assisted configuration and review. |
| perplexity/sonar | Default LLM model for AI assistant. |
| perplexityai | Python SDK for Perplexity integration. |
| CoinGecko Demo API | Token list and daily price history. |
| Local filesystem cache | App state, CoinGecko cache, and generated outputs. |

---

## Supported Models

| Model | ID | Description |
|---|---|---|
| Mean Variance | `mean_variance` | Classic Markowitz optimisation, maximising Sharpe ratio. Includes efficient frontier. |
| Risk Parity | `risk_parity` | Equalises risk contribution across assets using historical covariance. |
| Hierarchical Risk Parity | `hierarchical_risk_parity` | Clusters assets by correlation, then allocates inversely to cluster variance. |
| Hierarchical Equal Risk | `hierarchical_equal_risk` | Extends HRP to equalise risk contributions across hierarchical clusters. |

---

## Repo Layout

```text
app/                  Core app logic: ingestion, storage, processing, AI, and exports.
app/ingestion/        CoinGecko API client and price normalisation.
app/processing/       Dataset building, model execution, and output analysis.
app/storage/          Session state management and local cache.
app/ai/               Perplexity integration and prompt orchestration.
frontend/             Streamlit UI — pages, components, theme, and runtime state.
scripts/              Smoke tests and development entry points.
storage/cache/        Local stored data, split by type (not committed).
storage/cache/coingecko/
storage/cache/user-inputs/
storage/cache/model-outputs/
docs/                 Planning, specs, tasks, agent prompts, validation, and review briefs.
```

---

## Build Philosophy

This repo is being built through detailed planning before implementation. The project starts with high-level planning, scoped specs, agent prompts, and validation criteria in `docs/`.

Codex is used for agent orchestration. The plan is to use a small team of specialized agents, working from shared specs, to build in parallel across backend/data, modelling, AI, frontend, product/UX, and QA while keeping `docs/` as the source of truth.

---

## Hackathon

This project is a solo submission for The Accountant Quits [Vibe Coding Hackathon](https://www.linkedin.com/posts/ocf-institute_perplexity-is-sponsoring-our-vibe-coding-activity-7447664728333500416-74RA/). It was built between 20–27 April 2026.

---

## More Links

To learn more about the model, checkout:
- [Agent Plan](docs/plan.md) - full agentic plan for app build, used to develop specs and prompts for different agents and give all agents context of the big picture idea.
- [Tasks List](docs/tasks.md) - a full summary of all the core agentic tasks that were assigned and completed throughout the initial hackathon build.
- [Hackathon Submission Video](https://www.youtube.com/watch?v=P_582FmJzDY) - comprehensive walkthrough of the project and using the app.
- [Crypto Treasury Management Course](https://www.theaccountantquits.com/crypto-treasury-management-academy) - home page for the course that this project was built to support. Sign up to dive deeper into this and related topics on crypto treasury management.
- [X Page](https://x.com/iamjackgale) - to reach out and give me some public feedback.

---

## Author

jackgale.eth

## License

MIT License. See [LICENSE](LICENSE).
