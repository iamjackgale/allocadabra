| Metadata | Value |
|---|---|
| created | 2026-04-22 22:08:50 BST |
| last_updated | 2026-04-22 23:09:50 BST |

# Design Review 1 Spec

## Purpose

Define the first Product/UX review before deployment of the first code-producing agent.

This review exists to ensure the current Allocadabra design is workable, coherent, and sensible from a product/UX perspective before implementation begins.

## Review Timing

- This review should happen before the first agent begins writing production code.
- The review should focus on whether the planned customer journey is clear enough to build.
- The review should raise questions and improvements, not produce implementation code.

## Reviewer

Product/UX Agent.

## Required Reading

The Product/UX Agent must review all available `/docs` content before starting the design review, including:

- `/docs/plan.md`
- `/docs/tasks.md`
- all specs under `/docs/specs`
- all agent prompts under `/docs/prompts/agents`

## Review Focus

The Product/UX Agent should get comfortable with the full customer journey:

1. Starting a new modelling workflow.
2. Selecting assets and preferences.
3. Using Configuration Mode chat.
4. Generating and confirming a modelling plan.
5. Waiting through the Modelling Phase.
6. Recovering from modelling failure or partial success.
7. Reviewing comparable model outputs.
8. Asking Review Mode questions.
9. Downloading outputs.
10. Starting a new model.

## Expected Output

The Product/UX Agent should produce exactly 10 high-priority questions.

Each question should:

- identify the UX component or journey step it relates to.
- explain why the question matters before implementation.
- be framed so the Orchestrator/user can answer it directly.
- focus on decisions that could materially improve or unblock the V1 build.

The questions should prioritize:

- confusing or overloaded user flows.
- missing copy or explanation.
- awkward state transitions.
- likely Streamlit UI limitations.
- unclear user expectations during AI or modelling waits.
- download/export clarity.
- educational/no-advice framing.
- visual hierarchy and phase signalling.

## Non-Goals

- Do not write production code.
- Do not rewrite all specs.
- Do not create final visual designs.
- Do not add new product scope unless framed as a question or proposed concern.
- Do not produce more than 10 questions in the primary output.

## Follow-Up

After the 10 questions are answered, the Orchestrator Agent should update relevant specs, prompts, and tasks before code-producing agents begin implementation.

## Design Review 1 Output

Reviewed source of truth:

- `/docs/plan.md`
- `/docs/tasks.md`
- all specs under `/docs/specs`
- all agent prompts under `/docs/prompts/agents`

Primary assessment:

The planned three-phase journey is coherent enough to build from, but several decisions should be answered or explicitly accepted before code-producing agents begin. The highest-risk areas are expectation-setting around the AI chat, destructive state transitions, partial model success, and Review/export clarity.

## 10 High-Priority UX Questions

1. **Configuration readiness:** Should `Generate Plan` remain disabled until the minimum required fields are complete, or should it stay enabled and route all missing-field feedback through Configuration Mode chat?

   Why it matters: the specs say validation should preferably surface through chat, but the form also has required fields and invalid controls. Frontend, AI, and QA need one clear pattern so students understand whether the form, the agent, or both are guiding completion.

   Answer summary: `Generate Plan` should remain disabled until all required fields are complete. Validation should primarily be deterministic in the app, with chat acting only as a secondary guidance layer rather than completing or validating the setup for the user.

2. **AI chat expectations:** What visible affordance should explain that Configuration Mode chat can suggest changes but cannot directly update selected assets, objective, risk appetite, models, or constraints?

   Why it matters: students may expect the AI panel to act like an assistant that changes the setup for them. Without explicit expectation-setting, suggestions such as "use Risk Parity" can feel broken if the form does not update.

   Answer summary: Configuration Mode should set expectations in the assistant's first response after the user's first chat input. The response should briefly explain that the agent can advise, suggest, and steer, but cannot directly control or change the configuration fields.

