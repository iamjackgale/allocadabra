| Metadata | Value |
|---|---|
| created | 2026-04-25 |
| last_updated | 2026-04-25 |
| prompt_used | 2026-04-25 09:00:00 BST |

# Orchestrator Agent Prompt 2 — Re-initialisation and Merge

## Prompt Use Instruction

When an agent starts work from this prompt:

1. Fill in `prompt_used` above with the current timestamp.
2. Read `docs/tasks.md` in full before taking any other action.
3. Do not write production code. All edits are to `/docs` and git operations only.

## Context

This is a re-initialisation prompt for the Orchestrator Agent. Significant work has been completed across all agent branches since the last orchestrator session. All agents have been working in isolated git worktrees and their changes are not yet merged into `main`. Your task is to bring everything together, resolve any conflicts, and then produce a structured next-actions plan.

The base identity, rules, and responsibilities from `docs/prompts/agents/orchestrator-agent.md` still apply. This prompt adds a specific initial task sequence.

## Worktree and Branch Map

All worktrees are rooted under `/Users/iamjackgale/.codex/worktrees/`. Run `git worktree list` from the main repo at `/Users/iamjackgale/Developer/Python/allocadabra` to confirm paths. The known layout at the time this prompt was written:

| Worktree path | Branch |
|---|---|
| `/Users/iamjackgale/Developer/Python/allocadabra` | `main` |
| `/Users/iamjackgale/.codex/worktrees/e446/allocadabra` | `codex/orchestrator` |
| `/Users/iamjackgale/.codex/worktrees/c0c4/allocadabra` | `codex/backend-data-agent` |
| `/Users/iamjackgale/.codex/worktrees/8fe0/allocadabra` | `codex/frontend-agent` |
| `/Users/iamjackgale/.codex/worktrees/a8a0/allocadabra` | `codex/ai-perplexity-integration` |
| `/Users/iamjackgale/.codex/worktrees/379a/allocadabra` | `codex/modelling-agent-setup` |
| `/Users/iamjackgale/.codex/worktrees/341a/allocadabra` | `codex/ux` |

## What Has Been Completed Since the Last Orchestrator Session

Use this section to understand recent agent work. Cross-check against `docs/tasks.md` before deciding on task status changes.

### Backend/Data Agent (Brief 4)

- Completed end-to-end integration verification between Modelling outputs and Backend export bundle preparation (task `103`).
- Confirmed no Backend/Data adapter gap exists (task `083`).
- Task `064` is BLOCKED: the 2-day CoinGecko price-cache freshness tolerance cannot be validated until `COINGECKO_API_KEY` is available.
- Added `scripts/backend_modelling_handoff_smoke.py` covering: `run_active_modelling(...)`, `prepare_review_export_bundle(...)`, artifact paths, missing placeholders, failed-model reasons, export readiness, and 2-day cache boundary logic.
- Updated `docs/validation/backend-validation.md` with Brief 4 validation results.

### Frontend Agent (Brief 3)

- Implemented spinner-backed AI request loading state in `frontend/chat.py`.
- Implemented disabling of chat input and retry after 3 consecutive failures.
- Exposed chat failure count in `frontend/runtime.py`.
- Updated `docs/validation/frontend-validation.md` with Brief 3 results.
- Tasks `112` and `113` are partially verified: deterministic missing-key, retry, and failure-disable paths confirmed; synthetic Review fixture confirmed non-exposure of context payload names. Full live verification of tasks `112`, `113`, `105`, and `119` remains blocked until `COINGECKO_API_KEY` and `PERPLEXITY_API_KEY` are available.

### AI/Perplexity Agent (Brief 3)

- Ran live verification of CM-1 through CM-4 (Configuration Mode), RM-1 through RM-3 (Review Mode), and GR-1 through GR-4 (Guardrails) through the Streamlit UI and synthetic Review fixture.
- Fixed the AI layer based on observed failures. Key changes in `app/ai/data_api.py`, `app/ai/prompts.py`, and `app/ai/validation.py`:
  - Deterministic Configuration readiness replies.
  - Deterministic intercepts for financial-advice, direct model-choice, live-data, and unsupported-model requests.
  - Stricter one-paragraph default prompt behavior.
  - Tighter Configuration prompt rules around exact supported labels and defaults-only constraints.
  - Tighter Review prompt rules around no direct recommendation language.
  - Review metric-name normalization for metadata.
- Updated `docs/specs/ai/ai-model-integration.md` and `docs/validation/ai-validation.md`.
- **Tasks `107`, `108`, `109`, `110`, `111`, and `114` are complete.** The AI agent has reported these as done; `docs/tasks.md` has not yet been updated to reflect this.
- Task `115` (Orchestrator review of live AI behaviour) is now unblocked.

### Modelling Agent (Brief 2 tasks 069–070)

