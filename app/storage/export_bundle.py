"""Export manifest and bundle creation for Review downloads."""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from zipfile import ZIP_DEFLATED, ZipFile

from app.storage.json_files import read_json, write_json
from app.storage.paths import (
    ACTIVE_WORKFLOW_FILE,
    COINGECKO_CACHE_DIR,
    MODEL_OUTPUT_MANIFEST_FILE,
    MODEL_OUTPUTS_DIR,
    ensure_storage_dirs,
)
from app.storage.schemas import SCHEMA_VERSION, utc_now_iso


logger = logging.getLogger(__name__)

ArtifactCategory = Literal["general", "model", "manifest", "missing", "failure"]
ArtifactFormat = Literal["json", "md", "csv", "png", "txt"]
ArtifactStatus = Literal["available", "missing", "failed", "disabled"]

BUNDLE_FILENAME_PREFIX = "allocadabra-results"
MODEL_ARTIFACT_PATH_PREFIX = "models"
MISSING_ARTIFACT_PATH_PREFIX = "missing"
ZIP_FORMAT = "zip"


@dataclass(frozen=True)
class ArtifactEntry:
    """Manifest entry consumed by Frontend download controls."""

    artifact_id: str
    label: str
    category: ArtifactCategory
    model_id: str | None
    output_type: str
    format: ArtifactFormat
    path: str | None
    status: ArtifactStatus
    reason: str | None
    included_in_download_all: bool
    individual_download_enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExportBundleResult:
    """Result returned after manifest and bundle preparation."""

    ok: bool
    manifest_path: str
    bundle_path: str | None
    bundle_filename: str
    download_all_enabled: bool
    reason: str | None
    manifest: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def prepare_review_exports(
    *,
    modelling_artifacts: list[dict[str, Any]] | None = None,
    failed_models: list[dict[str, Any]] | None = None,
    missing_artifacts: list[dict[str, Any]] | None = None,
    created_at: str | None = None,
) -> ExportBundleResult:
    """Create export files, manifest, and Download All bundle for Review.

    `modelling_artifacts` describes files already produced by the Modelling Agent.
    Backend/Data copies those files into the V1 export layout but does not create
    modelling outputs itself.
    """
    ensure_storage_dirs()
    created_at = created_at or utc_now_iso()
    bundle_filename = bundle_filename_for_timestamp(created_at)

    artifacts: list[ArtifactEntry] = []
    artifacts.extend(_write_backend_owned_artifacts())
    artifacts.extend(_materialize_modelling_artifacts(modelling_artifacts or []))

    if failed_models:
        artifacts.append(_write_failed_models_artifact(failed_models))

    artifacts.extend(_write_missing_artifacts(missing_artifacts or []))

    manifest_entry = ArtifactEntry(
        artifact_id="manifest",
        label="Artifact manifest",
        category="manifest",
        model_id=None,
        output_type="artifact_manifest",
        format="json",
        path="manifest.json",
        status="available",
        reason=None,
        included_in_download_all=True,
        individual_download_enabled=True,
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "bundle_filename": bundle_filename,
        "download_all": {
            "format": ZIP_FORMAT,
            "path": bundle_filename,
            "enabled": True,
            "reason": None,
        },
        "artifacts": [entry.to_dict() for entry in [*artifacts, manifest_entry]],
    }
    write_json(MODEL_OUTPUT_MANIFEST_FILE, manifest)

    try:
        bundle_path = create_download_all_bundle(manifest)
        manifest["download_all"]["path"] = Path(bundle_path).name
        write_json(MODEL_OUTPUT_MANIFEST_FILE, manifest)
        return ExportBundleResult(
            ok=True,
            manifest_path=str(MODEL_OUTPUT_MANIFEST_FILE),
            bundle_path=bundle_path,
            bundle_filename=bundle_filename,
            download_all_enabled=True,
            reason=None,
            manifest=manifest,
        )
    except OSError as exc:
        logger.warning("Download bundle creation failed: %s", exc)
        manifest["download_all"] = {
            "format": ZIP_FORMAT,
            "path": None,
            "enabled": False,
            "reason": "Download bundle could not be created. Individual available artifacts may still be downloaded.",
        }
        write_json(MODEL_OUTPUT_MANIFEST_FILE, manifest)
        return ExportBundleResult(
            ok=False,
            manifest_path=str(MODEL_OUTPUT_MANIFEST_FILE),
            bundle_path=None,
            bundle_filename=bundle_filename,
            download_all_enabled=False,
            reason=manifest["download_all"]["reason"],
            manifest=manifest,
        )


