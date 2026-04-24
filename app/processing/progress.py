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
CancelCheck = Callable[[], bool]


class ModellingCancelled(RuntimeError):
    """Raised internally when a cooperative cancellation request is observed."""

    def __init__(
        self,
        message: str = "Modelling was cancelled.",
        *,
        phase: ProgressPhase = "outputs",
    ) -> None:
        super().__init__(message)
        self.phase = phase


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


def is_cancel_requested(cancel_check: CancelCheck | None) -> bool:
    """Return whether a cooperative cancellation has been requested."""
    return bool(cancel_check is not None and cancel_check())


def raise_if_cancelled(
    cancel_check: CancelCheck | None,
    *,
    phase: ProgressPhase = "outputs",
) -> None:
    """Stop modelling cooperatively when the caller requests cancellation."""
    if is_cancel_requested(cancel_check):
        raise ModellingCancelled(phase=phase)
