| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-24 13:18:28 BST |

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
- Keep default answers to one paragraph unless the user explicitly asks for more detail.

Modelling plan output:

- Must be stored in human-readable Markdown.
- Must include structured metadata alongside the Markdown where the app needs to act on the output.
- Required structured metadata includes selected model IDs when the agent suggests a model subset.
- Plan metadata is normalized by typed AI helpers before storage.
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

## Initial App Interfaces

Initial AI scaffolding exposes frontend-callable helpers from `app.ai.data_api`:

| Function | Purpose |
|---|---|
| `send_configuration_chat(user_message, active_inputs=None)` | Send one Configuration Mode chat turn, store the user message, store a safe assistant response, and return `{ok, message, metadata, workflow}` or a recoverable error shape. |
| `generate_modelling_plan(active_inputs=None, latest_user_message=None)` | Validate current configuration, call Perplexity, parse Markdown plus metadata, reject unsafe or invalid metadata, store the generated unconfirmed plan, and return `{ok, markdown, metadata, workflow}`. |
| `import_modelling_plan(markdown, metadata=None)` | Parse and validate a pasted modelling plan, reject incomplete or unsupported plans, and store a generated unconfirmed plan when valid. |
| `send_review_chat(user_message, model_output_summary=None, visible_context=None, detailed_context=None)` | Send one Review Mode chat turn after Review is ready, using summary plus visible context and narrowing any detailed context to referenced or visible models/output types before the prompt is sent. |
| `generate_review_opening(ranking_summary, model_output_summary)` | Generate the first neutral Review comparison from deterministic ranking inputs and store it in Review chat. |
| `get_fixed_financial_advice_refusal()` | Return the standard fixed refusal for financial-advice requests. |
| `get_generic_safe_error()` | Return the generic replacement message for unsafe or invalid AI responses. |

All public helpers return dictionaries with `ok: true` on success. Recoverable failures return `ok: false`, a stable `code`, and user-facing `message`; validation failures may include `issues`. Raw prompts and raw provider responses are not returned to the frontend by default.

Configuration and Review chat may short-circuit certain requests before using provider output when a deterministic app-safe response is preferable, including:

- direct financial-advice requests.
- direct requests to choose a model on the user's behalf.
- requests for live data outside the app's V1 scope.
- requests for unsupported or future-only models.

Configuration chat may also answer simple readiness checks from deterministic app validation state so missing required fields and current supported selections stay aligned with the form.

## Structured Metadata Validation

The AI layer validates app-actable metadata through typed helpers before storing it in active workflow state.

Modelling-plan metadata must normalize to:

- `kind`.
- `selected_model_ids`.
- `missing_required_fields`.
- `parsed_plan.objective`.
- `parsed_plan.risk_appetite`.
- `parsed_plan.selected_assets`.
- `parsed_plan.constraints`.
- `parsed_plan.selected_model_ids`.
- `parsed_plan.data_window`.

Review response metadata may normalize to:

- `kind`.
- `referenced_model_ids`.
- `referenced_metric_names`.
- `referenced_artifact_ids`.
- `referenced_output_table_names`.
- `needs_detailed_context`.

If visible text and metadata conflict on app-actable fields, the metadata is rejected. Unsupported or future-only model IDs are rejected in all app-actable metadata. Future-only model names in modelling-plan text are rejected so the displayed plan cannot imply unsupported execution.

## Supported Model Constraint

The AI may suggest only the initial supported models:

| Model ID | User-Facing Name |
|---|---|
| `mean_variance` | Mean Variance |
| `risk_parity` | Risk Parity |
| `hierarchical_risk_parity` | Hierarchical Risk Parity |

Worst Case, Ordered Weighted Average, and Hierarchical Equal Risk are future-only and must not be suggested for first-build execution.

The AI layer should load the supported V1 model set from the Modelling-owned contract where practical. If the Modelling contract cannot be imported in the current runtime, the AI layer may fall back to one fixed V1 helper containing:

- `mean_variance`
- `risk_parity`
- `hierarchical_risk_parity`

All Configuration and Review metadata validation should use the same AI-owned supported-model access path.

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
- The app may bypass provider output entirely for direct financial-advice requests and return the fixed refusal deterministically.
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
