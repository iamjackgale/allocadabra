"""Canonical local storage paths."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = REPO_ROOT / "storage" / "cache"

COINGECKO_CACHE_DIR = STORAGE_ROOT / "coingecko"
COINGECKO_PRICES_DIR = COINGECKO_CACHE_DIR / "prices"
TOKEN_LIST_FILE = COINGECKO_CACHE_DIR / "tokens.json"
INSUFFICIENT_HISTORY_FILE = COINGECKO_CACHE_DIR / "insufficient_history.json"

USER_INPUTS_DIR = STORAGE_ROOT / "user-inputs"
ACTIVE_WORKFLOW_FILE = USER_INPUTS_DIR / "active_workflow.json"

MODEL_OUTPUTS_DIR = STORAGE_ROOT / "model-outputs"
MODEL_OUTPUT_MANIFEST_FILE = MODEL_OUTPUTS_DIR / "manifest.json"


def ensure_storage_dirs() -> None:
    """Create expected storage directories if they do not exist."""
    for path in (
        COINGECKO_CACHE_DIR,
        COINGECKO_PRICES_DIR,
        USER_INPUTS_DIR,
        MODEL_OUTPUTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)

