"""Helpers for writing modelling artifacts and manifest-ready metadata."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import pandas as pd


logger = logging.getLogger(__name__)

ArtifactStatus = Literal["available", "missing", "failed", "disabled"]


@dataclass(frozen=True)
class ArtifactEntry:
    """Manifest-ready artifact metadata for Backend/Data packaging."""

    artifact_id: str
    label: str
    category: str
    model_id: str | None
    output_type: str
    format: str
    path: str | None
    status: ArtifactStatus
    reason: str | None
    included_in_download_all: bool
    individual_download_enabled: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ArtifactWriter:
    """Write model-owned artifacts under the model-output directory."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "missing").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "models").mkdir(parents=True, exist_ok=True)
        self.entries: list[ArtifactEntry] = []

    def write_dataframe(
        self,
        *,
        df: pd.DataFrame,
        relative_path: str,
        artifact_id: str,
        label: str,
        category: str,
        output_type: str,
        model_id: str | None = None,
        individual_download_enabled: bool = True,
    ) -> ArtifactEntry:
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return self._add_available(
            artifact_id=artifact_id,
            label=label,
            category=category,
            model_id=model_id,
            output_type=output_type,
            format_="csv",
            path=relative_path,
            individual_download_enabled=individual_download_enabled,
        )

    def write_json(
        self,
        *,
        payload: object,
        relative_path: str,
        artifact_id: str,
        label: str,
        category: str,
        output_type: str,
        model_id: str | None = None,
        individual_download_enabled: bool = True,
    ) -> ArtifactEntry:
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return self._add_available(
            artifact_id=artifact_id,
            label=label,
            category=category,
            model_id=model_id,
            output_type=output_type,
            format_="json",
            path=relative_path,
            individual_download_enabled=individual_download_enabled,
        )

    def write_png_from_plot(
        self,
        *,
        relative_path: str,
        artifact_id: str,
        label: str,
        category: str,
        output_type: str,
        plotter: object,
        model_id: str | None = None,
    ) -> ArtifactEntry:
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
            plotter(ax)
            fig.savefig(path, dpi=160)
            plt.close(fig)
        except Exception as exc:  # PNG export is best-effort in V1.
            logger.warning("PNG artifact %s unavailable: %s", artifact_id, exc)
            return self.add_missing(
                artifact_id=artifact_id,
                label=label,
                category=category,
                output_type=output_type,
                reason=f"PNG export is unavailable for this artifact: {exc}",
                model_id=model_id,
            )

        return self._add_available(
            artifact_id=artifact_id,
            label=label,
            category=category,
            model_id=model_id,
            output_type=output_type,
            format_="png",
            path=relative_path,
            individual_download_enabled=True,
        )

    def add_missing(
        self,
        *,
        artifact_id: str,
        label: str,
        category: str,
        output_type: str,
        reason: str,
        model_id: str | None = None,
    ) -> ArtifactEntry:
        relative_path = f"missing/{artifact_id}.txt"
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(reason + "\n", encoding="utf-8")
        entry = ArtifactEntry(
            artifact_id=artifact_id,
            label=label,
            category=category,
            model_id=model_id,
            output_type=output_type,
            format="txt",
            path=relative_path,
            status="missing",
            reason=reason,
            included_in_download_all=True,
            individual_download_enabled=False,
        )
        self.entries.append(entry)
        return entry

    def _add_available(
        self,
        *,
        artifact_id: str,
        label: str,
        category: str,
        model_id: str | None,
        output_type: str,
        format_: str,
        path: str,
        individual_download_enabled: bool,
    ) -> ArtifactEntry:
        entry = ArtifactEntry(
            artifact_id=artifact_id,
            label=label,
            category=category,
            model_id=model_id,
            output_type=output_type,
            format=format_,
            path=path,
            status="available",
            reason=None,
            included_in_download_all=True,
            individual_download_enabled=individual_download_enabled,
        )
        self.entries.append(entry)
        return entry
