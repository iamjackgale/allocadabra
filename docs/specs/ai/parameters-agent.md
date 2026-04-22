| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 20:23:50 BST |

# Parameters Agent Spec

## Purpose

Define prompts and context for the AI chat experience during Configuration Mode.

Configuration Mode covers initial asset selection, preference setting, modelling scope clarification, modelling-plan generation, and supported model subset suggestion.

## Responsibilities

- Help users select assets and describe modelling preferences.
- Answer technical questions about how to use the app.
- Clarify missing configuration details.
- Generate a human-readable modelling plan in Markdown.
- Suggest a subset from supported model names only.
- Keep suggestions appropriate for an educational crypto treasury setting.
- Avoid presenting modelling suggestions as financial advice.

## Configuration Inputs

The Configuration Agent helps collect:

| Input | Required | Notes |
|---|---|---|
| Selected assets | Yes | Selected from CoinGecko-backed dropdown. Minimum 2, maximum 10. |
| Treasury objective | Yes | One of: `Maximize return`, `Stable performance`, `Best risk-adjusted returns`, `Reduce drawdowns`, `Diversify exposure`. |
| Risk appetite | Yes | One of: `Very low`, `Low`, `Medium`, `High`, `Very high`. |
| Selected models | Yes | Up to 3 supported models. Default to the first 3 available models if the user does not choose. |
| Constraints | No | Use only predefined constraints the modelling system can handle. |

Do not collect benchmark preference in Configuration Mode. Benchmarking should be standardized by the app for teaching purposes.

Do not collect a time horizon in the initial configuration flow. The modelling window is the last 365 daily observations available from CoinGecko.

## Optional Constraints

Constraint collection should remain simple and predefined.

Supported V1 constraint categories:

- max allocation per asset.
- min allocation per asset.
- max allocation to selected asset.
- min allocation to selected asset.
- max number of assets in portfolio.
- min number of assets in portfolio.

If a requested constraint is not supported by the modelling system, the agent should explain that it cannot be configured in the current app.

The agent may suggest which available constraint preset to use, but it must not directly mutate the configuration form.

## Minimum Complete Configuration

The agent may generate a modelling plan only when these requirements are met:

- At least 2 selected assets.
- No more than 10 selected assets.
- Treasury objective is set.
- Treasury risk appetite is set.
- Selected model IDs are present, defaulting to the initial 3 supported models if needed.

The agent should proactively ask only for required missing fields. Optional fields should not block progress.

## Context Inputs

Configuration Mode may receive:

- Active user inputs.
- Selected assets and CoinGecko asset metadata.
- Current app constraints:
  - maximum 10 selected assets.
  - maximum 3 compared models.
  - maximum 365 daily observations.
  - minimum 90 valid daily prices per selected asset.
- Supported model list:
  - `mean_variance`
  - `risk_parity`
  - `hierarchical_risk_parity`
- Standard guardrail prompt from `/docs/specs/ai/ai-model-integration.md`.
- Course/app context explaining this is an educational crypto treasury tool.

Configuration Mode must not receive:

- Model outputs.
- Review Mode transcript.

## Asset Guidance Rules

The agent must not recommend specific assets as investment choices.

The agent may:

- Explain asset categories and selection considerations.
- Reference well-known examples for category explanation only.
- Explain that stablecoins may be a weaker fit for return-based price models because they are designed for price stability rather than price appreciation, without blocking their use.

Potential categories for later refinement:

- blue chips.
- altcoins.
- stablecoins.
- liquid-staking tokens.
- governance tokens.

## Outputs

Chat output:

- Renderable chatbot text.
- Keep formatting lightweight and efficient.

Modelling plan:

- Human-readable Markdown.
- Stored in active session state.
- Exportable as `.md`.
- Reused as context for Review Mode.
- Does not need to include plain-language explanations of each selected model; model explanations should be provided by the UI.
- Generated from current app state plus the latest relevant user message, not the full chat transcript unless needed.
- Direct user editing is not supported in V1; users can accept, regenerate, or paste an existing plan for import.

Required headings:

- Objective.
- Risk Appetite.
- Selected Assets.
- Constraints.
- Selected Models.
- Data Window.

Structured metadata:

- Suggested model IDs.
- Any app-actable configuration decisions.
- Missing required configuration fields, if any.

## Model Suggestion Rules

- Suggested model IDs must be from the initial supported set only.
- In normal chat, the agent may suggest one, two, or three supported models, but the user must manually apply any change in the configuration component.
- During modelling-plan generation, the agent should respect the models currently selected by the user and should not independently change the subset.
- If the user requests unsupported models, the agent should softly refuse and adopt the default supported model set unless the user chooses another supported subset.
- The agent must not suggest future-only models:
  - Worst Case.
  - Ordered Weighted Average.
  - Hierarchical Equal Risk.
- The user must confirm the modelling plan before model execution.

## Existing Plan Import

If a user pastes a complete modelling plan into the Configuration Mode chat, the agent should recognize it and adopt it without changes where possible.

The app should still validate:

- required fields.
- supported model IDs.
- asset count limits.
- metadata needed to execute the plan.

If the pasted plan is incomplete or invalid, the agent should explain what must be fixed.

## Guardrails

The agent must:

- Frame all guidance as educational and technical.
- Avoid financial advice.
- Avoid buy/sell/hold recommendations.
- Avoid warranty or accuracy guarantees.
- Make uncertainty and modelling limitations clear.
- Use neutral language suitable for students.

## Blocking Behaviour

The agent may block modelling plan generation when required inputs or model constraints fail.

When blocking, it should:

- explain why the configuration cannot be modelled yet.
- identify the exact field or constraint that must change.
- avoid implying the selected strategy is bad investment judgement.

## Handoff To Modelling Phase

Configuration Mode ends when:

1. the user confirms the modelling plan, and
2. model generation begins.

The app should then:

- Store the confirmed modelling plan.
- Store structured model IDs selected for execution.
- Enter the Modelling Phase.

Configuration Mode does not hand directly to Review Mode. The Modelling Phase runs after plan confirmation and before Review Mode.

## Relationship To Other Specs

- `/docs/specs/ai/ai-model-integration.md` defines provider integration and shared guardrails.
- `/docs/specs/frontend/model-parameters.md` defines the UI component this agent supports.
- `/docs/specs/data-backend/session-storage.md` defines active session state.
