created: 2026-04-20 20:06:11 BST
last_updated: 2026-04-21 10:53:18 BST

# Allocadabra Project Plan

## Project Goal

Allocadabra is a web application for students on an intro crypto treasury management course. It helps users explore strategic crypto treasury allocation by selecting assets, describing preferences, confirming an AI-generated modelling plan, comparing model outputs, and reflecting on trade-offs.

Allocadabra wraps `riskfolio-lib`; it does not modify or fork the library. The product is educational and should not present outputs as financial advice, trading instructions, or guaranteed outcomes.

## Workflow

1. User starts a new modelling workflow.
2. System fetches a selection of crypto asset options from the CoinGecko API.
3. User selects assets from a searchable dropdown.
4. User provides modelling preferences rather than full manual assumptions.
5. System sends the user's selected assets and preferences to Perplexity.
6. Perplexity generates a natural-language modelling plan for user confirmation.
7. Perplexity may suggest a subset from a fixed set of supported models.
8. User confirms the modelling plan before any model execution.
9. System runs the confirmed model subset through `riskfolio-lib`.
10. System presents comparable result summaries for the different models.
11. User can explore model results in more detail.
12. User can ask Perplexity follow-up questions about the results and model trade-offs.
13. System offers exports of generated outputs.
14. User can reset or refresh the workflow when they choose.

Progress should be cached locally so a user can leave the page and resume mid-query.

## Architecture Components

- Frontend: browser-based workflow for asset search, preference capture, plan confirmation, result comparison, deeper exploration, AI reflection, export, resume, and reset.
- App/Data Layer: coordinates CoinGecko data access, Perplexity calls, modelling execution, browser-local storage, and exports within a single holistic app.
- Asset Data Layer: fetches and normalizes crypto asset options from CoinGecko for searchable selection.
- LLM Layer: uses Perplexity to generate the natural-language modelling plan, suggest supported model subsets, and support post-result reflection.
- Modelling Layer: wraps `riskfolio-lib` and runs only confirmed models from the supported model set.
- Browser-Local Storage: stores cached CoinGecko data, the single active input state, and current model outputs so users can leave and resume.
- Export Layer: packages generated outputs for download after modelling and reflection.

## Tech Stack

Confirmed:

| System | Type | Use |
|---|---|---|
| Python | Language | Primary implementation language for the app and modelling workflow. |
| pandas | Python data library | Build canonical price dataframes and model-specific transformed datasets. |
| `riskfolio-lib` | Python modelling library | Portfolio modelling and strategic asset allocation calculations. |
| Perplexity | External LLM provider | AI model-plan generation, model subset suggestion, and result reflection. |
| CoinGecko Demo API | Market data API | Token list and token price history source. |
| Browser-local storage/cache | Local persistence model | Stores CoinGecko cache, active user inputs, and current model outputs on the user's machine. |

To decide:

- Python frontend/web app framework.
- Browser-local storage implementation.
- Charting/visualisation dependencies.
- Export packaging dependencies.
- Pyodide feasibility for browser-local Python execution with `riskfolio-lib`.

## Repository Layout

- `/app`: core processing functionality for ingestion, storage management, dataset building, modelling, AI/LLM calls, analysis, and export preparation.
- `/app/ingestion`: CoinGecko data gathering and normalization logic.
- `/app/processing`: dataset building, model preparation, modelling workflows, and output analysis logic.
- `/app/storage`: storage management logic for reading and writing browser-local/cache-backed data.
- `/app/ai`: Perplexity/LLM integration logic and prompt orchestration.
- `/frontend`: UI/frontend implementation.
- `/scripts`: command-style entry points that trigger app actions and can later be wired to UI buttons.
- `/storage/cache`: stored data only, not application logic.
- `/storage/cache/coingecko`: cached CoinGecko token and price data.
- `/storage/cache/user-inputs`: the single active user input state.
- `/storage/cache/model-outputs`: the current model output set.

## Cross-Cutting App Standards

- Logging must follow `/docs/specs/app/logging.md`.
- Production paths should use the shared logging utility and named module loggers.
- Production paths should not use `print()` for progress reporting.

## Agent Responsibilities

- Orchestrator Agent: owns `/docs`, records project decisions, maintains plan/task/spec consistency, and does not write production code.
- Frontend Agent: owns the student-facing web workflow and result exploration experience.
- Backend/Data Agent: owns app data boundaries, CoinGecko integration, browser-local storage, session state, and export support.
- LLM Agent: owns Perplexity prompts, modelling-plan generation, model-subset suggestion, and reflection flow.
- Modelling Agent: owns `riskfolio-lib` integration and the fixed supported model registry.
- QA Agent: owns validation strategy, workflow testing, and regression checks.

## Known Constraints

- `riskfolio-lib` model details remain intentionally light until the Modelling Agent defines the fixed supported model set.
- Perplexity output remains iterative, but it must be constrained to supported model names.
- The user must confirm the natural-language modelling plan before models run.
- Model results should be presented as summaries first, with deeper exploration available.
- The system should support follow-up questions about results and trade-offs.
- The system should preserve local in-progress state across page exits and reloads.
- The system should offer exports of generated files/results.

## Browser-Local Runtime Constraints

- Limit each modelling run to no more than 10 selected assets.
- Limit each comparison run to no more than 3 models.
- Limit the initial modelling window to a maximum of 365 daily observations.
- Avoid continuous background fetching; CoinGecko calls should be page-load, dropdown/search, or model-generation triggered.
- Reuse browser-cached CoinGecko data wherever possible before making new API calls.
- Run expensive modelling work asynchronously from the UI thread where practical, so the interface remains responsive.
- Present result summaries first and load deeper model exploration views only when the user requests them.
- Keep one active workflow state and one active model-output set; do not maintain a full in-browser history of prior runs.

## External Service Decisions

- CoinGecko access uses Demo API authentication against `https://api.coingecko.com/api/v3` with the `x-cg-demo-api-key` header.
- CoinGecko API keys are loaded from `.env` and must not be committed.
- CoinGecko usage is limited to free public endpoints available with the demo API key.
- Token-list retrieval supports the asset selection UI and may be triggered on page load, dropdown open, or user-prompted search confirmation.
- Token-price retrieval is handled entirely by the app data layer and only triggered after the user confirms modelling scope and chooses to generate models.
- CoinGecko market data, active user inputs, and current model outputs are stored locally in the user's browser.
- The app supports one active set of user inputs and one active set of model outputs; previous inputs/outputs are recoverable only if the user downloaded them.
- The app should not include an in-app cache-clearing control; browser storage is cleared only through the user's browser.

## Initial Spec Areas

Initial spec stubs have been created under `/docs/specs`. These files capture the current areas of concern without yet defining detailed schemas, API contracts, prompts, or implementation rules.

Current spec areas include:

- CoinGecko asset option contract.
- CoinGecko price data ingestion.
- Cached market data storage.
- User preference capture contract.
- Perplexity modelling-plan contract.
- Supported model registry contract.
- Riskfolio-Lib execution contract.
- Result summary and exploration contract.
- Reflection conversation contract.
- Local cache/session state contract.
- Export contract.
- Shared logging contract.

Detailed specs and contracts are the next planning action.
