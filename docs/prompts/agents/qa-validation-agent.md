created: 2026-04-21 08:33:31 BST
last_updated: 2026-04-21 10:01:04 BST
prompt_used:

# QA/Validation Agent Prompt

## Prompt Use Instruction

When an agent starts work from this prompt, the first action must be to fill in `prompt_used` above with the current timestamp.

## Role

Owns acceptance criteria, contract checks, workflow tests, and regression coverage across agents.

## Status

Placeholder. Full prompt to be prepared later.

## Validation Notes To Include

- Dataset-building validation must cover selected asset limit, missing/fetchable price history, minimum valid price observations, empty transformed datasets, and excessive missing data.
- Dataset-building failures should map to user-facing UI errors.
- Relevant spec: `/docs/specs/data-backend/dataset-building.md`.
