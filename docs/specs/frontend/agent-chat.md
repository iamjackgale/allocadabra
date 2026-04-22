created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 11:09:19 BST

# Agent Chat Spec

## Purpose

Define the AI chat box component used for Perplexity interactions throughout the app workflow.

## Initial Scope

- Provide an AI chat interface for Configuration Mode parameter-setting support.
- Provide an AI chat interface for Review Mode result interpretation and discussion.
- Keep chat context aligned with the current workflow phase.
- Route app-provided prompts and user messages to the AI integration layer.

## Modes

### Configuration Mode

- Supports asset selection, preference setting, technical app-use questions, modelling-plan generation, and supported model subset suggestion.
- Uses active user inputs and predefined app/course context.
- Does not include model outputs.

### Review Mode

- Supports interpretation and analysis of model outputs.
- Uses confirmed modelling plan and model output summary by default.
- Can request or display deeper context when the user asks about a specific output.
- Receives awareness of the model/output currently visible in the Model Review Component so the AI can discuss what the user is looking at.

## Session Behaviour

- Configuration Mode and Review Mode are separate chat sessions in the active workflow.
- Configuration Mode chat context is wiped before Review Mode.
- The confirmed modelling plan is reinjected into Review Mode.
- Chat transcripts are not exportable in V1.

## Notes

- This spec should define chat UI states, context injection, message persistence, loading/error states, and phase-specific behaviour after the initial contract pass.
- This spec depends on the AI model integration, parameters agent, and review agent specs.