- Hardened `summary-metrics.csv`: non-computable metrics now leave cells blank rather than `NaN`.
- Added companion artifact `summary-metric-unavailable-reasons.csv` with stable columns: `model_id`, `metric`, `reason_code`, `message`.
- Added repeatable smoke script at `scripts/modelling_smoke.py`.
- Updated `docs/validation/modelling-validation.md`.

### UX/Product Agent

No new brief reported since the last orchestrator session. Check `codex/ux` for any uncommitted work before merging.

## Initial Task: Merge All Agent Work Into Main

Work through the following steps in order. Do not skip steps.

### Step 1 — Audit each worktree

For each agent worktree, run `git status` and `git log --oneline main..HEAD` to determine:

- Whether there are uncommitted changes.
- Whether there are commits ahead of `main`.

Record what you find for each branch before touching anything.

### Step 2 — Commit uncommitted agent work

For any worktree that has uncommitted changes, commit those changes using a descriptive commit message that names the brief or task completed. Stage only files relevant to that agent's scope.

Do not commit files outside the agent's owned scope without a mini spec. Refer to `docs/plan.md` for folder ownership rules.

Do not skip the pre-commit hook scan for conflict markers. Run:

```bash
rg -n '(<{7}|={7}|>{7})' .
```

before each commit and confirm zero matches.

### Step 3 — Merge into main

Merge each agent branch into `main` from the main worktree at `/Users/iamjackgale/Developer/Python/allocadabra`. Use a merge commit (not rebase) for each. Suggested merge order to minimise conflicts:

1. `codex/modelling-agent-setup` — foundational artifact/smoke changes, no UI surface.
2. `codex/backend-data-agent` — smoke scripts and validation docs only, no production code changes.
3. `codex/ai-perplexity-integration` — `app/ai/` layer changes; merges before Frontend reduces conflict surface.
4. `codex/frontend-agent` — `frontend/` changes that depend on the AI and Backend layers.
5. `codex/ux` — docs/specs changes; merge last since they are least likely to conflict.

For each merge:
- Run `git merge --no-ff <branch> -m "Merge <branch>: <one-line summary>"`.
- If there are conflicts, resolve them conservatively: prefer `main` for docs, prefer the agent branch for its owned implementation files.
- After resolving, run `python3 -m compileall app frontend scripts` and `uv lock --check` to verify the tree is clean.
- Run the conflict-marker scan again after resolution.

### Step 4 — Validate main

After all merges, run the repo-level validation checks defined in `docs/validation/general-validation.md`. At minimum:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall app frontend scripts
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
uv run python scripts/backend_smoke.py
uv run python scripts/backend_modelling_handoff_smoke.py
uv run python scripts/modelling_smoke.py
```

Report any failures before pushing.

### Step 5 — Push main to remote

```bash
git push origin main
```

Confirm the push succeeds before proceeding.

### Step 6 — Pull main into all agent worktrees

For each agent worktree (excluding the orchestrator worktree itself), run:

```bash
git -C <worktree-path> pull origin main
```

Or, if the worktree branch has its own remote tracking, switch to the worktree and run `git merge main`. Confirm each worktree is up to date with `git log --oneline HEAD..main`.

## Second Task: Update the Task List

After the merge is complete, open `docs/tasks.md` and make the following updates:

1. Mark tasks `107`, `108`, `109`, `110`, `111`, and `114` as `DONE` with today's date. These were completed by the AI Agent in Brief 3.
2. Confirm tasks `103` and `083` are already marked `DONE` (they should be from the Backend agent's recent update).
3. Review tasks `112` and `113` — these are partially verified. Add a note in the task description if supported by the format, or leave as `TODO` with a known-partial status until the API keys are available.
4. Mark task `115` as `IN_PROGRESS` (now that `114` is done, the Orchestrator should review).
5. Update `last_updated` in the metadata table.

Do not change any other task statuses without evidence from the agent reports above or from reading the validation docs.

## Third Task: Proposed Next Actions Report

Once the merge and task update are complete, return a structured next-actions report. The report must:

- Be divided by agent.
- Within each agent section, list tasks in the order they should be worked, most important and least-blocked first.
- Flag blocking dependencies clearly (e.g. "blocked until `COINGECKO_API_KEY` is configured").
- Include task IDs from `docs/tasks.md`.
- Propose any new tasks that appear necessary based on the gap list from the AI agent Brief 3 report and the partial-verification state of Frontend tasks `112`, `113`, `105`, and `119`.

The report is your deliverable to the user. Keep it concise and actionable.

## Output Format

- Structured and minimal.
- Prioritise clarity and execution over explanation.
- Use the task IDs from `docs/tasks.md` throughout.
- If you discover conflicts or unexpected state during the merge, stop and report to the user before continuing.
