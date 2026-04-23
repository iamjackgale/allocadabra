"""CoinGecko Demo API client and normalizers."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)

COINGECKO_API_KEY_ENV = "COINGECKO_API_KEY"
DEFAULT_BASE_URL = "https://api.coingecko.com/api/v3"


class MissingCoinGeckoAPIKeyError(RuntimeError):
    """Raised when CoinGecko API credentials are unavailable."""


class CoinGeckoAPIError(RuntimeError):
    """Raised when CoinGecko requests fail."""


@dataclass(frozen=True)
class TokenOption:
    """Normalized token option exposed to app layers."""

    id: str
    symbol: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PricePoint:
    """Normalized daily USD price point."""

    id: str
    date: str
    price: float

    def to_dict(self) -> dict[str, str | float]:
        return asdict(self)


def load_dotenv_if_present(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs from `.env` without overriding env vars."""
    repo_env_path = Path(__file__).resolve().parents[2] / ".env"
    candidates = [path] if path else [Path.cwd() / ".env", repo_env_path]

    for env_path in candidates:
        if env_path is None or not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class CoinGeckoClient:
    """Small stdlib HTTP client for CoinGecko free public endpoints."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 20,
        max_retries: int = 2,
        retry_delay_seconds: float = 1,
    ) -> None:
        load_dotenv_if_present()
        self.api_key = api_key or os.getenv(COINGECKO_API_KEY_ENV, "")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        if not self.api_key:
            raise MissingCoinGeckoAPIKeyError(
                "COINGECKO_API_KEY is not set. Add it to .env or the process environment."
            )

    def fetch_token_list(self) -> list[TokenOption]:
        """Fetch and normalize active CoinGecko tokens."""
        payload = self._get_json(
            "/coins/list",
            {"status": "active", "include_platform": "false"},
        )
        if not isinstance(payload, list):
            raise CoinGeckoAPIError("CoinGecko token list response was not a list.")
        return normalize_token_list(payload)

    def fetch_market_chart(self, coin_id: str) -> list[PricePoint]:
        """Fetch and normalize up to 365 daily USD price points for a token."""
        payload = self._get_json(
            f"/coins/{coin_id}/market_chart",
            {
                "vs_currency": "usd",
                "interval": "daily",
                "precision": "full",
                "days": "365",
            },
        )
        if not isinstance(payload, dict):
            raise CoinGeckoAPIError("CoinGecko market chart response was not an object.")
        return normalize_market_chart(coin_id, payload)

    def _get_json(self, path: str, params: dict[str, str]) -> Any:
        query = urlencode(params)
        url = f"{self.base_url}{path}?{query}"
        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": self.api_key,
        }

        for attempt in range(self.max_retries + 1):
            try:
                request = Request(url, headers=headers, method="GET")
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                return json.loads(body)
            except HTTPError as exc:
                if exc.code in {408, 409, 425, 429, 500, 502, 503, 504}:
                    self._sleep_before_retry(attempt, exc)
                    continue
                message = exc.read().decode("utf-8", errors="replace")
                raise CoinGeckoAPIError(
                    f"CoinGecko request failed with status {exc.code}: {message}"
                ) from exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                self._sleep_before_retry(attempt, exc)
                continue

        raise CoinGeckoAPIError(f"CoinGecko request failed after retries: {path}")

    def _sleep_before_retry(self, attempt: int, exc: BaseException) -> None:
        if attempt >= self.max_retries:
            raise CoinGeckoAPIError("CoinGecko request failed after retries.") from exc
        delay = self.retry_delay_seconds * (attempt + 1)
        logger.warning("CoinGecko request failed; retrying in %.1fs", delay)
        time.sleep(delay)


def normalize_token_list(rows: list[Any]) -> list[TokenOption]:
    """Normalize CoinGecko `/coins/list` rows."""
    tokens: list[TokenOption] = []
    seen_ids: set[str] = set()

    for row in rows:
        if not isinstance(row, dict):
            continue
        coin_id = _clean_text(row.get("id"))
        symbol = _clean_text(row.get("symbol"))
        name = _clean_text(row.get("name"))
        if not coin_id or not symbol or not name or coin_id in seen_ids:
            continue
        tokens.append(TokenOption(id=coin_id, symbol=symbol, name=name))
        seen_ids.add(coin_id)

    return sorted(tokens, key=lambda token: (token.symbol.lower(), token.name.lower(), token.id))


def normalize_market_chart(coin_id: str, payload: dict[str, Any]) -> list[PricePoint]:
    """Normalize CoinGecko market chart data to daily points with forward fill."""
    raw_prices = payload.get("prices", [])
    if not isinstance(raw_prices, list):
        return []

    by_date: dict[date, float] = {}
    for raw_point in raw_prices:
        if not _is_price_pair(raw_point):
            continue
        timestamp_ms, raw_price = raw_point
        try:
            observed_date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date()
            price = float(raw_price)
        except (TypeError, ValueError, OSError):
            continue
        by_date[observed_date] = price

    if not by_date:
        return []

    points: list[PricePoint] = []
    current = min(by_date)
    last = max(by_date)
    last_price: float | None = None

    while current <= last:
        if current in by_date:
            last_price = by_date[current]
        if last_price is not None:
            points.append(PricePoint(id=coin_id, date=current.isoformat(), price=last_price))
        current += timedelta(days=1)

    return points


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _is_price_pair(value: Any) -> bool:
    return isinstance(value, list) and len(value) >= 2
