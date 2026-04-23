| Metadata | Value |
|---|---|
| created | 2026-04-20 20:06:11 BST |
| last_updated | 2026-04-23 09:40:39 BST |

# Allocadabra Project Plan

## Project Goal

Allocadabra is a local Streamlit web application for students on an intro crypto treasury management course. It helps users explore strategic crypto treasury allocation by selecting crypto assets, describing treasury preferences, confirming an AI-generated modelling plan, running supported portfolio models, comparing outputs, and reflecting on trade-offs.

Allocadabra wraps `riskfolio-lib`; it does not modify or fork the library. The product is educational and must not present outputs as financial advice, trading instructions, or guaranteed outcomes.

## Product Principles

- Build a focused hackathon V1 that can run as one local app from the repo.
- Keep the user journey clear: Configuration, Modelling, Review.
- Let users specify preferences rather than requiring full manual assumptions.
- Use AI for guided configuration and result interpretation, not autonomous investment advice.
- Present comparable model summaries first, then allow deeper exploration.
- Keep implementation practical: no separate backend service, no accounts, no cloud persistence, no mobile optimization beyond a holding screen.
- Preserve clear ownership boundaries between frontend, backend/data, modelling, AI, product/UX, QA, and orchestration.

## Workflow

Allocadabra has three workflow phases:

1. Configuration Phase.
2. Modelling Phase.
3. Review Phase.

### Configuration Phase

User-facing purpose:

- Select assets.
- Set treasury objective and risk appetite.
- Optionally set supported constraints.
- Choose supported models.
- Use Configuration Mode chat for help.
- Generate, review, and accept a modelling plan.

Core rules:

- Asset selection uses a searchable CoinGecko-backed dropdown.
- Search uses token `symbol` and `name`, not `id`.
- Users select at least 2 assets and no more than 10.
- Treasury objective is one of:
  - `Maximize return`
  - `Stable performance`
  - `Best risk-adjusted returns`
  - `Reduce drawdowns`
  - `Diversify exposure`
- Risk appetite is one of:
  - `Very low`
  - `Low`
  - `Medium`
  - `High`
  - `Very high`
- Risk appetite informs AI wording and Review ranking, but does not change how models are run in V1.
- Initial supported models are pre-selected by default, but users may deselect down to one.
- Optional constraints are limited to supported allocation and asset-count constraints.
- `Generate Plan` runs deterministic validation before AI.
- Generated modelling plan temporarily replaces the form and offers exactly three actions:
  - `Run`: begin validation and modelling to move past Configuration Phase.
  - `Regenerate`: generate another plan while staying in the same core workflow.
  - `Reconfigure`: abandon the current plan and return to the configuration screen with previous items still selected.
- `Reconfigure` requires confirmation copy: `This abandons the current plan and returns to Configuration with your previous selections still filled in.`
- Users cannot directly edit generated modelling plans in V1.

### Modelling Phase

User-facing purpose:

- Show that the app is working while data is fetched, datasets are built, models run, metrics/charts are prepared, and downloads are packaged.

Core rules:

- Use a full Modelling screen, not the Configuration/Review two-panel layout.
- Use red accent/backlighting while Modelling is active.
- Show a restrained phase header that reads `MODELLING` in the centre of the full Modelling screen.
- Show a progress bar with major checkpoints:
  - Validation.
  - Ingestion.
  - Datasets.
  - Modelling.
  - Analysis.
  - Outputs.
- Show one smooth transient micro-log line at a time, not a CLI-style log.
- Show approximate elapsed time, but avoid percentage progress unless accurate.
- Users may `Cancel` while modelling is active.
- `Cancel` requires confirmation copy: `This abandons the current modelling run, deletes partial outputs, and returns to Configuration with your previous options selected.`
- `Cancel` abandons the active run and generated plan, deletes partial model outputs, keeps cached market data unchanged, and returns to the Configuration screen with the previous configuration options still selected.
- After `Cancel`, the right-hand Configuration pane shows the editable configuration component, not the abandoned modelling plan.
- Warn users not to close or refresh while modelling is active.
- If refresh interrupts a run, show interrupted state with copy: `The previous modelling run was interrupted. You can return to Configuration with your previous options selected, or restart the run.`
- Interrupted-run resume is V2.
- When outputs and review artifacts are ready, Modelling is complete, the accent changes to green, and the UI shows `Review Results`.
- If the app reloads after review artifacts are ready, reopen in Review.
- Configuration chat is wiped when Modelling succeeds and review artifacts are ready.
- If at least one selected model succeeds, proceed to Review with failed models marked; do not pause for failed-model retries in V1.
- If no selected models succeed, stay in Modelling and require retry or `Cancel` back to Configuration.
- If no selected models succeed, show copy: `No models completed successfully. You can retry the run or cancel back to Configuration.`

