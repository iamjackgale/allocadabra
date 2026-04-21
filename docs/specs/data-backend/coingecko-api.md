created: 2026-04-21 08:27:31 BST
last_updated: 2026-04-21 08:27:31 BST

# CoinGecko API Spec

## Purpose

Define how Allocadabra ingests raw CoinGecko data for use in the app.

## Initial Scope

- Fetch a list of available crypto tokens from CoinGecko.
- Fetch token price data from CoinGecko for selected assets.
- Normalize CoinGecko data enough for searchable asset selection and later dataset building.

## Notes

- This spec should define the exact CoinGecko endpoints, request parameters, rate-limit handling, response normalization, and error handling after the initial contract pass.
- This spec feeds the data storage and dataset building specs.
