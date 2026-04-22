created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 13:02:38 BST

# AI Model Integration Spec

## Purpose

Define how Allocadabra connects to external LLMs through Perplexity and exposes one shared app integration for Configuration Mode and Review Mode.

## Provider

| Field | Decision |
|---|---|
| Provider | Perplexity |
| API | Perplexity Agent API |
| SDK | `perplexityai` Python SDK |
| Default model | `perplexity/sonar` |
| API key env var | `PERPLEXITY_API_KEY` |
| Endpoint reference | `POST https://api.perplexity.ai/v1/agent` |

Notes:

- Perplexity Agent API is multi-provider and can access models from multiple providers through a unified interface.
- The initial implementation should use `perplexity/sonar`.
- Default to `perplexity/sonar`; allow an environment override later only if straightforward.
- The integration should leave room for additional model options later, but alternate models are not required for the first build.
- API keys must come from `.env`/environment configuration and must not be committed.

## Shared Integration

Use one shared app integration for all Perplexity calls.

The app should:

- Initialize the Perplexity SDK client from `PERPLEXITY_API_KEY`.
- Route Configuration Mode and Review Mode requests through the same integration layer.
- Inject the standard guardrail prompt into every AI request.
- Log requests, phases, recoverable failures, and errors according to `/docs/specs/app/logging.md`.
- Do not log full prompt or response contents by default.
- Store AI messages in the active session state according to `/docs/specs/data-backend/session-storage.md`.
- Disable Perplexity web search in V1.

## Response Format

Default chat responses:

- Prefer plain text/Markdown-style text that is efficient to render in a chatbot UI.
- Do not spend extra compute on polished formatting unless needed for comprehension.

Modelling plan output:

- Must be stored in human-readable Markdown.
- Must include structured metadata alongside the Markdown where the app needs to act on the output.
- Required structured metadata includes selected model IDs when the agent suggests a model subset.
- Must be exportable exactly as displayed.

Modelling plan Markdown headings:

- Objective.
- Risk Appetite.
- Selected Assets.
- Constraints.
- Selected Models.
- Data Window.

`Educational Caveats` is a candidate V2 heading, not required in V1.

Actable AI output:

- Any AI output that changes app behaviour must include app-readable metadata.
- User-facing text and actable metadata must be stored together in session state.

## Standard Guardrail Prompt

Every AI request must include standard context explaining:

- Allocadabra is an educational crypto treasury modelling tool.
- Outputs are educational and technical, not financial advice.
- No warranty is given as to the accuracy of data, modelling outputs, or AI explanations.
- The agent must not recommend buying, selling, holding, or trading assets.
- The agent must not imply guaranteed returns or certain outcomes.
- The agent must only reference supported model names when suggesting models.
- In Configuration Mode, the agent guides users through app setup and modelling configuration.
- In Review Mode, the agent explains results from a simple, neutral, technical perspective.
- Responses should be short by default, normally one paragraph.
- Responses may expand to 3-5 paragraphs when the user asks for more detail.
- The agent should admit uncertainty around model limitations, data quality, and unsupported requests.
- If asked for financial advice, the agent must refuse with the standard educational/no-warranty framing and say users should consult a professional financial advisor before making investment decisions.

## Supported Modes

### Configuration Mode

Purpose:

- Help the user configure assets, preferences, and modelling scope.
- Answer technical questions about how to use the app.
- Generate the modelling plan for user confirmation.
- Suggest a subset from supported model names only.

Context sent:

- Active user inputs.
- Predefined app/course context.
- Supported model list and model IDs.
- No model outputs.

Outputs:

- Chat messages for display.
- Human-readable modelling plan in Markdown.
- Structured metadata for selected/suggested model IDs.

### Review Mode

Purpose:

- Help the user interpret and compare model outputs.
- Explain trade-offs neutrally and technically.
- Answer follow-up questions about results.

Context sent by default:

- Model output summary.
- Model warnings/failure messages.
- Confirmed modelling plan from Configuration Mode.
- Relevant user preferences.

Detailed context:

- Full or detailed output data should be sent only when the user asks about a specific model output or deeper detail.
- Do not send all detailed model output data by default.

Outputs:

- Chat messages for display.
- Optional references to specific models, metrics, warnings, or artifacts.

## Session Handling

- AI messages are part of the single active workflow state.
- Store Configuration Mode and Review Mode as separate chat sessions inside the active workflow state.
- Clear/wipe chat context between Configuration Mode and Review Mode.
- Reinject the confirmed modelling plan from Configuration Mode into Review Mode.
- Review Mode does not need the full Configuration Mode transcript by default.
- If future behaviour requires Configuration Mode transcript access, it must be explicitly added to this spec.
- AI chat transcripts are not exportable in V1.

## Supported Model Constraint

The AI may suggest only the initial supported models:

| Model ID | User-Facing Name |
|---|---|
| `mean_variance` | Mean Variance |
| `risk_parity` | Risk Parity |
| `hierarchical_risk_parity` | Hierarchical Risk Parity |

Worst Case, Ordered Weighted Average, and Hierarchical Equal Risk are future-only and must not be suggested for first-build execution.

## Web Search

Perplexity web search should be off in V1.

The agent should not cite external sources, reference live data, or retrieve current information. It should rely on:

- the gathered CoinGecko data available in the app.
- model outputs and summaries produced by the app.
- predefined app/course context.
- general model knowledge without citations.

Web search is a potential V2 feature.

## Error Handling

- Missing `PERPLEXITY_API_KEY` should produce a clear user-facing setup error.
- Provider failures should produce a recoverable app error where possible.
- Invalid or unsupported model IDs in AI metadata must be rejected.
- If AI text and structured metadata conflict, structured metadata should be rejected and the user should be asked to regenerate or confirm manually.
- If Perplexity is unavailable, show a recoverable error and let the user retry; do not proceed to AI-required steps.
- If AI returns financial advice despite guardrails, discard or replace the output with a refusal/error message and allow the user to prompt a further AI analysis on the same educational basis.
- There is no manual fallback in V1; the app does not work if AI is unavailable for AI-required steps.

## Implementation Ownership

The AI/Perplexity implementation owns:

- Perplexity integration.
- Prompt templates.
- Configuration Mode and Review Mode orchestration.
- Response parsing.
- Structured metadata schemas for actable AI outputs.
- Model ID validation for AI suggestions.
- Session/chat state hooks.

The AI/Perplexity implementation does not own:

- frontend rendering.
- the supported model registry source of truth.
- model execution.

## References

- Perplexity Agent API quickstart: `https://docs.perplexity.ai/docs/agent-api/quickstart`
