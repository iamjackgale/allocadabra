"""Shared logging helpers for Allocadabra."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure process-wide application logging."""
    logging.basicConfig(
        level=level,
        format="| %(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def log_dataframe_preview(name: str, df: object, rows: int = 3) -> None:
    """Log a concise dataframe-like preview for CLI/debug workflows."""
    logger.info("\n%s\n%s\n%s", "=" * 60, name, "=" * 60)
    logger.info("Shape: %s", getattr(df, "shape", None))
    logger.info("Columns: %s", list(getattr(df, "columns", [])))
    logger.info("First %s rows:\n%s", rows, df.head(rows).to_string())

