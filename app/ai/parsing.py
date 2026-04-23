"""Parsing helpers for AI text plus structured metadata."""

from __future__ import annotations

import json
import re
from typing import Any


METADATA_FENCE_RE = re.compile(
    r"```allocadabra-metadata\s*(\{.*?\})\s*```",
    flags=re.IGNORECASE | re.DOTALL,
)
METADATA_COMMENT_RE = re.compile(
    r"<!--\s*allocadabra_metadata:\s*(\{.*?\})\s*-->",
    flags=re.IGNORECASE | re.DOTALL,
)


def split_visible_text_and_metadata(text: str) -> tuple[str, dict[str, Any]]:
    """Split model-visible text from app-readable metadata."""
    match = METADATA_FENCE_RE.search(text) or METADATA_COMMENT_RE.search(text)
    if not match:
        return text.strip(), {}

    metadata = _load_metadata(match.group(1))
    visible = text[: match.start()] + text[match.end() :]
    return visible.strip(), metadata


def _load_metadata(raw: str) -> dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("AI metadata must be a JSON object.")
    return payload


def markdown_sections(markdown: str) -> dict[str, str]:
    """Return Markdown heading sections keyed by lowercase heading text."""
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in markdown.splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if heading:
            current = _normalize_heading(heading.group(1))
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip().strip("#")).lower()
