created: 2026-04-22 22:08:50 BST
last_updated: 2026-04-22 22:08:50 BST

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