def get_export_manifest() -> dict[str, Any] | None:
    """Return the stored export manifest, if present."""
    manifest = read_json(MODEL_OUTPUT_MANIFEST_FILE, default=None)
    return manifest if isinstance(manifest, dict) else None


def get_individual_download_metadata(artifact_id: str) -> dict[str, Any]:
    """Return metadata needed for one frontend individual-download control."""
    manifest = get_export_manifest()
    if not manifest:
        return {
            "ok": False,
            "enabled": False,
            "reason": "No export manifest is available for this run.",
            "artifact": None,
            "path": None,
        }

    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict) or artifact.get("artifact_id") != artifact_id:
            continue
        enabled = bool(artifact.get("individual_download_enabled"))
        relative_path = artifact.get("path")
        resolved_path = _resolve_output_path(relative_path) if enabled and relative_path else None
        return {
            "ok": enabled and resolved_path is not None and resolved_path.exists(),
            "enabled": enabled,
            "reason": artifact.get("reason"),
            "artifact": artifact,
            "path": str(resolved_path) if resolved_path and resolved_path.exists() else None,
        }

    return {
        "ok": False,
        "enabled": False,
        "reason": "This artifact was not generated for this run.",
        "artifact": None,
        "path": None,
    }


def get_download_all_metadata() -> dict[str, Any]:
    """Return metadata for the Frontend `Download All` control."""
    manifest = get_export_manifest()
    if not manifest:
        return {
            "ok": False,
            "enabled": False,
            "reason": "No export manifest is available for this run.",
            "path": None,
            "filename": None,
        }

    download_all = manifest.get("download_all", {})
    enabled = bool(download_all.get("enabled")) if isinstance(download_all, dict) else False
    relative_path = download_all.get("path") if isinstance(download_all, dict) else None
    bundle_path = MODEL_OUTPUTS_DIR / str(relative_path) if enabled and relative_path else None
    exists = bool(bundle_path and bundle_path.exists())
    return {
        "ok": enabled and exists,
        "enabled": enabled and exists,
        "reason": None if enabled and exists else download_all.get("reason"),
        "path": str(bundle_path) if exists else None,
        "filename": manifest.get("bundle_filename"),
    }


def create_download_all_bundle(manifest: dict[str, Any] | None = None) -> str:
    """Create the Download All zip from available manifest artifacts."""
    ensure_storage_dirs()
    manifest = manifest or get_export_manifest()
    if not manifest:
        raise FileNotFoundError("No export manifest is available.")

    bundle_filename = str(manifest["bundle_filename"])
    bundle_path = MODEL_OUTPUTS_DIR / bundle_filename

    with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
        for artifact in manifest.get("artifacts", []):
            if not _should_include_in_bundle(artifact):
                continue
            relative_path = artifact.get("path")
            if not isinstance(relative_path, str):
                continue
            source_path = _resolve_output_path(relative_path)
            if not source_path.exists():
                logger.warning("Skipping missing bundle artifact %s", relative_path)
                continue
            archive.write(source_path, arcname=relative_path)

    return str(bundle_path)


def bundle_filename_for_timestamp(timestamp: str | None = None) -> str:
    """Return `allocadabra-results-YYYYMMDD-HHMM.zip` for an ISO timestamp."""
    dt = _parse_timestamp(timestamp) if timestamp else datetime.now(tz=timezone.utc)
    return f"{BUNDLE_FILENAME_PREFIX}-{dt.strftime('%Y%m%d-%H%M')}.zip"


def _write_backend_owned_artifacts() -> list[ArtifactEntry]:
    state = read_json(ACTIVE_WORKFLOW_FILE, default={})
    if not isinstance(state, dict):
        state = {}

    user_inputs_path = MODEL_OUTPUTS_DIR / "user-inputs.json"
    write_json(user_inputs_path, state.get("user_inputs", {}))
    entries = [
        ArtifactEntry(
            artifact_id="user_inputs",
            label="User inputs",
            category="general",
            model_id=None,
            output_type="user_inputs",
            format="json",
            path="user-inputs.json",
            status="available",
            reason=None,
            included_in_download_all=True,
            individual_download_enabled=True,
        )
    ]

    plan = state.get("modelling_plan", {})
    plan_markdown = plan.get("markdown") if isinstance(plan, dict) else None
    plan_confirmed = isinstance(plan, dict) and plan.get("status") == "confirmed"
    if plan_confirmed and isinstance(plan_markdown, str) and plan_markdown.strip():
        plan_path = MODEL_OUTPUTS_DIR / "modelling-plan.md"
        plan_path.write_text(plan_markdown, encoding="utf-8")
        entries.append(
            ArtifactEntry(
                artifact_id="modelling_plan",
                label="Accepted modelling plan",
                category="general",
                model_id=None,
                output_type="modelling_plan",
                format="md",
                path="modelling-plan.md",
                status="available",
                reason=None,
                included_in_download_all=True,
                individual_download_enabled=True,
            )
        )
    else:
        entries.append(
            _missing_entry(
                artifact_id="modelling_plan",
                label="Accepted modelling plan",
                output_type="modelling_plan",
                reason="The accepted modelling plan was not available for this run.",
                required=True,
            )
        )

    return entries


