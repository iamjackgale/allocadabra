created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# Data Storage Spec

## Purpose

Define how CoinGecko data is stored in a local cache for the app and updated over time.

## Initial Scope

- Store token list data fetched from CoinGecko.
- Store token price data fetched from CoinGecko.
- Define local cache refresh behaviour for stale CoinGecko data.
- Keep cached market data separate from user session state.

## Notes

- This spec should define storage format, cache keys, update cadence, invalidation rules, and recovery behaviour after the initial contract pass.
- This spec depends on the CoinGecko API spec.
