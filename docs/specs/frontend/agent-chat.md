created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# Agent Chat Spec

## Purpose

Define the AI chat box component used for Perplexity interactions throughout the app workflow.

## Initial Scope

- Provide an AI chat interface for parameter-setting support.
- Provide an AI chat interface for reviewing and discussing model results.
- Keep chat context aligned with the current workflow phase.
- Route app-provided prompts and user messages to the AI integration layer.

## Notes

- This spec should define chat UI states, context injection, message persistence, loading/error states, and phase-specific behaviour after the initial contract pass.
- This spec depends on the AI model integration, parameters agent, and review agent specs.