### Review Phase

User-facing purpose:

- Compare model outputs.
- Explore charts and artifacts.
- Ask Review Mode AI questions about visible outputs and trade-offs.
- Download generated artifacts.
- Return to Configuration or start a new model.

Core rules:

- Desktop layout uses Review Mode chat on the left and Model Review on the right.
- Summary metrics comparison is open by default.
- Review pane should include non-chat comparison cues above the default summary metrics:
  - `Compare model outputs against your selected objective and risk appetite. Green/yellow/red rankings compare these models within this run only.`
  - `Ranked for: [Treasury objective] · [Risk appetite]`
- Review Mode AI gives the opening comparison in chat only.
- Review ranking is prepared before Review starts and does not update based on Review chat in V1.
- Review chat receives visible output context automatically, but the user does not see context-injection details.
- Review chat cannot control UI navigation in V1.
- One Review output section is open at a time.
- Failed models may appear in red with failure reasons.
- `Return To Configure` requires confirmation copy: `This returns to Configuration and clears the current outputs and Review chat. Download results first if you want to keep them.`
- `Start New Model` requires confirmation copy: `This clears the current configuration, outputs, and Review chat. Download results first if you want to keep them.`

## Architecture Components

- Frontend: Streamlit-based local web workflow for Configuration, Modelling, Review, exports, resume, and reset.
- App/Data Layer: coordinates CoinGecko access, local cache/session storage, validation boundaries, and export bundling.
- Asset Data Layer: fetches and normalizes CoinGecko token list and price history.
- LLM Layer: uses Perplexity for Configuration Mode, modelling-plan generation, Review Mode explanation, metadata parsing, and guardrail enforcement.
- Modelling Layer: builds datasets, applies transformations, runs `riskfolio-lib`, computes metrics, and produces chart/export artifacts.
- Local App Storage: stores cached CoinGecko data, the single active workflow state, current chat state, and current model output set.
- Export Layer: packages generated artifacts for download.
- Product/UX Layer: reviews and directs the workflow before implementation and during later review passes.
- QA/Validation Layer: validates contracts, workflows, errors, regressions, and acceptance criteria.

## Tech Stack

Confirmed:

| System | Type | Use |
|---|---|---|
| Python | Language | Primary implementation language for app, data, AI integration, and modelling; prefer Python `3.11` for the first modelling feasibility spike. |
| `pyproject.toml` | Dependency file | Root shared dependency source for the local Python app. |
| `uv` | Python dependency/install tooling | Used to resolve and install the local Python environment. |
| `uv.lock` | Python lockfile | Committed for reproducible local installs; regenerated only after approved dependency updates. |
| Streamlit | Python UI framework | Single local web app runtime for the three-phase workflow. |
| pandas | Python data library | Canonical price dataframes and model-specific transformed datasets. |
| `riskfolio-lib` | Python modelling library | Portfolio modelling and strategic asset allocation calculations. |
| Plotly | Python charting library | V1 charts and `.png` chart export where practical. |
| Perplexity Agent API | Multi-provider LLM API | Shared AI integration for Configuration Mode and Review Mode. |
| `perplexity/sonar` | Default LLM model | Initial model for app chat/completion through Perplexity. |
| `perplexityai` | Python SDK | Python client for calling the Perplexity Agent API. |
| CoinGecko Demo API | Market data API | Token list and token price history source. |
| Local filesystem storage/cache | Local persistence model | Stores CoinGecko cache, active user inputs, chat state, and current model outputs under the local app workspace. |

To decide:

