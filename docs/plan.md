created: 2026-04-21 20:06:11 BST
last_updated: 2026-04-21 20:06:11 BST

# Allocadabra Project Plan

## Project Goal

Allocadabra is a web application for students on an intro crypto treasury management course. It helps users explore strategic crypto treasury allocation by selecting assets, describing preferences, confirming an AI-generated modelling plan, comparing model outputs, and reflecting on trade-offs.

Allocadabra wraps `riskfolio-lib`; it does not modify or fork the library. The product is educational and should not present outputs as financial advice, trading instructions, or guaranteed outcomes.

## V1 Workflow

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
- Backend/API: coordinates frontend requests, CoinGecko data access, Perplexity calls, modelling execution, local cache, and exports.
- Asset Data Layer: fetches and normalizes crypto asset options from CoinGecko for searchable selection.
- LLM Layer: uses Perplexity to generate the natural-language modelling plan, suggest supported model subsets, and support post-result reflection.
- Modelling Layer: wraps `riskfolio-lib` and runs only confirmed models from the supported model set.
- Local Cache: stores in-progress workflow state so users can leave and resume.
- Export Layer: packages generated outputs for download after modelling and reflection.

## Agent Responsibilities

- Orchestrator Agent: owns `/docs`, records project decisions, maintains plan/task/spec consistency, and does not write production code.
- Frontend Agent: owns the student-facing web workflow and result exploration experience.
- Backend/API Agent: owns service boundaries, API coordination, cache integration, and export endpoints.
- Asset Data Agent: owns CoinGecko integration and asset-option normalization.
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

## Deferred Specs

Specs and contracts are the next planning action after this V1 outline is committed. Do not populate detailed specs yet.

Expected future specs include:

- CoinGecko asset option contract.
- User preference capture contract.
- Perplexity modelling-plan contract.
- Supported model registry contract.
- Riskfolio-Lib execution contract.
- Result summary and exploration contract.
- Reflection conversation contract.
- Local cache/session state contract.
- Export contract.
