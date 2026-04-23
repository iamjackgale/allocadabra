"""Structured progress events for the Modelling Phase."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Literal

from app.storage.schemas import utc_now_iso


ProgressPhase = Literal[
    "validation",
    "ingestion",
    "datasets",
    "modelling",
    "analysis",
    "outputs",
]

ProgressStatus = Literal["started", "completed", "failed", "info"]

ProgressCallback = Callable[[dict[str, object]], None]


@dataclass(frozen=True)
class ProgressEvent:
    """Frontend-safe progress event for the Modelling screen."""

    phase: ProgressPhase
    status: ProgressStatus
    message: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def make_progress_event(
    *,
    phase: ProgressPhase,
    status: ProgressStatus,
    message: str,
) -> dict[str, object]:
    """Build one frontend-safe progress event."""
    return ProgressEvent(
        phase=phase,
        status=status,
        message=message,
        created_at=utc_now_iso(),
    ).to_dict()


def emit_progress(
    callback: ProgressCallback | None,
    events: list[dict[str, object]],
    *,
    phase: ProgressPhase,
    status: ProgressStatus,
    message: str,
) -> dict[str, object]:
    """Record and optionally emit one progress event."""
    event = make_progress_event(
        phase=phase,
        status=status,
        message=message,
    )
    events.append(event)
    if callback is not None:
        callback(event)
    return event