3. **Modelling plan confirmation:** Which exact actions should appear on the generated plan screen, and how should the screen communicate that changing configuration abandons the current plan?

   Why it matters: the generated plan screen needs one confirmation model before implementation so the handoff from AI-generated text to executable metadata feels deliberate and non-editable.

   Answer summary: No compact locked-plan state is needed. After a plan is generated, the only three actions should be `Run`, `Regenerate`, and `Reconfigure`. `Run` begins validation and modelling to move past Configuration Phase. `Regenerate` generates another plan while staying in the same core workflow. `Reconfigure` abandons the current plan and returns to the configuration screen with previous items still selected after confirmation.

4. **Educational/no-advice framing:** Is the persistent footer enough, or should the modelling plan preview and first Review message also include a short no-advice/no-warranty line?

   Why it matters: the highest-risk moments are where the app recommends a model fit or explains apparent performance. The product needs guardrail placement that is visible without making the interface feel like a legal disclaimer wall.

   Answer summary: The persistent footer is enough for general visible UI framing, and the product should keep disclaimers minimal. As a secondary guard, the prompt injection for the Review Agent's initial model comparison should include that the comparison is not financial advice and no warranty is given as to the accuracy of the information.

5. **Phase signalling:** How should the Modelling Phase red accent be labelled or paired with copy so it reads as "app is processing" rather than "something is wrong"?

   Why it matters: red commonly signals error. Since Modelling uses red even during normal operation, Frontend needs copy and status hierarchy that distinguish active processing, warnings, cancellation, interrupted runs, and actual failures.

   Answer summary: Use a restrained phase header alongside the colour shift. Configuration and Review should show `CONFIGURATION` or `REVIEW` as the header of the right-hand workflow pane. Modelling should show `MODELLING` centred in the full Modelling screen because that phase does not use the left/right layout. The header should be subtle and non-obnoxious.

6. **Cancel and return behaviour:** Are `Cancel` and `Return To Configure` separate Modelling controls, and what exact state should each leave behind for inputs, Configuration chat, the generated plan, partial outputs, and cached market data?

   Why it matters: the specs allow cancelling or returning while modelling is active, but the persistence rules need an unambiguous user promise. This affects session storage, progress handling, warning copy, and QA recovery tests.

   Answer summary: They should not be separate controls during Modelling. Use a single `Cancel` action. `Cancel` returns to the Configuration screen with the two-pane layout and editable configuration component, with the previous configuration options still selected. It should not return to the modelling plan preview. Cached market data is unaffected, and all partial outputs are deleted.

7. **Partial model success:** If one selected model fails but at least one succeeds, should the app automatically allow Review, ask the user whether to continue to Review, or require retry first?

   Why it matters: the plan and frontend/modelling specs allow Review with partial success, while the AI/Perplexity prompt currently says the app should remain in Modelling if a selected model fails. This must be reconciled before implementation to avoid conflicting agent behaviour.

   Answer summary: For V1, if at least one selected model succeeds, move straight to Review with failed models marked. Do not pause for failed-model retries because this risks long delays and keeps users from the Review process. Add failed-model retry before Review as a possible V2 improvement.

8. **Review hierarchy:** Because the opening comparison appears in chat only, what non-chat cue should tell users that the side-by-side metrics table is the primary comparison surface and that any "best fit" ranking is preference-relative, not generally best?

   Why it matters: students may focus on the right-hand Review panel and miss the chat opening summary, or overread green/red rankings as investment recommendations. The Review screen needs a clear hierarchy without duplicating the AI explanation in a second summary block.

   Answer summary: Add concise non-chat cues in the Review pane above the default comparison: `Compare model outputs against your selected objective and risk appetite. Green/yellow/red rankings compare these models within this run only.` Also show a dynamic context line such as `Ranked for: Reduce drawdowns · Medium risk appetite`, using the user's selected objective and risk appetite.