- Export packaging dependency.
- Exact local cache/session file formats and schema versioning.
- Frontend-callable app-layer function names and return shapes.
- Model output manifest shape.
- Streamlit pattern for one-open-section Review behaviour.

## Repository Layout

- `/app`: core processing functionality for ingestion, storage management, dataset building, modelling, AI/LLM calls, analysis, and export preparation.
- `/app/ingestion`: CoinGecko data gathering and normalization logic.
- `/app/processing`: dataset building, model preparation, modelling workflows, and output analysis logic.
- `/app/storage`: storage management logic for reading and writing local cache-backed data.
- `/app/ai`: Perplexity/LLM integration logic and prompt orchestration.
- `/frontend`: Streamlit UI/frontend implementation.
- `/scripts`: command-style entry points that trigger app actions and can later be wired to UI buttons.
- `/storage/cache`: stored data only, not application logic.
- `/storage/cache/coingecko`: cached CoinGecko token and price data.
- `/storage/cache/user-inputs`: the single active user input state.
- `/storage/cache/model-outputs`: the current model output set.
- `/docs`: project source of truth for plan, tasks, specs, prompts, validation, and review briefs.

## Data And Storage Decisions

- The app does not require a separate backend service.
- CoinGecko market data is cached locally and persists until the user clears local storage files outside the app.
- Workflow reset must not clear CoinGecko market-data cache.
- `Reset Configuration` requires confirmation copy: `This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.`
- The app supports one active set of user inputs and one active set of model outputs.
- Previous inputs and outputs are recoverable only if the user downloaded them.
- User inputs export as `.json`.
- AI modelling plan exports as `.md`.
- Canonical modelling dataset exports as `.csv`.
- Model tables export as `.csv`.
- Chart images export as `.png`.
- Download bundles are `.zip` files named `allocadabra-results-YYYYMMDD-HHMM.zip`.
- Download bundles include every generated user-facing artifact, including confirmed modelling plan, user input JSON, canonical modelling dataset CSV, model outputs, chart PNGs, chart data CSVs, failed model reasons, missing-artifact placeholders, and the artifact manifest.
- General/comparative outputs live at the bundle root; model-specific outputs live under `models/{model_id}/`.
- Raw CoinGecko cache data is not exportable in V1.
- AI chat transcripts are not exportable in V1.
- Exports are written once after modelling completes and are not regenerated on demand.
- Review UI position does not need to persist; reload defaults to summary metrics and the first model in run order.

## CoinGecko Decisions

- Base URL: `https://api.coingecko.com/api/v3`
- Auth mode: Demo API.
- Auth header: `x-cg-demo-api-key`.
- API key source: `.env`; exact variable name remains to be finalized.
- Use only free public endpoints accessible with the demo key.
- Token list endpoint: `GET /coins/list`.
- Token list parameters: `status=active`, `include_platform=false`.
- Token list normalized fields: `id`, `symbol`, `name`.
- Omit tokens missing any of `id`, `symbol`, or `name`.
- Price endpoint: `GET /coins/{id}/market_chart`.
- Price parameters: `vs_currency=usd`, `interval=daily`, `precision=full`, `days=365`.
- Price normalized fields: UTC `date`, numeric `price`.
- Forward-fill missing prices only after the first valid price.
- Token prices are fetched only after the user confirms scope and starts modelling.
- Assets found during Modelling to have fewer than 90 valid daily prices are recorded in an insufficient-history suppression cache.

## Dataset And Modelling Decisions

- V1 modelling uses up to 365 daily observations from CoinGecko.
- Selected assets need at least 90 valid daily prices.
- Canonical dataset is a pandas price dataframe indexed by UTC date.
- User-facing price columns use `[SYMBOL]_price` where unique; duplicate symbols keep the first `[SYMBOL]_price` label and suffix later duplicates with CoinGecko ID, for example `[SYMBOL]_[COINGECKO_ID]_price`.
- Internal metadata maps dataframe columns back to CoinGecko IDs, symbols, and names.
- Model-specific datasets are produced through reusable transformation functions.
- Initial supported models:
  - Mean Variance.
  - Risk Parity.
  - Hierarchical Risk Parity.
- Future-only model candidates:
  - Worst Case.
  - Ordered Weighted Average.
  - Hierarchical Equal Risk.
