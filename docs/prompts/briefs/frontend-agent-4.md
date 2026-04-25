| Metadata | Value |
|---|---|
| created | 2026-04-25 BST |
| last_updated | 2026-04-25 BST |
| prompt_used | 2026-04-25 BST |

# Frontend Agent Brief 4

You are the Frontend Agent for Allocadabra.

Before starting:

1. Fill in the `prompt_used` timestamp above as the first edit.
2. Pull latest `main` into your branch at `/Users/iamjackgale/.codex/worktrees/8fe0/allocadabra`.
3. Read:
   - `/docs/plan.md`
   - `/docs/tasks.md`
   - `/docs/specs/app/frontend-backend-modelling-integration.md` (especially the Orchestrator Integration Review section)
   - `/docs/specs/app/ai-live-integration.md`
   - `/docs/specs/frontend/agent-chat.md`
   - `/docs/specs/frontend/model-review.md`
   - `/docs/validation/frontend-validation.md`
   - `/docs/validation/general-validation.md`
4. Run the standard validation checks from `docs/validation/general-validation.md` to confirm the baseline passes before making any changes.

## Context: What Brief 3 Already Covered

Brief 3 completed the following deterministic checks — do not repeat them:

- Missing-key Configuration path (`?alloca_dev_no_ai_env=1`): user message rendered, recoverable error shown, no traceback, retry available.
- Three-consecutive-failure disable path: chat disabled after third failure, no traceback.
- Review fixture + missing-key path (`?alloca_dev_review_fixture=brief3&alloca_dev_no_ai_env=1`): Review opened with correct `Ranked for` heading, no exposed context payload strings.
- Review missing-key chat path: recoverable error displayed, no context payload names visible.

Both `COINGECKO_API_KEY` and `PERPLEXITY_API_KEY` are now set in the `8fe0` worktree `.env`. Full live paths are unblocked.

## Tasks In This Brief

| Task | Description |
|---|---|
| `130` | Replace deprecated `use_container_width` usage with current API equivalents. |
| `112` | Complete live AI chat UI verification in Configuration and Review. |
| `113` | Complete live Review context verification with a real modelling run. |
| `105` | Run full end-to-end smoke test (happy path, failures, exports). Also satisfies `119`. |

Complete `130` first — it is a code change with no live run dependency. Then run `112`, `113`, and `105` together with the app running.

---

## Task 130 — Fix Deprecated `use_container_width` Usage

Streamlit 1.56.0 emits runtime warnings for deprecated `use_container_width` usage on certain components. Remove these warnings before demo prep.

**Step 1 — identify usages:**

```bash
grep -rn "use_container_width" frontend/
```

**Step 2 — check which are deprecated.** Start the app and read the terminal output carefully:

```bash
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Note every `DeprecationWarning` or `StreamlitAPIWarning` line that mentions `use_container_width`. Check the Streamlit 1.56.0 changelog or API docs for the correct replacement for each affected component.

Common replacements to check against:

- `st.plotly_chart(fig, use_container_width=True)` — check if `use_container_width` is still valid in 1.56.0 or replaced by a different width argument.
- `st.dataframe(df, use_container_width=True)` — same check.
- `st.button(...)` / `st.download_button(...)` with `use_container_width=True` — in some versions deprecated in favour of `width="stretch"` or no parameter at all.

**Step 3 — apply fixes.** Update only the usages that produce actual runtime warnings. Leave unchanged any `use_container_width` usage that does not produce a warning in 1.56.0.

**Step 4 — verify:**

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app
uv run streamlit run frontend/app.py --server.headless true --server.port 8501
```

Confirm the deprecation warnings are gone from terminal output. Confirm no visual regressions in Configuration, Modelling, and Review layouts.

### Acceptance Criteria

- No `use_container_width` deprecation or API warnings in the `uv run streamlit run` terminal output.
- All page layouts render correctly.
- Compile check passes.

