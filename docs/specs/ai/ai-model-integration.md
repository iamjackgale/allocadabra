created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# AI Model Integration Spec

## Purpose

Define how Allocadabra connects to external LLMs through APIs, specifically Perplexity.

## Initial Scope

- Send prompts and context from the app to Perplexity.
- Receive and process responses from Perplexity.
- Inject standard app prompts into model-plan and review workflows.
- Keep AI responses constrained to the app's supported workflow and model names.

## Notes

- This spec should define provider configuration, request/response handling, prompt injection strategy, error handling, and validation boundaries after the initial contract pass.
- This spec is shared by the parameters agent and review agent specs.
