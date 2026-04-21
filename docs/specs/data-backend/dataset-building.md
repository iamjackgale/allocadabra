created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# Dataset Building Spec

## Purpose

Define how a modelling dataset is prepared after the user confirms the AI-generated model plan.

## Initial Scope

- Build modelling-ready datasets from selected CoinGecko assets and cached price data.
- Apply user preferences specified in the UI.
- Prepare data in the shape required by the modelling layer.
- Run after the model plan is agreed and before riskfolio-lib execution.

## Notes

- This spec should define input data shape, preference handling, missing-data rules, date-range rules, return calculations, and output dataset shape after the initial contract pass.
- This spec connects frontend preferences, CoinGecko data, and riskfolio-lib execution.
