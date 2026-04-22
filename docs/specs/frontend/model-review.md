| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 21:59:59 BST |

# Model Review Spec

## Purpose

Define the component that lets users review model outputs and download copies of generated artifacts.

## Initial Scope

- Present comparable summaries of model outputs.
- Let users explore individual model outputs in more detail.
- Support AI-assisted review and trade-off discussion through Review Mode.
- Let users download generated results and related files.

## Layout

- Display inside the right panel of the Review screen on desktop.
- Sit alongside the Review Mode chat panel.
- V1 mobile is not optimized; the app should show a mobile holding screen.
- Use simple Streamlit-native components where practical; flag if native components create layout or state issues.
- Use Plotly for charts and `.png` export where practical.
- Use vertical dropdown/accordion sections, one for each output type.
- Only one output section should be open at a time in V1.
- The side-by-side metrics table opens by default when entering Review.
- The component takes the full right panel beside chat and should not add a separate internal sidebar.

## Output Sections

Initial sections:

- Side-by-side metrics table.
- Allocation weights.
- Allocation over time.
- Cumulative performance.
- Drawdown.
- Rolling volatility.
- Risk contribution.
- Efficient frontier.
- Dendrogram.
- Modelling plan.

Comparative outputs should show all selected models together.

Single-model outputs should use the selected model from the model selector.

Allocation-over-time should initially show static optimized weights repeated across the 365-day modelling window.

Per-model charts should include a short explanatory tooltip.

Chart data should not be shown as tables under charts in V1; underlying data should be downloadable.

The accepted modelling plan should appear as the last item at the bottom of the review pane.

## Controls

- Top left: `Download All`.
- Top right: selected-model dropdown for outputs that inspect one model at a time.
- Each output dropdown/accordion includes a download button for that artifact.
- The selected-model dropdown affects only per-model sections; comparative sections always show all models.
- Model names should display as full names, not abbreviations.
- Selected model defaults to first model in run order.
- Failed models may appear in the selector in red with failure state.
- `Download All` should return a zip of every generated artifact.
- `Download All` should include accepted modelling plan and user input JSON.
- Per-section downloads should export chart images as `.png` in V1.
- If an artifact is missing, show a disabled download state with a short explanation.

## Default Review State

- Open the side-by-side metrics table first.
- Review Mode AI should provide a short neutral opening comparison in chat only.
- Do not pin the AI overview above the review component.
- The initial selected model should be the first model in run order.
- Ranking should be against the user's stated preferences and should not update dynamically from Review chat in V1.

## Summary Metrics Table

Default side-by-side metrics:

- total return.
- max drawdown.
- Sharpe.
- Calmar.
- Omega.
- Sortino.
- annualized return.
- annualized volatility.
- 30d volatility.
- average drawdown.
- skewness.
- kurtosis.
- CVaR.
- CDaR.

Metric table rules:

- Each metric should include a tooltip with a one-line explanation.
- Tooltip should indicate whether higher or lower values are generally better for the metric.
- Use green/yellow/red ranking across models alongside numeric values.
- Green indicates better relative values and red indicates worse relative values.
- Do not rely on colour alone; numbers must remain visible.
- Benchmark rows are deferred beyond V1.

## AI Context Awareness

The Model Review Component should expose the currently visible model and output type to Review Mode so the AI can receive relevant detailed data for what the user is viewing.

Examples:

- visible model: Hierarchical Risk Parity.
- visible output type: allocation-over-time chart.

Review Mode should not receive unrelated model output details by default.

When the user sends a Review chat message, the frontend should expose:

- visible model, if applicable.
- visible output type.
- visible comparative section, if applicable.
- visible section.
- selected metric row, if applicable.
- open expander IDs.
- chart/table data headers.
- actual visible table/chart data, except that summary metrics can be passed as the summary metrics dataset already prepared for review.

The AI layer then selects detailed context based on both the user message and visible review state.

The user should not see what context was injected into Review Mode.

Review chat cannot trigger UI navigation or control the visible review component in V1.

## State And Reset

- Review does not need to remember the open output section or selected model across reload in V1.
- On reload, default back to summary metrics and the first model in run order.
- Include `Return To Configure` in Review.
- `Return To Configure` should warn that current outputs and Review chat will be replaced.
- `Start New Model` should ask for confirmation before clearing Review state.

## Failure Rules

- If at least one model output exists, the user may enter Review even if another selected model failed.
- Failed models should show in red where they appear in review controls or comparison tables.
- Modelling failures should be handled in the Modelling phase, with retry/fix or return-to-configure options.
- Review Mode should not trigger model rebuilds.
- If a chart cannot render but model outputs exist, allow Review with available tables and other artifacts.
- If a downloadable artifact is missing, show a disabled download button/state with explanation.

## Notes

- This spec depends on the riskfolio-lib, session storage, and review agent specs.