def _materialize_modelling_artifacts(rows: list[dict[str, Any]]) -> list[ArtifactEntry]:
    entries: list[ArtifactEntry] = []
    for row in rows:
        try:
            entry = _artifact_entry_from_modelling_row(row)
        except ValueError as exc:
            logger.warning("Skipping invalid modelling artifact descriptor: %s", exc)
            continue

        if entry.status == "missing":
            entries.append(
                _missing_entry(
                    artifact_id=entry.artifact_id,
                    label=entry.label,
                    output_type=entry.output_type,
                    reason=entry.reason or "This artifact was not generated for this run.",
                    model_id=entry.model_id,
                    required=False,
                )
            )
            continue

        source_path = _source_path_for_modelling_row(row)
        if entry.status != "available":
            entries.append(entry)
            continue

        if not source_path.exists():
            entries.append(
                _entry_with_status(
                    entry,
                    status="failed",
                    reason="This artifact was expected but the generated file was not found.",
                    path=None,
                )
            )
            continue

        if _is_excluded_source_path(source_path):
            entries.append(
                _entry_with_status(
                    entry,
                    status="disabled",
                    reason="This source file is excluded from V1 exports.",
                    path=None,
                )
            )
            continue

        destination = _resolve_output_path(str(entry.path))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != destination.resolve():
            shutil.copy2(source_path, destination)
        entries.append(entry)

    return entries


def _write_failed_models_artifact(failed_models: list[dict[str, Any]]) -> ArtifactEntry:
    path = MODEL_OUTPUTS_DIR / "failed-models.json"
    write_json(path, {"failed_models": failed_models})
    return ArtifactEntry(
        artifact_id="failed_models",
        label="Failed model reasons",
        category="failure",
        model_id=None,
        output_type="failed_models",
        format="json",
        path="failed-models.json",
        status="available",
        reason=None,
        included_in_download_all=True,
        individual_download_enabled=True,
    )


def _write_missing_artifacts(rows: list[dict[str, Any]]) -> list[ArtifactEntry]:
    return [
        _missing_entry(
            artifact_id=str(row.get("artifact_id", "")),
            label=str(row.get("label", "Missing artifact")),
            output_type=str(row.get("output_type", "missing_artifact")),
            reason=str(row.get("reason", "This artifact was not generated for this run.")),
            model_id=_optional_str(row.get("model_id")),
            required=bool(row.get("required", False)),
        )
        for row in rows
        if row.get("artifact_id")
    ]


def _missing_entry(
    *,
    artifact_id: str,
    label: str,
    output_type: str,
    reason: str,
    model_id: str | None = None,
    required: bool = False,
) -> ArtifactEntry:
    safe_artifact_id = _safe_artifact_id(artifact_id)
    placeholder_path = f"{MISSING_ARTIFACT_PATH_PREFIX}/{safe_artifact_id}.txt"
    placeholder_file = _resolve_output_path(placeholder_path)
    placeholder_file.parent.mkdir(parents=True, exist_ok=True)
    placeholder_file.write_text(reason + "\n", encoding="utf-8")

    return ArtifactEntry(
        artifact_id=safe_artifact_id,
        label=label,
        category="missing",
        model_id=model_id,
        output_type=output_type,
        format="txt",
        path=placeholder_path,
        status="missing" if not required else "failed",
        reason=reason,
        included_in_download_all=True,
        individual_download_enabled=False,
    )


