"""Local environment loading helpers for the AI integration."""

from __future__ import annotations

import os
from pathlib import Path


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