9. **Download clarity:** What exact labels, disabled states, and bundle contents should users see for `Download All` and per-section downloads when chart images, tables, modelling plan, user input JSON, or failed-model artifacts are unavailable?

   Why it matters: exports are part of the course workflow, and missing artifacts are explicitly allowed. Frontend, Backend/Data, Modelling, and QA need a shared user-facing contract for what can be downloaded, what is included, and why something is disabled.

   Answer summary: No firm UX answer yet. This needs a dedicated download/export layer spec first, including the full list of generated outputs, expected files for each output such as table `.csv`, chart `.png`, user input `.json`, and modelling plan `.md`, plus bundle contents and unavailable-artifact states. Added Task 057 for the Orchestrator Agent to prepare that spec and assign follow-up implementation ownership.

10. **Reset, reload, and destructive navigation:** What confirmation copy and recovery state should apply for `Reset Configuration`, `Return To Configure` from Review, `Start New Model`, browser refresh during Modelling, and reload after Review artifacts are ready?

    Why it matters: Allocadabra supports one active workflow and no recoverable history beyond downloads. These are the moments where students can accidentally lose work, so the product needs a precise state-transition matrix before implementation.

    Answer summary: Use the following state-transition matrix. Confirmation copy should be declarative rather than starting with a question, and user-facing copy should not mention CoinGecko market-data cache.

    | Step | Needs Confirmation? | Confirmation Or State Copy | Recovery State |
    |---|---|---|---|
    | `Reset Configuration` during Configuration form | Yes | `This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.` | Return to empty/default Configuration form. Clear generated plan if any, Configuration chat, Review chat, and model outputs. |
    | `Reconfigure` from generated plan | Yes | `This abandons the current plan and returns to Configuration with your previous selections still filled in.` | Return to editable Configuration form with previous selected assets, preferences, models, and constraints preserved. Clear generated plan. Keep Configuration chat. |
    | `Cancel` during Modelling | Yes | `This abandons the current modelling run, deletes partial outputs, and returns to Configuration with your previous options selected.` | Return to editable Configuration form with previous options selected. Clear generated plan and partial outputs. Preserve Configuration chat. |
    | Browser refresh during active Modelling | No pre-refresh confirmation; show recovery state after reload | `The previous modelling run was interrupted. You can return to Configuration with your previous options selected, or restart the run.` | Show interrupted Modelling state. Offer `Return To Configuration` and `Restart Run`. No partial outputs retained. Keep previous options, Configuration chat, and generated plan if needed for restart. |
    | All models fail in Modelling | No destructive confirmation | `No models completed successfully. You can retry the run or cancel back to Configuration.` | Stay in Modelling failure state. Offer `Retry` and `Cancel`. Preserve previous options and Configuration chat. Keep generated plan for retry while still in Modelling. Clear partial outputs. |
    | Partial model success | No | No confirmation. Proceed to Review. | Enter Review automatically with successful outputs available and failed models marked with reasons. |
    | Reload after Review artifacts are ready | No | No confirmation. | Reopen in Review. Default to summary metrics and first model in run order. Review chat persists if already started; Configuration chat has already been wiped. |
    | `Return To Configure` from Review | Yes | `This returns to Configuration and clears the current outputs and Review chat. Download results first if you want to keep them.` | Return to editable Configuration form with prior configuration options selected. Clear Review chat and current model outputs once the user confirms. |
    | `Start New Model` from Review | Yes | `This clears the current configuration, outputs, and Review chat. Download results first if you want to keep them.` | Return to empty/default Configuration form. Clear active inputs, generated plan, Review chat, and model outputs. |
    | Missing artifact download click | No; disabled state | `This artifact was not generated for this run.` | Remain in Review. No state change. |
    | Per-section available download click | No | No confirmation. | Download only that artifact. No state change. |
    | `Download All` click | No | No confirmation. | Download bundle. No state change. |
