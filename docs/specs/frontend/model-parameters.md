created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-22 11:09:19 BST

# Model Parameters Spec

## Purpose

Define the component that lets users set and adjust parameters during the modelling preparation phase.

## Initial Scope

- Let users select assets from CoinGecko-backed options.
- Let users specify preferences for the modelling process.
- Support AI-assisted parameter setting through Configuration Mode.
- Prepare user inputs for the AI-generated model plan.

## Required Inputs

- Selected assets.
- Treasury objective.
- Risk appetite.
- Selected models, defaulting to the initial 3 supported models.

Optional:

- Supported predefined constraints.

Do not include benchmark preference or time horizon as user inputs in V1.

## Notes

- This spec should define required fields, optional preferences, validation rules, asset search behaviour, and handoff to the AI model plan flow after the initial contract pass.
- This spec depends on the CoinGecko API and parameters agent specs.
