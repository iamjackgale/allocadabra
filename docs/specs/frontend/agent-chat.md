created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 14:57:42 BST

# Agent Chat Spec

## Purpose

Define the AI chat box component used for Perplexity interactions throughout the app workflow.

## Initial Scope

- Provide an AI chat interface for Configuration Mode parameter-setting support.
- Provide an AI chat interface for Review Mode result interpretation and discussion.
- Keep chat context aligned with the current workflow phase.
- Route app-provided prompts and user messages to the AI integration layer.

## Component Design

- Build one reusable Streamlit chat component configured by mode.
- Use different agent sessions, prompts, stored state, and context injection depending on Configuration Mode or Review Mode.
- Prefer Streamlit-native chat primitives where practical:
  - `st.chat_message` for message display.
  - `st.chat_input` for text input.
- The implementation may take product inspiration from Chatbot UI or Gradio chat patterns, but these are not dependencies unless explicitly added by the Frontend Agent.

## Layout

- Desktop: chat sits in the left panel during Configuration and Review.
- Mobile: V1 is not optimized; show a holding screen rather than a fully responsive chat.
- Configuration and Review chat panels should feel similar, but must use separate mode context.
- The chat panel is always visible in Configuration and Review.
- The chat is available immediately for general user questions, even before minimum modelling inputs are complete.

## Behaviour

- Responses should be short by default, normally one paragraph.
- The user can ask for expansion, capped at approximately 3-5 paragraphs.
- The chat should show user messages, AI messages, loading state, and recoverable error state.
- Chat should not expose raw prompt payloads or technical metadata to the user.
- Chat should not be exportable in V1.
- Message timestamps are not required.
- Assistant messages should support Markdown rendering if Streamlit-native rendering is straightforward.
- User message input should support multiline input if Streamlit supports it without heavy custom work.
- Do not include quick action buttons in V1; use free text only.

## Modes

### Configuration Mode

- Supports asset selection, preference setting, technical app-use questions, modelling-plan generation, and supported model subset suggestion.
- Uses active user inputs and predefined app/course context.
- Does not include model outputs.
- Proactively asks only for required missing fields.
- Stays lightweight for optional constraints and non-required preferences.
- Can recognize a pasted modelling plan, route it for metadata parsing, and adopt it only after validation.
- Supports `Generate Plan`, `Regenerate`, and `Accept` plan interactions.
- Has access to current incomplete configuration on every message.
- Should automatically explain what required fields are missing to successfully generate the plan.
- Can suggest how to use available constraint presets, including when a user expresses a preference such as avoiding too much exposure to specific assets.
- Does not directly update Model Configuration Component state; it suggests changes for the user to apply.
- If the user pastes a modelling plan, show the pasted plan in chat and handle parsing/adoption invisibly after validation.
- Unsupported model requests should be surfaced in chat and should also mark the relevant form/model-selection control invalid.

### Review Mode

- Supports interpretation and analysis of model outputs.
- Uses confirmed modelling plan and model output summary by default.
- Can request or display deeper context when the user asks about a specific output.
- Receives awareness of the model/output currently visible in the Model Review Component so the AI can discuss what the user is looking at.
- Receives visible model and visible output type from the frontend before the next user chat turn.
- Should provide a short neutral opening comparison on first Review load using deterministic app-prepared summary/ranking inputs.
- Review Mode does not trigger model rebuilds.
- Receives visible output context automatically on every message.
- Does not display injected context details to the user.
- On entering Review, the Model Review Component opens the summary metrics comparison by default.
- The Review Mode agent should receive those high-level metrics and provide a basic overview of:
  - which model performed best based on user requirements.
  - why it performed best.
  - what the strengths of the other selected models are by comparison.
- Review chat cannot trigger UI navigation or control the visible review component in V1.

## Session Behaviour

- Configuration Mode and Review Mode are separate chat sessions in the active workflow.
- Configuration Mode chat context is wiped before Review Mode.
- The confirmed modelling plan is reinjected into Review Mode.
- Chat transcripts are not exportable in V1.
- If Modelling fails before Review, Configuration chat can be restored with the prior configuration and plan.
- Chat history persists across browser refresh/local app reload within the active workflow.
- Configuration chat persists through Configuration and Modelling.
- Configuration chat is wiped only after review files have loaded and the app transitions fully into Review.
- If the user refreshes after Review is ready, the app should reopen in Review, not Modelling or Configuration.
- Review chat resets when the user clicks `Start New Model`.

## Failure Handling

- Failed AI calls should preserve the user's sent message for retry.
- Repeated failures should stop automatic retries and ask the user to wait and refresh rather than spamming the same failing call.
- No-financial-advice refusals should use a standard fixed message stored in the repo, not free-form AI-generated refusal text.
- Unsafe or invalid AI responses should be replaced with a generic safe error message.

## Logging

- Chat logging should stay simple.
- Log phase events and errors only.
- Do not log full prompt or response payloads by default.
- Message counts and response latency are not required for V1 chat logging.
- Detailed modelling progress logging belongs to a separate Modelling progress/log component spec.

## Notes

- This spec depends on the AI model integration, parameters agent, and review agent specs.
