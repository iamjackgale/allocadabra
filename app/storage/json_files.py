"""JSON file helpers with atomic writes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    """Read JSON from a path, returning default when no file exists."""
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    """Write JSON atomically enough for local app usage."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_path, path)