### Update `docs/validation/frontend-validation.md`

Add a short note under a new "Task 130 — Deprecated API Fixes" section: which usages were found, which were deprecated, and what replacement was applied.

---

## Task 112 — Live AI Chat UI Verification

Brief 3 confirmed the deterministic missing-key and retry paths. Now verify with live Perplexity credentials.

**Configuration Mode live checks:**

1. Start the app at `http://localhost:8501` (no dev flags).
2. Add 2–3 assets, set objective and risk appetite.
3. Send a Configuration Mode chat message, e.g. `What portfolio model should I choose for a medium risk appetite?`
4. Verify:
   - User message renders immediately after send.
   - A loading state is visible while the Perplexity request is pending.
   - The assistant response appears without a traceback and uses the safe educational tone.
   - Chat history persists for the session.
5. Send a follow-up question and confirm context is maintained across turns.
6. Ask for financial advice (e.g. `Should I put all my treasury in Bitcoin?`) and confirm the fixed financial-advice refusal message is displayed rather than a raw AI response or error.

**Review Mode live checks:**

Use the synthetic Review fixture with live AI to avoid requiring a full modelling run:

```text
http://localhost:8501/?alloca_dev_review_fixture=1
```

1. Open the fixture URL. Confirm Review opens with synthetic outputs.
2. Send a Review Mode chat message, e.g. `Compare the two models in terms of drawdown`.
3. Verify:
   - User message renders immediately.
   - Loading state is visible while waiting.
   - The response refers to visible output data naturally (no internal metadata strings).
   - Configuration and Review chat histories are separate — switch between fixture and standard app to confirm.

If you also complete a full live run in task 105, repeat the Review chat check with a real run's outputs and note the difference in the validation doc.

### Acceptance Criteria

- Live Configuration Mode: loading state visible, response rendered, no traceback.
- Financial advice prompt: fixed refusal text displayed, not a raw error.
- Live Review Mode: response references visible output, no context payload strings in the UI or response.
- Chat histories are independent between Configuration and Review.

### Update `docs/validation/frontend-validation.md`

Add a "Task 112 — Live AI Chat Verification" section with observations for each check above.

---

## Task 113 — Live Review Context Verification

Brief 3 confirmed no context payload strings are exposed using the synthetic fixture with missing key. Now verify with live AI that the correct visible context is actually being passed into Review Mode.

**Using the synthetic fixture with live AI:**

1. Open `http://localhost:8501/?alloca_dev_review_fixture=1`.
2. Switch to the Allocation Weights section, select Risk Parity.
3. Send `What percentage is Bitcoin allocated in this model?`
4. Verify the response references the actual synthetic allocation weight value (not a generic answer).
5. Switch to Summary Metrics. Send `Which model has the lower max drawdown?`
6. Verify the response identifies the correct model using actual metric values.

**If a full live run is completed in task 105:**

Repeat the same checks using the real modelling run outputs and note whether the context passed matches what is visible in the Review pane. Confirm the same checks pass with real data.

**Context leakage checks:**

After any Review AI response, confirm the following strings do not appear anywhere in the visible Review UI or in the chat response text:

- `visible_context`
- `detailed_context`
- `chart_table_headers`
- `visible_table_data`
- `open_expander_ids`

### Acceptance Criteria

- Review Mode AI response references actual visible data from the selected section and model.
- Responses are specific, not generic — the answer to a metric question should cite the actual value.
- No context payload or internal label strings are visible to the user anywhere in the Review UI.
- Context passes correctly for both comparative (multi-model) and per-model sections.

### Update `docs/validation/frontend-validation.md`

Add a "Task 113 — Live Review Context Verification" section noting which paths were tested (synthetic fixture only, or synthetic + live run) and the result of each check.

---

## Task 105 — Full End-to-End Smoke Test

Run a complete live smoke test. Both API keys are set in the `8fe0` worktree `.env`. A successful full live run also satisfies task `119`.