def _artifact_entry_from_modelling_row(row: dict[str, Any]) -> ArtifactEntry:
    artifact_id = _required_str(row, "artifact_id")
    label = _required_str(row, "label")
    output_type = _required_str(row, "output_type")
    fmt = _artifact_format(_required_str(row, "format"))
    model_id = _optional_str(row.get("model_id"))
    category = _artifact_category(str(row.get("category") or ("model" if model_id else "general")))
    status = _artifact_status(str(row.get("status") or "available"))
    reason = _optional_str(row.get("reason"))
    bundle_path = _bundle_path_for_artifact(row, artifact_id, fmt, category, model_id)

    if status != "available" and not reason:
        reason = "This artifact was not generated for this run."

    return ArtifactEntry(
        artifact_id=_safe_artifact_id(artifact_id),
        label=label,
        category=category,
        model_id=model_id,
        output_type=output_type,
        format=fmt,
        path=bundle_path if status == "available" else None,
        status=status,
        reason=reason,
        included_in_download_all=bool(row.get("included_in_download_all", True)),
        individual_download_enabled=bool(
            row.get("individual_download_enabled", status == "available")
        ),
    )


def _bundle_path_for_artifact(
    row: dict[str, Any],
    artifact_id: str,
    fmt: ArtifactFormat,
    category: ArtifactCategory,
    model_id: str | None,
) -> str:
    explicit_path = _optional_str(row.get("bundle_path"))
    if explicit_path:
        return _validate_relative_bundle_path(explicit_path)

    relative_path = _optional_str(row.get("path"))
    if relative_path and not Path(relative_path).is_absolute():
        return _validate_relative_bundle_path(relative_path)

    filename = _optional_str(row.get("filename")) or f"{_safe_filename(artifact_id)}.{fmt}"
    if category == "model":
        if not model_id:
            raise ValueError("model artifacts require model_id")
        return _validate_relative_bundle_path(f"{MODEL_ARTIFACT_PATH_PREFIX}/{model_id}/{filename}")
    return _validate_relative_bundle_path(filename)


def _source_path_for_modelling_row(row: dict[str, Any]) -> Path:
    explicit_source = _optional_str(row.get("source_path"))
    if explicit_source:
        return Path(explicit_source)

    generated_path = _optional_str(row.get("path"))
    if not generated_path:
        return Path("")
    if Path(generated_path).is_absolute():
        return Path(generated_path)
    return _resolve_output_path(generated_path)


def _resolve_output_path(relative_path: str | None) -> Path:
    if not relative_path:
        raise ValueError("Artifact path is required.")
    relative = Path(_validate_relative_bundle_path(relative_path))
    return MODEL_OUTPUTS_DIR / relative


def _validate_relative_bundle_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Invalid export artifact path: {path}")
    return candidate.as_posix()


def _is_excluded_source_path(path: Path) -> bool:
    resolved = path.resolve()
    excluded_roots = {
        COINGECKO_CACHE_DIR.resolve(),
        ACTIVE_WORKFLOW_FILE.resolve(),
    }
    return any(resolved == root or root in resolved.parents for root in excluded_roots)


def _entry_with_status(
    entry: ArtifactEntry,
    *,
    status: ArtifactStatus,
    reason: str,
    path: str | None,
) -> ArtifactEntry:
    return ArtifactEntry(
        artifact_id=entry.artifact_id,
        label=entry.label,
        category=entry.category,
        model_id=entry.model_id,
        output_type=entry.output_type,
        format=entry.format,
        path=path,
        status=status,
        reason=reason,
        included_in_download_all=entry.included_in_download_all,
        individual_download_enabled=False,
    )


def _should_include_in_bundle(artifact: Any) -> bool:
    return (
        isinstance(artifact, dict)
        and bool(artifact.get("included_in_download_all"))
        and artifact.get("status") in {"available", "missing"}
        and isinstance(artifact.get("path"), str)
    )


def _required_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def _artifact_category(value: str) -> ArtifactCategory:
    allowed = {"general", "model", "manifest", "missing", "failure"}
    if value not in allowed:
        raise ValueError(f"Unsupported artifact category: {value}")
    return value  # type: ignore[return-value]


def _artifact_format(value: str) -> ArtifactFormat:
    allowed = {"json", "md", "csv", "png", "txt"}
    if value not in allowed:
        raise ValueError(f"Unsupported artifact format: {value}")
    return value  # type: ignore[return-value]


def _artifact_status(value: str) -> ArtifactStatus:
    allowed = {"available", "missing", "failed", "disabled"}
    if value not in allowed:
        raise ValueError(f"Unsupported artifact status: {value}")
    return value  # type: ignore[return-value]


def _safe_artifact_id(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip()).strip("_").lower()
    if not slug:
        raise ValueError("artifact_id must contain at least one safe character")
    return slug


def _safe_filename(value: str) -> str:
    return _safe_artifact_id(value).replace("_", "-")


def _parse_timestamp(timestamp: str) -> datetime:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid export timestamp %s; using current UTC time", timestamp)
        return datetime.now(tz=timezone.utc)
