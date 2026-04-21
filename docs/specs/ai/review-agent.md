created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# Review Agent Spec

## Purpose

Define prompts and context for the AI chat experience during model result review.

## Initial Scope

- Help users interpret model outputs after models are built and compared.
- Support reflection on trade-offs between model results.
- Use model outputs and user preferences as context.
- Avoid presenting reflections as financial advice.

## Notes

- This spec should define system prompts, result-context injection, allowed outputs, guardrails, and export-related behaviours after the initial prompt pass.
- This spec depends on the model review and AI model integration specs.
