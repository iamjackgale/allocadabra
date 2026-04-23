| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-23 12:32:47 BST |

# CoinGecko API Spec

## Purpose

Define how Allocadabra ingests raw CoinGecko data for use in the app.

## API Access

- Base URL: `https://api.coingecko.com/api/v3`
- Auth mode: CoinGecko Demo API.
- Auth header: `x-cg-demo-api-key`.
- API key source: `.env`.
- Endpoint policy: use only free public API endpoints accessible with the demo API key.

## Environment

The app must read the CoinGecko demo API key from environment configuration.

| Setting | Value |
|---|---|
| Environment variable | `COINGECKO_API_KEY` |
| Example location | `.env.example` |

The key must not be hard-coded or committed. Implementation should check `.env.example` before introducing any new environment variable names.

## Coins List

Endpoint:

```text
GET /coins/list
```

Docs:

```text
https://docs.coingecko.com/reference/coins-list
```

Purpose:

- Fetch the list of token IDs available from CoinGecko.
- Provide token options for the asset selection dropdown.

Request parameters:

| Parameter | Value |
|---|---|
| `status` | `active` |
| `include_platform` | `false` |

Normalized output:

| Field | Source | Use |
|---|---|---|
| `id` | CoinGecko token ID | Stored and used to fetch price data. |
| `symbol` | CoinGecko symbol | Displayed to the user and included in search. |
| `name` | CoinGecko name | Displayed to the user and included in search. |

Missing-data rule:

- Omit any token that does not include all of `id`, `symbol`, and `name`.

Frontend behaviour:

- The token selection dropdown/window should trigger the initial token-list call.
- The app may call the token list on page load so the dropdown has no delay when opened.
- The token list should be stored in the local market-data cache before presentation to the user.
- If the user types a search term and manually clicks search, the app may refetch the token list to confirm whether the term appears in `id`, `name`, or `symbol`.
- Token-list refetching should be user-prompted or page-load prompted, not continuous background polling.

## Price History

Endpoint:

```text
GET /coins/{id}/market_chart
```

Docs:

```text
https://docs.coingecko.com/reference/coins-id-market-chart
```

Purpose:

- Fetch daily USD price history for selected assets.
- Provide price data for dataset building and model execution.

Request parameters:

| Parameter | Value |
|---|---|
| `id` | CoinGecko token ID selected by the user |
| `vs_currency` | `usd` |
| `interval` | `daily` |
| `precision` | `full` |
| `days` | `365` |

Normalized output:

| Field | Source | Use |
|---|---|---|
| `date` | CoinGecko timestamp converted to UTC date | Dataset index. |
| `price` | CoinGecko price value | Daily price series for modelling. |

Missing-data rule:

- If a date has no price, forward-fill it using the last available price from a previous day.
- If no previous price exists for the missing date, the downstream dataset-building spec must decide whether to omit the date or reject the asset.

Fetch trigger:

- Token prices are fetched only after the user confirms their modelling scope and chooses to generate models.
- The app data layer handles price fetching entirely.
- The only user action that can trigger token price fetching is confirming the scope and selecting model generation.

## Retry, Timeout, And Rate-Limit Policy

The V1 CoinGecko client uses one shared HTTP policy for:

- `GET /coins/list`
- `GET /coins/{id}/market_chart`

Current client defaults:

| Setting | Value | Notes |
|---|---:|---|
| `timeout_seconds` | `20` | Applies per HTTP request attempt. |
| `max_retries` | `2` | Allows up to 3 total attempts: the initial attempt plus 2 retries. |
| `retry_delay_seconds` | `1` | Linear retry delay: 1 second before the first retry, 2 seconds before the second retry. |

Retryable failures:

- HTTP status `408`, `409`, `425`, `429`, `500`, `502`, `503`, and `504`.
- Network/URL failures surfaced by Python as `URLError`.
- Request timeouts surfaced as `TimeoutError`.
- JSON decode failures when the response body cannot be parsed.

Non-retryable failures:

- Other HTTP errors fail immediately and include the CoinGecko response status and response text in the internal exception.
- Missing `COINGECKO_API_KEY` fails before any live API request.
- Unexpected response shapes fail during endpoint-specific normalization checks.

Caller behaviour:

- The ingestion client raises `MissingCoinGeckoAPIKeyError` when `COINGECKO_API_KEY` is unavailable.
- The ingestion client raises `CoinGeckoAPIError` when a CoinGecko request fails or returns an unusable response.
- The app/storage layer may catch per-asset price-history failures and return user-facing `errors` entries without aborting every other selected asset.
- Token-list failures should be treated as recoverable setup/API errors for the UI to surface; the app should not expose API keys, raw backend logs, or detailed request payloads to users.

Rate-limit behaviour:

- V1 does not implement proactive request throttling.
- CoinGecko `429` responses are retried using the shared retry policy above.
- The app should avoid continuous background polling. Token-list refreshes should remain page-load or user-prompted, and price-history requests should run only when modelling begins or when cached data is insufficient/stale.

Live API validation:

- Live CoinGecko validation requires `COINGECKO_API_KEY` to be configured in `.env` or the process environment.
- Default validation may use import, compile, fixture, or smoke checks that do not call CoinGecko.
- Task `064` separately tracks whether the 2-day price-cache freshness tolerance in `/docs/specs/data-backend/data-storage.md` should change after Streamlit/runtime validation.

## Component Ownership

- Frontend triggers token-list retrieval for search and selection.
- The app data layer owns CoinGecko API calls, authentication, normalization, and local-cache writes.
- The app data layer owns all token-price retrieval.
- Dataset building consumes normalized price history; it should not call CoinGecko directly.

## Initial App Interfaces

Initial backend/data scaffolding exposes frontend-callable functions from `app.storage.data_api`:

| Function | Purpose | Return shape |
|---|---|---|
| `list_token_options(search_term=None, force_refresh=False)` | Return cached or freshly fetched token options, optionally filtered by user-facing symbol/name search. | `{ok, tokens, count}` |
| `fetch_price_history_for_assets(asset_ids, force_refresh=False)` | Fetch/read normalized daily price history for selected CoinGecko IDs. | `{ok, prices, statuses, errors}` |

Token search should filter on `symbol` and `name` for user-facing behaviour.

## Open Questions

- None for V1 CoinGecko request configuration. Price-cache freshness tuning remains tracked separately in task `064`.