- V1 comparison supports no more than 3 models at once.
- Initial outputs include:
  - weights dataframe.
  - side-by-side summary metrics.
  - allocation weights.
  - allocation over time.
  - cumulative performance.
  - drawdown.
  - rolling volatility.
  - efficient frontier where available.
  - risk contribution where available.
  - dendrogram/cluster data where available.
- Allocation-over-time initially repeats static optimized weights across the 365-day window.
- Benchmark rows are deferred beyond V1.
- The Modelling Agent owns solver/runtime feasibility for `riskfolio-lib`, `cvxpy`, and required solvers.
- Dependency additions for modelling must be proposed as a mini spec before editing `pyproject.toml`; the Orchestrator Agent approves and integrates shared dependency changes.
- `pyproject.toml` is the human-edited dependency source; `uv.lock` is committed for reproducible installs and should not be manually edited.
- The modelling runtime feasibility spike confirmed no additional solver dependency is required for the base workflow.
- V1 starts with local Python execution, not Pyodide or pure browser execution.

## Review Metrics

V1 side-by-side comparison should include:

- total return.
- max drawdown.
- Sharpe.
- Calmar.
- Omega.
- Sortino.
- annualized return.
- annualized volatility.
- 30d volatility.
- average drawdown.
- skewness.
- kurtosis.
- CVaR.
- CDaR.

Metric rows should include one-line tooltips and use green/yellow/red ranking alongside visible numbers. Colour must not be the only meaning carrier.

Approved V1 metric defaults:

- Annualization factor: `365`.
- Omega threshold: `0`.
- Sortino target return: `0`.
- CVaR confidence level: `95%`.
- CDaR confidence level: `95%`.

## AI Interaction Modes

Allocadabra uses two AI interaction modes:

- Configuration Mode: helps users select assets, understand preferences, ask technical app-use questions, use supported constraints, and generate/validate the modelling plan.
- Review Mode: helps users interpret outputs, compare trade-offs, understand metrics/charts, and ask technical follow-up questions after model generation.

Shared AI rules:

- Use one shared Perplexity integration.
- Use `perplexity/sonar` through `perplexityai` by default.
- Use `PERPLEXITY_API_KEY`.
- Disable Perplexity web search in V1.
- Do not cite external sources or reference live data in AI responses.
- Inject educational/no-advice/no-warranty guardrails into every AI request.
- Keep responses short by default, with expansion on request.
- Store AI messages in active session state, but do not export chat transcripts.
- Log AI phases and errors, not full prompt/response payloads.
- Reject unsafe, unsupported, or invalid actable AI outputs.

Configuration Mode specifics:

- Receives active user inputs and predefined app/course context.
- Does not receive model outputs.
- Can suggest model changes in chat, but the user must apply them manually.
- During modelling-plan generation, respects the models selected by the user.
- Modelling plan is Markdown plus structured metadata.
- Existing pasted modelling plans can be parsed and validated for import.

Review Mode specifics:

- Receives confirmed modelling plan and model output summary by default.
- Receives visible model/output context automatically on every chat turn.
- May receive detailed data for referenced or visible model/output pairs.
- Does not receive the full Configuration Mode transcript by default.
- Cannot trigger model rebuilds.
- Cannot control Review UI navigation in V1.

## User Interface Direction

- Use three phase screens on one base Streamlit app URL: Configuration, Modelling, Review.
- Configuration and Review use a two-panel desktop layout with AI chat on the left and the active workflow component on the right.
- Modelling uses a focused progress screen with progress bar, micro-log text, elapsed time, animated dots, and collapsed modelling plan.
- V1 is not mobile optimized; mobile users see a holding screen.
- Visual style should be clean, academic, dashboard-like, light/dark compatible, and should avoid crypto-themed branding.
- Configuration and Review use subtle green accent/backlighting for user-led phases.
- Modelling uses subtle red accent/backlighting for app-led processing.
- Configuration and Review show a restrained phase header in the right-hand workflow pane: `CONFIGURATION` or `REVIEW`.
- Modelling shows the phase header `MODELLING` centred in the full screen because it does not use the two-panel layout.
- When Modelling finishes and Review is ready, the accent changes back to green.
- The frontend should not include hackathon or sponsor branding.
- Persistent footer:
  `Experimental project produced for educational purposes only. No warranty as to correctness. Licence: MIT`