If either credential is missing at runtime, stop and report the exact missing variable before running live paths.

### Path 1 — Happy Path (also satisfies task `119`)

1. Start the app at `http://localhost:8501`.
2. Load the CoinGecko token list — confirm assets appear in search.
3. Select 2–3 assets (e.g. BTC, ETH).
4. Set objective, risk appetite, and at least two models.
5. Send a Configuration Mode message and confirm live Perplexity response.
6. Click `Generate Plan`. Confirm deterministic validation passes, then a Perplexity modelling plan is generated and displayed.
7. Click `Run`. Enter the Modelling screen.
8. Observe all six progress checkpoints: Validation → Ingestion → Datasets → Modelling → Analysis → Outputs.
9. Confirm `Review Results` appears when outputs are ready and accent changes to green.
10. Enter Review. Confirm the summary metrics table is populated with real model outputs.
11. Select a per-model section. Confirm the model dropdown works and content changes on selection.
12. Send a Review Mode chat message and confirm a live response that references visible data.
13. Download one individual artifact. Confirm a file is received and is readable.
14. Click `Download All`. Confirm a zip is received and opens with the expected artifact files, confirmed modelling plan, and user input JSON.
15. Click `Return To Configure`. Confirm outputs are cleared after the confirmation dialog.

### Path 2 — Deterministic Validation Failure

1. Select only one asset.
2. Click `Generate Plan`.
3. Confirm validation failure surfaces in the Configuration chat area without calling Perplexity and without a traceback.

### Path 3 — Cancel Modelling Run

1. Start a new modelling run.
2. Click `Cancel` while modelling is active.
3. Confirm the cancellation confirmation copy appears.
4. Confirm the Configuration screen reopens with previous asset and parameter selections intact.

### Path 4 — Missing Artifact Download State

If any model produces a missing artifact in the run, confirm:

- The relevant download control is disabled.
- The `This artifact was not generated for this run.` tooltip or label appears.

If no missing artifacts appear naturally, note this in the validation doc — do not force the condition.

### Path 5 — Start New Model

1. From Review, click `Start New Model`.
2. Confirm the required confirmation copy appears.
3. Confirm the Configuration screen opens clean with no previous selections or outputs.

### Acceptance Criteria

- Happy path completes end-to-end with no tracebacks or unhandled exceptions.
- Deterministic validation failure surfaces in chat, not as an uncaught error.
- Cancel returns to Configuration with previous selections intact.
- `Download All` produces a valid zip.
- Task `119` can be marked complete when the happy path succeeds with live credentials.

### Update `docs/validation/frontend-validation.md`

Add a "Task 105 / 119 — Full Live End-to-End Smoke" section documenting:

- each path tested and its result;
- any paths not tested and why;
- mini specs for any gaps found in other agents' code.

---

## Boundaries

Own:

- `/frontend/**`

Do not edit:

- `/app/**` — owned by Backend/Data, Modelling, and AI agents.
- `/docs/tasks.md` — owned by the Orchestrator.
- `pyproject.toml` / `uv.lock` — shared; do not change without a mini spec.

If a live run reveals a callable gap in another agent's folder, return a mini spec with:

- target files or folders
- requested owner agent
- reproduction path (exact URL or script)
- observed behaviour
- expected behaviour
- risk or dependency notes

---

## Standard Validation

Run before starting and again after completing task `130`:

```bash
PYTHONPYCACHEPREFIX=/tmp/allocadabra-pycache-main python3 -m compileall frontend app
uv lock --check
rg -n '(<{7}|={7}|>{7})' .
```

---

## Reporting Back

When complete, report:

- tasks completed (`130`, `112`, `113`, `105`, `119`);
- files changed;
- validation commands and outcomes;
- URLs tested and key observations for each smoke path;
- any mini specs for other owner agents;
- whether task `119` is marked complete or still blocked.
