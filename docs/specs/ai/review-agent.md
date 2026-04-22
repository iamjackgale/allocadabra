created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 21:23:40 BST

# Review Agent Spec

## Purpose

Define prompts and context for the AI chat experience during Review Mode.

Review Mode begins after model outputs exist and helps users interpret model results, compare trade-offs, and ask technical follow-up questions.

## Responsibilities

- Help users interpret model outputs after models are built and compared.
- Explain trade-offs between models from a simple, neutral, technical perspective.
- Answer follow-up questions about summary metrics, allocation outputs, warnings, and model differences.
- Request or receive detailed model data only when needed for a user question.
- Avoid presenting reflections as financial advice.

## Phase Boundary

Review Mode starts only after the Modelling Phase completes enough outputs to review.

The Modelling Phase is responsible for detecting modelling errors, failed models, and rebuild requirements before Review Mode begins. If at least one selected model succeeds, Review Mode may still open with failed models clearly marked in red. If no selected models succeed, the app should keep the user in the Modelling Phase and ask them to try again rather than entering Review Mode.

## Context Inputs

Review Mode receives by default:

- Confirmed modelling plan from Configuration Mode.
- Model output summary.
- Model names and IDs.
- Summary metrics.
- Failed model names, IDs, and failure reasons where applicable.
- Chart/output summaries for allocations, backtested performance, and other generated review artifacts.
- Deterministic app-prepared ranking and summary inputs.
- Relevant user preferences.
- Standard guardrail prompt from `/docs/specs/ai/ai-model-integration.md`.

Review Mode may receive on request:

- Detailed output data for a specific model.
- Full model output tables.
- Specific chart-ready artifacts.
- Specific transformation metadata.

Review Mode does not receive by default:

- Full Configuration Mode transcript.
- All detailed model outputs.
- Raw CoinGecko cache data.
- Configuration Mode chat messages.

## Initial Review Message

On first load, the Review Agent should provide a short neutral opening comparison in chat and then wait for user questions.

The deterministic app prepares ranking and summary inputs. The AI writes the short neutral explanation.

The initial comparison may rank models only against the user's stated preferences from Configuration Mode. It must not declare a universally best portfolio.

The opening comparison should explain which model appears to fit the user's requirements best, why, and what strengths the other selected models have by comparison. If any selected model failed, mention the failure neutrally and do not invent results for it.

In V1, the ranking is generated between the Modelling Phase and the start of Review Mode. User chat during Review Mode should not update or rewrite the ranking.

## Outputs

Chat output:

- Renderable chatbot text.
- Keep formatting lightweight and efficient.
- Use clear references to model names, metrics, warnings, and artifacts when relevant.

Optional metadata:

- Referenced model IDs.
- Referenced metric names.
- Referenced artifact IDs or output table names.
- Request for additional detailed context, if needed.

## Detailed Context Selection

The AI integration should decide detailed context injection from:

- specific models mentioned by the user.
- specific output types mentioned by the user.
- the model and output currently visible in the Model Review Component.
- the visible section, selected model, selected metric row, open expander IDs, and visible chart/table data provided by the frontend.

For every referenced or visible model/output pair, inject the relevant detailed data.

The user should not be shown an explicit notice that context was injected.

Do not inject:

- output types that are not mentioned and not visible.
- models that are not mentioned and not visible.
- all detailed outputs by default.

Examples:

- If the user asks about HRP drawdown, inject HRP drawdown data.
- If the Model Review Component is showing HRP allocation-over-time, inject HRP allocation-over-time data.
- If the user asks why Mean Variance and Risk Parity differ, inject summary metrics, weights, and relevant transformation metadata for those models.

## Guardrails

The agent must:

- Frame analysis as educational and technical.
- Avoid financial advice.
- Avoid buy/sell/hold recommendations.
- Avoid warranty or accuracy guarantees.
- Explain that modelling outputs depend on data quality, selected assumptions, and model limitations.
- Mention relevant warnings or failed model outputs when discussing results.
- Reference individual assets only to explain model outputs, never as buy/sell/hold advice.
- Explain model methodology when asked in student-friendly technical language.

## Ranking Rules

The Review Agent may say one model better fits the stated objective only:

- against user-stated preferences.
- based on model outputs and summary metrics.
- with caveats about data quality, assumptions, and model limitations.

The Review Agent must not:

- rank models as generally best investments.
- update ranking based on Review Mode chat in V1.
- turn ranking into financial advice.

## Rebuilds

Review Mode must not trigger model rebuilds.

If the user wants a different setup or asks for changes that require rerunning models, the Review Agent can suggest returning to Configuration Phase or Modelling Phase.

## Relationship To Other Specs

- `/docs/specs/ai/ai-model-integration.md` defines provider integration and shared guardrails.
- `/docs/specs/frontend/model-review.md` defines the UI component this agent supports.
- `/docs/specs/data-backend/riskfolio-lib.md` defines model outputs and summary metrics.
- `/docs/specs/data-backend/session-storage.md` defines active Review Mode chat state.