- Include `© 2026 Jack Harry Gale`, with `Jack Harry Gale` linking to `https://jackgale.uk`.

## Cross-Cutting Standards

- Logging must follow `/docs/specs/app/logging.md`.
- Use one shared logging utility and named module loggers.
- Production paths should not use `print()` for progress reporting.
- Use parameterized logging rather than f-strings in logger calls.
- User-facing Modelling progress logs are separate from detailed application logs.
- Do not expose raw API keys, prompt payloads, detailed backend logs, or sensitive request data to users.
- All implementation agents should fill in `prompt_used` in their prompt file when starting work.
- All implementation agents should review relevant specs and raise pressing questions before implementation.

## Agent Folder Ownership And Branching

- Each implementation or review agent should work on its own dedicated branch.
- Each agent must keep changes primarily inside its owned folders and assigned docs.
- Folders owned by other agents are not free-edit areas.
- If an agent needs a change outside its owned area, it should stop and return a mini spec instead of editing directly.
- The mini spec should include target folders/files, requested owner agent, proposed change, reason, interface/contract impact, and risks or dependencies.
- The Orchestrator Agent routes mini specs to the relevant owner for review, approval, or implementation.
- Integration happens later through deliberate conflict reviews when agent branches are brought together.
- `/docs` remains the single source of truth for ownership, specs, tasks, prompts, and cross-agent decisions.

## Agent Responsibilities

- Orchestrator Agent: owns `/docs/**`, records project decisions, maintains plan/task/spec consistency, coordinates branches and cross-agent mini specs, and does not write production code.
- Product/UX Agent: owns product/UX review work under `/docs/specs/ux/**`, starting with Design Review 1 before code-producing agents begin.
- Backend/Data Agent: owns `/app/ingestion/**`, `/app/storage/**`, data/cache contracts for `/storage/cache/**`, CoinGecko ingestion, local cache/session storage, frontend-facing data interfaces, export bundling boundaries, and active workflow persistence.
- Modelling Agent: owns `/app/processing/**`, dataset preparation, transformation registry, `riskfolio-lib` integration, solver/runtime feasibility, model execution, metrics, and model output artifacts.
- AI/Perplexity Agent: owns `/app/ai/**`, Perplexity integration, guardrails, prompt templates, Configuration/Review orchestration, response parsing, metadata validation, fixed refusal/error messages, and chat/session hooks.
- Frontend Agent: owns `/frontend/**`, Streamlit screens/components, phase transitions, chat rendering, parameters UI, modelling progress UI, review UI, downloads, and visible-context exposure.
- QA/Validation Agent: owns `/docs/validation/**` and validation/test strategy, including acceptance criteria, contract checks, workflow tests, error coverage, and regression validation.

## Implementation Gate

Before code-producing agents start:

1. Product/UX Agent completes Design Review 1 and raises exactly 10 high-priority UX questions.
2. Orchestrator/user answers or triages those questions.
3. Orchestrator updates relevant specs, prompts, and tasks.

Early implementation tasks should then resolve interface contracts:

- Backend/Data Agent defines cache/session schemas and frontend-facing state interfaces.
- Backend/Data Agent defines callable token-list, validation, and export-bundling interfaces.
- AI/Perplexity Agent defines callable AI plan/chat interfaces and fixed refusal/error messages.
- Modelling Agent defines callable run/progress/output-manifest interfaces.
- Frontend Agent decides the one-open-section Review implementation pattern in Streamlit.

## Key V2 / Deferred Items

- Mobile-optimized UI.
- Pure browser/Pyodide runtime.
- Web search through Perplexity.
- Alternate LLM/provider options.
- Chat transcript export.
- Full Configuration transcript access in Review Mode.
- Direct modelling-plan editing.
- Benchmarks and benchmark rows.
- Worst Case, Ordered Weighted Average, and Hierarchical Equal Risk models.
- Rolling optimization or scheduled rebalancing.
- Multiple open Review sections.
- Persisting Review open section/selected model across reload.
- Resuming interrupted modelling runs after reload.
- Retrying failed individual models before entering Review.
- AI-controlled Review UI navigation.
