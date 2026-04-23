| Metadata | Value |
|---|---|
| created | 2026-04-23 20:06:01 BST |
| last_updated | 2026-04-23 20:06:01 BST |
| prompt_used | |

# Frontend Runtime Dependency Mini Spec 1

You are the Orchestrator/dependency owner for Allocadabra shared runtime dependencies.

Before starting:

1. Pull latest `main`.
2. Fill in the `prompt_used` timestamp above as the first edit.
3. Review relevant specs and raise any pressing questions, issues, or proposed changes before implementation.
4. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/frontend/ui-design-build.md`
   - `/docs/prompts/agents/frontend-agent.md`
   - `/docs/validation/general-validation.md`

## Requested Owner

- Orchestrator Agent / shared dependency owner

## Target Files

- `/pyproject.toml`
- `/uv.lock`

## Proposed Change

- Add `streamlit` as the frontend runtime dependency in the shared project dependencies.
- Regenerate `uv.lock` after the dependency change is applied.

## Reason

- The Frontend Agent is implementing the V1 application as a single local Streamlit app.
- `plotly` is already available for charting, but `streamlit` is the missing runtime dependency needed to build and run the frontend.
- This keeps the project aligned with the agreed V1 architecture: one local Python application rather than multiple separate services.

## Constraints

- Keep this change narrowly scoped to `streamlit`.
- Do not introduce additional frontend packages in the same step unless the resolver forces a compatibility change that must be documented.
- Do not change app-layer contracts, storage schemas, or frontend specs in this dependency step.

## Validation

- Run `uv lock --check`.
- Run `uv run python -c "import streamlit; print(streamlit.__version__)"`.
- If the dependency graph changes unexpectedly, report the resolver impact before adding further packages.

## Handoff Notes

- Once merged, the Frontend Agent can pull latest `main` and begin implementation against the shared environment.
- Any later frontend dependency additions should come back as separate mini specs because `pyproject.toml` and `uv.lock` are shared cross-agent territory.
