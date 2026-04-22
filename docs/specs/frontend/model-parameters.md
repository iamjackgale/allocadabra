| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 23:09:50 BST |

# Model Parameters Spec

## Purpose

Define the component that lets users set and adjust parameters during the modelling preparation phase.

## Initial Scope

- Let users select assets from CoinGecko-backed options.
- Let users specify preferences for the modelling process.
- Support AI-assisted parameter setting through Configuration Mode.
- Prepare user inputs for the AI-generated model plan.

## Layout

- Display inside the right panel of the Configuration screen on desktop.
- Sit alongside the Configuration Mode chat panel.
- V1 mobile is not optimized; the app should show a mobile holding screen.

## Required Inputs

- Selected assets.
- Treasury objective.
- Risk appetite.
- Selected models, defaulting to the initial 3 supported models.

Optional:

- Supported predefined constraints.

Do not include benchmark preference or time horizon as user inputs in V1.

## Asset Selection

- Use a searchable dropdown backed by the cached CoinGecko token list.
- Search only across CoinGecko `symbol` and `name`, not `id`.
- Load cached token list on page load where available.
- Fetch CoinGecko token list on page load only if no cache exists.
- If a manual user search does not appear in cached `symbol` or `name`, the app may refetch the token list and update cache.
- Selected assets display as chips beneath the dropdown.
- Maximum selected assets: 10.
- Minimum selected assets to generate a plan: 2.
- Show a visible asset count/counter communicating the 2 minimum and 10 maximum.
- Chips show the symbol as a dominant cashtag and token name below it in smaller text.
- Example chip copy: `$BTC` with `Bitcoin` beneath.
- Each selected asset chip must include an easy remove control.
- If two selected assets share the same symbol, use the token name to disambiguate.
- If two selected assets share both symbol and name, replace the displayed name with the CoinGecko `id`.
- Do not include token icons or category badges in V1.
- Stablecoins are allowed by default; do not try to identify or warn on stablecoins in the asset selector.

## Objective And Risk Appetite

- Capture treasury objective with button cards.
- Capture risk appetite with button cards.
- Users select one treasury objective.
- Treasury objective options:
  - `Maximize return`.
  - `Stable performance`.
  - `Best risk-adjusted returns`.
  - `Reduce drawdowns`.
  - `Diversify exposure`.
- Each treasury objective card should include an info tooltip with a short explanation.
- Users select one risk appetite.
- Risk appetite options:
  - `Very low`.
  - `Low`.
  - `Medium`.
  - `High`.
  - `Very high`.
- Risk appetite should not change how models are run in V1.
- Risk appetite should guide AI plan wording, Review Mode comparison, and model/result ranking against user needs.
- Multiple/ranked objectives are deferred beyond V1.

## Model Selection

- Show only supported V1 models.
- Hide unsupported/future models entirely.
- Initial supported models are pre-selected by default:
  - Mean Variance.
  - Risk Parity.
  - Hierarchical Risk Parity.
- Users may deselect down to one model.
- Each model card should include an info tooltip with a short plain-language explanation.
- If the AI suggests model changes in chat, the user must manually apply them in the component.
- During modelling-plan generation, the AI should accept the selected models requested by the user rather than changing the selection.

## Constraints

- Constraints are optional.
- Present constraints in a collapsed `Optional constraints` section.
- Use simple presets only where the modelling system can enforce them.
- V1 constraints:
  - max allocation per asset.
  - min allocation per asset.
  - max allocation to selected asset.
  - min allocation to selected asset.
  - max number of assets in portfolio.
  - min number of assets in portfolio.
- Global min/max allocation constraints apply to all selected assets.
- Selected-asset min/max constraints allow the user to select one or more assets from the current asset list.
- Selected-asset constraints should be added once per constraint type with one percentage value, then applied to any number of currently selected assets.
- Percentage constraints use small numeric inputs, not sliders.
- Percentage inputs allow 0-100 with 1% steps and no more than 3 digits.
- Number-of-assets constraints use numeric inputs bounded by the current selected asset count.
- Invalid constraints block `Generate Plan`.
- Deterministic validation should catch clearly impossible constraints before any AI call, for example:
  - min allocation of 20% across 6 assets.
  - max allocation of 30% across only 3 assets.

## Modelling Plan Confirmation

- Generated plan is shown as readable Markdown.
- Generated plan temporarily replaces the configuration form.
- Users have exactly three generated-plan actions:
  - `Run`: begin validation and modelling to move past Configuration Phase.
  - `Regenerate`: generate another plan while staying in the same core workflow.
  - `Reconfigure`: abandon the current plan and return to the configuration screen with previous items still selected.
- `Reconfigure` requires confirmation copy: `This abandons the current plan and returns to Configuration with your previous selections still filled in.`
- After a plan is generated, the form is read-only until the user chooses `Reconfigure`.
- `Reconfigure` shows the configuration form again and invalidates the previous generated plan.
- The configuration form should then offer `Generate Plan` as the forward action.
- Users cannot directly edit the generated modelling plan in V1.

## State And Reset

- Every field should autosave immediately to active local state.
- Configuration Mode should include a `Reset Configuration` action.
- `Reset Configuration` requires confirmation copy: `This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.`
- `Reset Configuration` returns to the empty/default Configuration form and clears generated plan, Configuration chat, Review chat, and model outputs.
- `Start New Model` belongs to Review Mode.
- If the user changes inputs after a plan has been generated, the existing plan is invalidated through `Reconfigure`.

## Failure And Validation

- Required validation failures should prevent plan generation or model run.
- If the Configuration Agent says the setup cannot be modelled yet, the UI should show the reason and the required fix.
- Unsupported model metadata from AI must not be accepted.
- `Generate Plan` first runs deterministic validation before calling AI.
- AI may also validate and explain issues, but deterministic validation owns the first blocking pass.
- Prefer surfacing validation errors through the chat experience so it feels like the agent is giving feedback.
- CoinGecko token-list loading errors block the whole configuration form.
- If token-list loading fails, offer a check-again/retry action.
- If token-list loading fails again, prompt the user to reload and check the CoinGecko API key.
- Assets with fewer than 90 valid price days are discovered during Modelling after price fetch, not during initial configuration.
- When insufficient-history assets are discovered, the app should store a local suppression record containing the token and first available price date.
- Suppressed insufficient-history assets may be hidden from selection until 90 days after the first available price date, then shown again.

## Notes

- This spec depends on the CoinGecko API and parameters agent specs.
