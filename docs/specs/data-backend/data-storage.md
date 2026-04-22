| Metadata | Value |
|---|---|
| created | 2026-04-21 08:27:31 BST |
| last_updated | 2026-04-22 20:23:50 BST |

# Data Storage Spec

## Purpose

Define how CoinGecko market data is stored in the local app cache and updated over time.

## Storage Boundary

- All CoinGecko market-data storage is local to the app workspace.
- The app should not require a separate backend service for market-data persistence.
- CoinGecko cache data should persist until the user clears local storage/cache files outside the app.
- The app should not provide an in-app control to clear the CoinGecko cache.
- Cached CoinGecko data must be stored separately from active user input state and model output state.
- V1 storage should live under `/storage/cache/coingecko`.

## Data Types

### Token List Cache

Stores normalized token options from CoinGecko.

Required normalized fields:

| Field | Description |
|---|---|
| `id` | CoinGecko token ID used for price fetches. |
| `symbol` | Token symbol displayed and searched in the UI. |
| `name` | Token name displayed and searched in the UI. |

Load behaviour:

- On app load, check local cache for an existing token list.
- If a cached token list exists, load it for the token selection UI.
- If no cached token list exists, fetch `/coins/list`, normalize the response, store it, and then present it to the user.
- If the user manually searches and the term does not appear in cached `id`, `symbol`, or `name`, the app may refetch the token list and append/update cached entries.

### Insufficient History Suppression Cache

Stores token IDs discovered during Modelling to have fewer than 90 valid daily prices.

Purpose:

- Avoid repeatedly presenting assets that are currently known to be unusable for modelling.
- Allow those assets to reappear once enough time may have passed for 90 daily observations.

Required fields:

| Field | Description |
|---|---|
| `id` | CoinGecko token ID. |
| `symbol` | CoinGecko symbol at the time of rejection. |
| `name` | CoinGecko name at the time of rejection. |
| `first_available_price_date` | First valid UTC price date found during price fetch. |
| `suppressed_until` | Date 90 days after `first_available_price_date`. |
| `reason` | Rejection reason, initially `insufficient_price_history`. |

Rules:

- Populate this cache only after price data is fetched during Modelling.
- Do not prefetch price data during Configuration just to identify insufficient-history tokens.
- The asset selector may hide suppressed tokens until `suppressed_until`.
- Once `suppressed_until` has passed, the asset may be shown again and revalidated during a future modelling run.

### Price History Cache

Stores normalized daily USD price history for CoinGecko token IDs.

Required normalized fields:

| Field | Description |
|---|---|
| `id` | CoinGecko token ID. |
| `date` | UTC date for the price observation. |
| `price` | Daily USD price. |

Load behaviour:

- Price data is fetched only when model generation begins after the user confirms scope.
- Before fetching, check local cache for existing price data for each selected token ID.
- If sufficient cached price data exists for the required modelling window, use cached data.
- If cached price data is missing or stale, fetch only the data needed to update the cache where practical.
- Newly fetched price data should be appended to or merged into the existing token price cache.
- The app should avoid unnecessary full reloads of existing price history.

## Update Rules

- CoinGecko data should be treated as a growing local app cache.
- New token-list or price-history data should update existing cache entries rather than replace the entire cache unless replacement is required for data integrity.
- Cache writes should happen after normalization, so downstream specs consume app-normalized data.
- Duplicate token or price entries should be resolved by stable keys:
  - Token list: `id`.
  - Price history: `id` plus `date`.

## Clear/Reset Behaviour

- In-app workflow reset must not clear CoinGecko cache.
- Starting a new model must not clear CoinGecko cache.
- Exporting outputs must not clear CoinGecko cache.
- CoinGecko data is lost only if the user clears local storage/cache files outside the app.

## Relationship To Other Specs

- `/docs/specs/data-backend/coingecko-api.md` defines source endpoints and normalization.
- `/docs/specs/data-backend/session-storage.md` defines active user inputs and model output storage.
- `/docs/specs/data-backend/dataset-building.md` consumes cached price data to prepare modelling datasets.

## Open Questions

- Exact local cache file format: candidates include JSON, CSV, Parquet, or SQLite depending on implementation simplicity and dependency constraints.
- Exact cache schema and versioning strategy.
- Exact rule for what counts as sufficient cached price data for a modelling run.
