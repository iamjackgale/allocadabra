created: 2026-04-22 21:29:01 BST
last_updated: 2026-04-22 21:59:59 BST

# Modelling Page Spec

## Purpose

Define what the frontend presents while the app prepares datasets, runs models, and builds review outputs.

## Scope

- Covers the Modelling Phase screen only.
- Presents user-facing progress while backend/data and modelling workflows run.
- Bridges the accepted modelling plan and the Review Phase.
- Does not define backend logging internals or `riskfolio-lib` execution details.

## Layout

- Use a full phase screen rather than the Configuration/Review two-panel layout.
- Apply the red accent/backlight defined in `/docs/specs/frontend/ui-design-build.md` throughout the active Modelling Phase.
- Primary content should be centred and focused on progress.
- Show the accepted modelling plan collapsed by default below the progress area.
- The plan display should be Markdown only, with no structured metadata shown.
- Do not offer modelling-plan download from this page; downloads belong in Review.
- Include a clear route back to Configuration at any time.
- Warn that returning to Configuration while modelling is running cancels or interrupts the current run.

## User-Facing Progress

Show plain-English checkpoint updates, not raw technical logs.

Use:

- A progress bar with major checkpoints.
- A transient smooth log line that fades or replaces itself as work progresses.
- Approximate elapsed time.

Do not show percentage completion unless the app can calculate it accurately.

Major progress checkpoints:

1. Validation.
2. Ingestion.
3. Datasets.
4. Modelling.
5. Analysis.
6. Outputs.

Micro-log examples:

- Checking selected assets.
- Confirming model list.
- Loading CoinGecko cache.
- Fetching missing prices.
- Aligning daily price data.
- Building returns dataframe.
- Preparing Mean Variance inputs.
- Running Mean Variance.
- Preparing Risk Parity inputs.
- Running Risk Parity.
- Preparing HRP inputs.
- Running HRP.
- Building side-by-side metrics.
- Preparing allocation charts.
- Preparing drawdown chart.
- Packaging downloads.

Target approximately 30-100 possible micro-log messages across the full process so the screen feels active without resembling a CLI log.

Completed micro-log lines should not stay visible. The current log line should be replaced by the next log line.

Checkpoint text should be concise and suitable for a non-technical user.

## Detailed Logs

- Do not show detailed logs to normal users in the default Modelling page.
- The visible user-facing log should be only a short summary phrase.
- Detailed logs must use the shared logging pattern from `/docs/specs/app/logging.md`.
- Do not expose raw API keys, prompt payloads, or sensitive request data.
- Detailed logs may be available only in developer/debug mode or explicit failure diagnostics.
- User-facing progress logs should not be saved into session/model outputs; they are live display state only.
- Model-specific warnings should be deferred to Review if outputs succeed.

## Loading State

- Use animated dots while work is active.
- The animation should be subtle and must not distract from progress text.
- Progress should not imply precision unless the app knows actual completion percentage.

## User Controls

- User can cancel the modelling run.
- User can return to Configuration while modelling is active.
- User should see a warning not to close or refresh while modelling is active.
- If the user refreshes mid-run, show that the previous run was interrupted and offer return to Configuration or restart.
- Interrupted-run resume is deferred beyond V1.

## Failure State

If modelling fails:

- Stop automatic retries after one failed retry path.
- Explain the failure in plain English.
- Present fix/retry options only when the app can identify a practical next action.
- Let the user return to Configuration with previous configuration, Configuration chat, and modelling plan preserved.

Fixable failures:

- Missing API key.
- CoinGecko timeout.
- Insufficient asset history.
- Invalid constraints.
- Solver failure.

Failure handling rules:

- CoinGecko fetch failures should offer retry without returning to Configuration.
- Insufficient-history assets should not offer an automatic remove-and-retry action in V1.
- Invalid constraints should be caught during validation before entering Modelling; they should not normally appear on this page.
- Solver failure for one model should ask the user whether to continue to Review with partial results.

If at least one selected model succeeds and another fails:

- The app may proceed to Review with failed models marked in red, according to `/docs/specs/frontend/model-review.md`.

If no selected models succeed:

- Stay in Modelling and require retry or return to Configuration.

## Success State

When review artifacts are ready:

- Switch the accent/backlight from red to green.
- Show a `Review Results` button.
- Do not automatically navigate before the user clicks `Review Results`.
- Treat Modelling as complete once model outputs and review artifacts are ready.
- If the user refreshes after Modelling is complete, reopen in Review even if the user had not clicked `Review Results`.
- Wipe Configuration chat immediately when Modelling succeeds and review artifacts are ready.

## Partial Success

- Minimum threshold to enter Review: at least one successful model.
- If only one of multiple selected models succeeds, Review is still allowed.
- Failed model names, IDs, and reasons should be carried into Review automatically.

## Notes

- This spec depends on `/docs/specs/app/logging.md`, `/docs/specs/data-backend/riskfolio-lib.md`, `/docs/specs/data-backend/session-storage.md`, and `/docs/specs/frontend/model-review.md`.
