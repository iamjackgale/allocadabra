"""Canonical modelling dataset construction from normalized price histories."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)

MAX_ASSETS = 10
MAX_DAILY_OBSERVATIONS = 365
MIN_VALID_DAILY_PRICES = 90


class DatasetBuildError(ValueError):
    """Raised when selected asset data cannot form a modelling dataset."""


@dataclass(frozen=True)
class AssetColumnMetadata:
    """Mapping between a unique dataframe column and CoinGecko asset identity."""

    column: str
    id: str
    symbol: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetBuildResult:
    """Canonical price dataframe plus metadata needed downstream."""

    prices: pd.DataFrame
    assets: list[AssetColumnMetadata]
    metadata: dict[str, object]
    warnings: list[str]


def build_canonical_price_dataframe(
    *,
    selected_assets: list[dict[str, Any]],
    price_history_by_id: dict[str, list[dict[str, Any]]],
) -> DatasetBuildResult:
    """Build the aligned price dataframe specified by the modelling docs."""
    if len(selected_assets) > MAX_ASSETS:
        raise DatasetBuildError("Select no more than 10 assets for modelling.")
    if len(selected_assets) < 2:
        raise DatasetBuildError("Select at least 2 assets for modelling.")

    columns = _asset_columns(selected_assets)
    series_by_column: dict[str, pd.Series] = {}
    warnings: list[str] = []

    for asset, column_meta in zip(selected_assets, columns, strict=True):
        coin_id = column_meta.id
        raw_prices = price_history_by_id.get(coin_id)
        if not raw_prices:
            raise DatasetBuildError(
                f"Price history is missing for {column_meta.symbol.upper()} ({coin_id})."
            )

        series = _price_series(raw_prices)
        valid_count = int(series.notna().sum())
        if valid_count < MIN_VALID_DAILY_PRICES:
            raise DatasetBuildError(
                f"{column_meta.symbol.upper()} has fewer than 90 valid daily prices."
            )
        series_by_column[column_meta.column] = series.rename(column_meta.column)

    aligned = pd.concat(series_by_column.values(), axis=1).sort_index()
    aligned = aligned.ffill().tail(MAX_DAILY_OBSERVATIONS)
    aligned.index.name = "date"

    empty_columns = [column for column in aligned.columns if aligned[column].notna().sum() == 0]
    if empty_columns:
        raise DatasetBuildError(
            "One or more selected assets has no usable price history after alignment."
        )

    if aligned.empty:
        raise DatasetBuildError("The canonical modelling dataset is empty.")

    missing_cells = int(aligned.isna().sum().sum())
    if missing_cells:
        warnings.append(
            "Aligned prices contain missing early rows before every asset has a first valid price."
        )

    metadata = {
        "source_assets": [column.to_dict() for column in columns],
        "date_start": aligned.index.min().date().isoformat(),
        "date_end": aligned.index.max().date().isoformat(),
        "row_count": int(len(aligned)),
        "column_count": int(len(aligned.columns)),
        "missing_cell_count": missing_cells,
        "max_daily_observations": MAX_DAILY_OBSERVATIONS,
        "min_valid_daily_prices": MIN_VALID_DAILY_PRICES,
        "warnings": warnings,
    }
    logger.info("Built canonical price dataframe with shape %s", aligned.shape)
    return DatasetBuildResult(prices=aligned, assets=columns, metadata=metadata, warnings=warnings)


def _asset_columns(selected_assets: list[dict[str, Any]]) -> list[AssetColumnMetadata]:
    symbol_counts: dict[str, int] = {}
    columns: list[AssetColumnMetadata] = []

    for asset in selected_assets:
        coin_id = _required_text(asset, "id")
        symbol = _required_text(asset, "symbol")
        name = _required_text(asset, "name")
        symbol_key = symbol.lower()
        symbol_counts[symbol_key] = symbol_counts.get(symbol_key, 0) + 1
        display_symbol = _display_symbol(symbol)
        if symbol_counts[symbol_key] == 1:
            column = f"{display_symbol}_price"
        else:
            column = f"{display_symbol}_{_safe_column_token(coin_id)}_price"
        columns.append(AssetColumnMetadata(column=column, id=coin_id, symbol=symbol, name=name))

    if len({column.column for column in columns}) != len(columns):
        raise DatasetBuildError("Selected assets produced duplicate modelling columns.")
    return columns


def _price_series(raw_prices: list[dict[str, Any]]) -> pd.Series:
    rows: list[tuple[pd.Timestamp, float]] = []
    for row in raw_prices:
        try:
            date = pd.Timestamp(str(row["date"]), tz="UTC").normalize()
            price = float(row["price"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((date, price))

    if not rows:
        return pd.Series(dtype="float64")

    frame = pd.DataFrame(rows, columns=["date", "price"])
    return frame.groupby("date", sort=True)["price"].last().astype(float)


def _required_text(asset: dict[str, Any], key: str) -> str:
    value = str(asset.get(key, "")).strip()
    if not value:
        raise DatasetBuildError(f"Selected asset is missing required field: {key}.")
    return value


def _display_symbol(symbol: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", symbol.strip().upper()).strip("_")
    return cleaned or "ASSET"


def _safe_column_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "asset"
