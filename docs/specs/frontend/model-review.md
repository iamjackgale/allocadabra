created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 11:09:19 BST

# Model Review Spec

## Purpose

Define the component that lets users review model outputs and download copies of generated artifacts.

## Initial Scope

- Present comparable summaries of model outputs.
- Let users explore individual model outputs in more detail.
- Support AI-assisted review and trade-off discussion through Review Mode.
- Let users download generated results and related files.

## AI Context Awareness

The Model Review Component should expose the currently visible model and output type to Review Mode so the AI can receive relevant detailed data for what the user is viewing.

Examples:

- visible model: Hierarchical Risk Parity.
- visible output type: allocation-over-time chart.

Review Mode should not receive unrelated model output details by default.

## Notes

- This spec should define summary views, detail views, comparison behaviour, export interactions, and review chat integration after the initial contract pass.
- This spec depends on the riskfolio-lib, session storage, and review agent specs.
