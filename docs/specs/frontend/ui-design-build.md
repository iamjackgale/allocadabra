| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 23:09:50 BST |

# UI Design/Build Spec

## Purpose

Define the overall user interface for Allocadabra.

## Runtime

- Use Streamlit for V1 as a single local Python web app.
- The user should be able to run one local app from the repo, not separate frontend/backend processes.
- Keep the app on one base URL with phase-screen changes, not multi-page navigation.

## Workflow Screens

The UI has three phase screens:

1. Configuration.
2. Modelling.
3. Review.

Configuration and Review should share a similar two-panel structure, but they are separate phases with different components and data context.

## Configuration Screen

- Desktop layout: AI chat panel on the left, model configuration component on the right.
- Mobile layout: do not optimize for V1; show a holding screen stating that the app has not yet been optimized for mobile.
- The right-hand workflow pane should have a restrained phase header: `CONFIGURATION`.
- Users select assets, set objective, set risk appetite, optional constraints, and generate/confirm the modelling plan.
- Modelling plan confirmation appears as a readable Markdown preview with:
  - `Run`: begin validation and modelling to move past Configuration Phase.
  - `Regenerate`: generate another plan while staying in the same core workflow.
  - `Reconfigure`: abandon the current plan and return to the configuration screen with previous items still selected.
- `Reconfigure` requires confirmation copy: `This abandons the current plan and returns to Configuration with your previous selections still filled in.`

## Modelling Screen

- Full phase screen focused on progress, status, and errors.
- Show a restrained centred phase header: `MODELLING`.
- Top/centre primary element: plain-English checkpoint log.
- Checkpoint log examples:
  - validating inputs.
  - fetching price data.
  - building dataframe.
  - transforming data.
  - running each selected model.
  - preparing charts.
  - preparing tables.
  - preparing review.
- Beneath progress, show a smaller copy of the agreed modelling plan.
- Visible logs should be summarized user-facing checkpoints.
- Detailed technical logs should be hidden or expandable.
- Include minor loading animation so the screen feels active during model execution.

## Review Screen

- Desktop layout: AI chat panel on the left, model review component on the right.
- The right-hand workflow pane should have a restrained phase header: `REVIEW`.
- Beneath the `REVIEW` phase header, show concise comparison cues:
  - `Compare model outputs against your selected objective and risk appetite. Green/yellow/red rankings compare these models within this run only.`
  - `Ranked for: [Treasury objective] · [Risk appetite]`
- Model review component uses vertical dropdown/accordion sections for output types.
- The side-by-side metrics table is open by default.
- Allocation weights and deeper charts appear below as additional dropdown/accordion sections.
- Comparative outputs should show all selected models together.
- Per-model outputs should use a model selector in the top right of the review component.
- Top left of the review component should include `Download All`.
- Each output dropdown/accordion should include its own download button.

## Navigation

- Configuration can progress to Modelling only from the generated plan screen through `Run`.
- Modelling can progress to Review only after all selected models and required outputs are available.
- Review can return to Configuration only after confirmation that current outputs and Review chat will be cleared.
- Failed or cancelled Modelling returns to the editable Configuration component with previous configuration options selected and previous Configuration chat logs preserved; it does not return to the generated modelling plan.
- Configuration does not need a back navigation to Modelling.
- Starting a new model clears prior Review state according to the session storage spec.

## Confirmation And Recovery Copy

Confirmation copy should be declarative and should not start with a question.

| User Action Or State | Confirmation Or State Copy |
|---|---|
| `Reset Configuration` | `This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.` |
| `Reconfigure` | `This abandons the current plan and returns to Configuration with your previous selections still filled in.` |
| `Cancel` during Modelling | `This abandons the current modelling run, deletes partial outputs, and returns to Configuration with your previous options selected.` |
| Interrupted run after refresh | `The previous modelling run was interrupted. You can return to Configuration with your previous options selected, or restart the run.` |
| All models fail | `No models completed successfully. You can retry the run or cancel back to Configuration.` |
| `Return To Configure` from Review | `This returns to Configuration and clears the current outputs and Review chat. Download results first if you want to keep them.` |
| `Start New Model` | `This clears the current configuration, outputs, and Review chat. Download results first if you want to keep them.` |
| Missing artifact disabled state | `This artifact was not generated for this run.` |

## Visual Direction

- Academic, clean dashboard.
- Avoid crypto cliché, command-centre styling, playful styling, and institutional styling.
- Use rounded edges, transparent or lightly translucent components, and minor accent colours.
- Support light and dark mode.
- Avoid relying on colour alone to communicate metric quality.
- Do not add hackathon or sponsor branding to the frontend.

## Phase Accent State

- Configuration Mode and Review Mode should use a green accent/backlight because these are user-led interaction phases.
- Modelling Mode should use a red accent/backlight because this is the app-led processing phase.
- Pair the colour shift with a visible phase header so colour is not the only phase signal.
- Keep phase headers quiet and non-obnoxious; they should label the current workflow area, not dominate the screen.
- In Configuration and Review, place the phase header in the right-hand workflow pane.
- In Modelling, place the phase header in the middle of the full-screen Modelling layout.
- The accent should feel like ambient backlighting or a subtle phase indicator, not a dominant colour palette.
- The UI must not rely on the green/red accent alone to communicate state; phase labels, progress text, and controls must remain explicit.
- Keep both accents compatible with light and dark mode.

## Footer

Persistent concise footer:

`Experimental project produced for educational purposes only. No warranty as to correctness. Licence: MIT`

Also include `© 2026 Jack Harry Gale`, with `Jack Harry Gale` linking to `https://jackgale.uk`.

## Button Copy

- `Generate Plan`
- `Run`
- `Regenerate`
- `Reconfigure`
- `Return To Configure`
- `Review Results`
- `Start New Model`

## Copy Rules

- Use `model` for configuration and course clarity.
- Use `portfolio` for model outputs.
- Keep copy minimal and product-facing.
- Do not add unnecessary course/tutorial framing to the app.

## Notes

- This spec depends on the model parameters, agent chat, and model review specs.
