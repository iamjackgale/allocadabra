"""Shared storage schema constants and helpers."""

from __future__ import annotations

from datetime import datetime, timezone


SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def metadata_payload(**data: object) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": utc_now_iso(),
        **data,
    }
