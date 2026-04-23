"""CoinGecko market-data cache and retrieval functions."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from app.ingestion.coingecko import CoinGeckoClient, PricePoint, TokenOption
from app.storage.json_files import read_json, write_json
from app.storage.paths import (
    COINGECKO_PRICES_DIR,
    INSUFFICIENT_HISTORY_FILE,
    TOKEN_LIST_FILE,
    ensure_storage_dirs,
)
from app.storage.schemas import metadata_payload


logger = logging.getLogger(__name__)

MIN_VALID_DAILY_PRICES = 90
PRICE_CACHE_FRESHNESS_DAYS = 2


@dataclass(frozen=True)
class CacheStatus:
    """Market-cache status for a requested token price series."""

    coin_id: str
    cache_hit: bool
    valid_price_count: int
    latest_date: str | None
    stale: bool


def get_token_options(*, force_refresh: bool = False) -> list[TokenOption]:
    """Return token options from cache, fetching CoinGecko when needed."""
    ensure_storage_dirs()
    if not force_refresh:
        cached = _read_cached_tokens()
        if cached:
            return _filter_suppressed_tokens(cached)

    logger.info("Fetching CoinGecko token list")
    tokens = CoinGeckoClient().fetch_token_list()
    _write_cached_tokens(tokens)
    return _filter_suppressed_tokens(tokens)


def search_token_options(term: str, *, force_refresh: bool = False) -> list[TokenOption]:
    """Search token options by user-facing symbol and name."""
    normalized = term.strip().lower()
    tokens = get_token_options(force_refresh=force_refresh)
    if not normalized:
        return tokens
    return [
        token
        for token in tokens
        if normalized in token.symbol.lower() or normalized in token.name.lower()
    ]


def get_price_history(coin_id: str, *, force_refresh: bool = False) -> list[PricePoint]:
    """Return normalized daily price history for a CoinGecko token ID."""
    ensure_storage_dirs()
    cached = _read_price_csv(coin_id)
    status = price_cache_status(coin_id, cached)
    if not force_refresh and cached and status.cache_hit and not status.stale:
        return cached

    logger.info("Fetching CoinGecko price history for %s", coin_id)
    fetched = CoinGeckoClient().fetch_market_chart(coin_id)
    merged = _merge_price_points(cached, fetched)
    _write_price_csv(coin_id, merged)
    return merged


def price_cache_status(coin_id: str, points: list[PricePoint] | None = None) -> CacheStatus:
    """Return enough cache metadata for validation and progress UI."""
    price_points = points if points is not None else _read_price_csv(coin_id)
    valid_dates = [point.date for point in price_points if point.price is not None]
    latest_date = max(valid_dates) if valid_dates else None
    stale = True

    if latest_date:
        latest = date.fromisoformat(latest_date)
        today = datetime.now(tz=timezone.utc).date()
        stale = latest < today - timedelta(days=PRICE_CACHE_FRESHNESS_DAYS)

    return CacheStatus(
        coin_id=coin_id,
        cache_hit=len(valid_dates) >= MIN_VALID_DAILY_PRICES,
        valid_price_count=len(valid_dates),
        latest_date=latest_date,
        stale=stale,
    )


def record_insufficient_history(
    *,
    coin_id: str,
    symbol: str,
    name: str,
    first_available_price_date: str | None,
) -> None:
    """Suppress a token until it may have enough price history for modelling."""
    ensure_storage_dirs()
    existing = read_json(INSUFFICIENT_HISTORY_FILE, default={"tokens": []})
    records = {
        record.get("id"): record
        for record in existing.get("tokens", [])
        if isinstance(record, dict) and record.get("id")
    }

    if first_available_price_date:
        first_date = date.fromisoformat(first_available_price_date)
    else:
        first_date = datetime.now(tz=timezone.utc).date()

    records[coin_id] = {
        "id": coin_id,
        "symbol": symbol,
        "name": name,
        "first_available_price_date": first_date.isoformat(),
        "suppressed_until": (first_date + timedelta(days=MIN_VALID_DAILY_PRICES)).isoformat(),
        "reason": "insufficient_price_history",
    }

    write_json(
        INSUFFICIENT_HISTORY_FILE,
        metadata_payload(tokens=sorted(records.values(), key=lambda record: record["id"])),
    )


def _read_cached_tokens() -> list[TokenOption]:
    payload = read_json(TOKEN_LIST_FILE, default={})
    rows = payload.get("tokens", []) if isinstance(payload, dict) else []
    tokens: list[TokenOption] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        coin_id = str(row.get("id", "")).strip()
        symbol = str(row.get("symbol", "")).strip()
        name = str(row.get("name", "")).strip()
        if coin_id and symbol and name:
            tokens.append(TokenOption(id=coin_id, symbol=symbol, name=name))
    return tokens


def _write_cached_tokens(tokens: list[TokenOption]) -> None:
    write_json(TOKEN_LIST_FILE, metadata_payload(tokens=[token.to_dict() for token in tokens]))


def _filter_suppressed_tokens(tokens: list[TokenOption]) -> list[TokenOption]:
    payload = read_json(INSUFFICIENT_HISTORY_FILE, default={})
    rows = payload.get("tokens", []) if isinstance(payload, dict) else []
    today = datetime.now(tz=timezone.utc).date()
    suppressed_ids: set[str] = set()

    for row in rows:
        if not isinstance(row, dict):
            continue
        suppressed_until = row.get("suppressed_until")
        coin_id = row.get("id")
        if not isinstance(coin_id, str) or not isinstance(suppressed_until, str):
            continue
        try:
            if date.fromisoformat(suppressed_until) > today:
                suppressed_ids.add(coin_id)
        except ValueError:
            continue

    return [token for token in tokens if token.id not in suppressed_ids]


def _price_file(coin_id: str) -> Path:
    return COINGECKO_PRICES_DIR / f"{quote(coin_id, safe='')}.csv"


def _read_price_csv(coin_id: str) -> list[PricePoint]:
    path = _price_file(coin_id)
    if not path.exists():
        return []

    points: list[PricePoint] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                points.append(
                    PricePoint(
                        id=str(row["id"]),
                        date=str(row["date"]),
                        price=float(row["price"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Skipping invalid cached price row for %s", coin_id)
    return sorted(points, key=lambda point: point.date)


def _write_price_csv(coin_id: str, points: list[PricePoint]) -> None:
    path = _price_file(coin_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "date", "price"])
        writer.writeheader()
        for point in sorted(points, key=lambda item: item.date):
            writer.writerow(point.to_dict())


def _merge_price_points(existing: list[PricePoint], incoming: list[PricePoint]) -> list[PricePoint]:
    merged = {point.date: point for point in existing}
    merged.update({point.date: point for point in incoming})
    return sorted(merged.values(), key=lambda point: point.date)
