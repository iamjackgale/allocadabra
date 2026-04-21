created: 2026-04-21 10:53:18 BST
last_updated: 2026-04-21 10:53:18 BST

# Logging Spec

## Purpose

Define the shared logging pattern for Allocadabra so CLI tools, ingestion jobs, processing builds, model runs, AI calls, and future app actions report progress consistently.

## Shared Logging Utility

Use one shared logging utility, then every module or script gets its own named logger.

Expected implementation location:

```text
app/utils/logging.py
```

Expected utility:

```python
import logging

def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="| %(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
```

## Module Logger Pattern

Each module should define a named logger:

```python
import logging

logger = logging.getLogger(__name__)
```

## CLI Entrypoint Pattern

CLI entrypoints and scripts should configure logging once at startup:

```python
from app.utils.logging import configure_logging

def main() -> int:
    configure_logging(level=logging.DEBUG if args.debug else logging.INFO)
    logger.info("Building ETH dataset")
    ...
```

## Workflow Logging Rules

Log each major phase, row counts, output paths, and recoverable failures.

Use parameterized logging with `%s` placeholders rather than f-strings for normal logger calls.

Example:

```python
logger.info("Building ETH dataset from raw parquet files...")

try:
    eth = load_raw_columns("theblock_eth", [DATE_COL, "ETH Price"])
    logger.info("  theblock_eth: %s rows", len(eth))
except FileNotFoundError as exc:
    logger.warning("  theblock_eth: %s", exc)

logger.info("Saved dataset parquet to %s", parquet_path)
```

## Log Levels

Use levels consistently:

| Level | Use |
|---|---|
| `debug` | Noisy internals and detailed troubleshooting data. |
| `info` | Normal progress, major phases, row counts, and output paths. |
| `warning` | Skipped or missing non-fatal data and recoverable failures. |
| `error` | Abort conditions or operations that truly failed. |

Examples:

```python
logger.debug("Reduced delay to %.2fs", current_delay)
logger.info("Progress: %s successful, %s failed", successful, failed)
logger.warning("Missing configured feature columns: %s", missing_features)
logger.error("COINGECKO_API_KEY not set. Please set it in .env.")
```

## Dataframe Preview Helper

For dataframe-heavy workflows, include a preview helper for confirmation during CLI or debug runs.

Expected helper:

```python
def log_dataframe_preview(name: str, df: pd.DataFrame, rows: int = 3) -> None:
    logger.info("\n%s\n%s\n%s", "=" * 60, name, "=" * 60)
    logger.info("Shape: %s", df.shape)
    logger.info("Columns: %s", list(df.columns))
    logger.info("First %s rows:\n%s", rows, df.head(rows).to_string())
```

## No Print Rule

Do not use `print()` in production paths.

CLI tools, ingestion jobs, processing builds, model runs, AI calls, and app actions should report progress through the shared logging pattern so local runs, scheduled jobs, browser-local app logs, and future cloud logs remain consistent.

## Agent Guidance

All implementation agents should follow this spec when writing scripts or production paths that report progress.

Agent prompts should reference this file when the agent owns implementation work that logs actions or failures.
