created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# Session Storage Spec

## Purpose

Define how user workflow state is stored locally and retrieved by the app.

## Initial Scope

- Store user inputs.
- Store AI-generated model plans.
- Store confirmed model selections.
- Store model outputs.
- Retrieve cached state so users can resume an in-progress workflow.
- Provide stored outputs for export.

## Notes

- This spec should define session identity, local cache format, expiration behaviour, reset behaviour, export access, and separation from cached market data after the initial contract pass.
