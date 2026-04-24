"""Frontend-callable modelling app-layer contract."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.processing.models import SUPPORTED_MODELS
from app.processing.progress import (
    CancelCheck,
    ModellingCancelled,
    ProgressCallback,
    emit_progress,
    raise_if_cancelled,
)
from app.processing.runner import generate_modelling_outputs
from app.storage.data_api import (
    fetch_price_history_for_assets,
    get_active_workflow,
    validate_active_configuration,
)
from app.storage.paths import MODEL_OUTPUTS_DIR


logger = logging.getLogger(__name__)

DEFAULT_USER_ERROR = "Modelling could not be completed. Check the configuration and try again."


def run_active_modelling(
    *,
    progress_callback: ProgressCallback | None = None,
    cancel_check: CancelCheck | None = None,
    force_refresh_prices: bool = False,
    output_dir: Path = MODEL_OUTPUTS_DIR,
) -> dict[str, Any]:
    """Run modelling from the active workflow and return a frontend-safe result.

    Return shape:
    - `ok`: true when at least one selected model succeeds.
    - `successful_models`: stable model IDs that completed.
    - `failed_models`: structured per-model failure details.
    - `artifacts`: available/failed/disabled modelling artifact descriptors, excluding
      missing placeholders and Backend-owned `failed-models.json` materialization.
    - `missing_artifacts`: missing optional artifact descriptors with reasons.
    - `errors`: run-level validation, ingestion, dataset, or runtime errors.
    - `user_message`: concise user-facing status copy.
    - `progress_events`: emitted checkpoint events for the Modelling screen.

    This function deliberately does not create zip bundles, write the final export
    manifest, or move the active workflow into Review. Backend/Data owns that step.
    """
    progress_events: list[dict[str, object]] = []

    try:
        raise_if_cancelled(cancel_check, phase="validation")
        emit_progress(
            progress_callback,
            progress_events,
            phase="validation",
            status="started",
            message="Validating configuration.",
        )
        workflow = get_active_workflow()
        raise_if_cancelled(cancel_check, phase="validation")
        validation = validate_active_configuration()
        raise_if_cancelled(cancel_check, phase="validation")
        if not validation.get("valid"):
            errors = _validation_errors(validation.get("issues", []))
            emit_progress(
                progress_callback,
                progress_events,
                phase="validation",
                status="failed",
                message="Configuration needs attention before modelling can start.",
            )
            return _result(
                ok=False,
                errors=errors,
                user_message="Check the configuration before running models.",
                progress_events=progress_events,
            )

        user_inputs = workflow.get("user_inputs", {})
        selected_assets = _selected_assets(user_inputs)
        selected_models, unsupported_models = _selected_models(user_inputs)
        if unsupported_models:
            emit_progress(
                progress_callback,
                progress_events,
                phase="validation",
                status="failed",
                message="Unsupported model selections were found.",
            )
            return _result(
                ok=False,
                errors=[
                    {
                        "code": "unsupported_models",
                        "field": "selected_models",
                        "message": "Choose only supported V1 models.",
                        "model_ids": unsupported_models,
                    }
                ],
                user_message="Choose only supported V1 models before running modelling.",
                progress_events=progress_events,
            )
        plan_status = workflow.get("modelling_plan", {}).get("status")
        if plan_status != "confirmed":
            emit_progress(
                progress_callback,
                progress_events,
                phase="validation",
                status="failed",
                message="No confirmed modelling plan is available.",
            )
            return _result(
                ok=False,
                errors=[
                    {
                        "code": "modelling_plan_not_confirmed",
                        "message": "Confirm the modelling plan before running models.",
                    }
                ],
                user_message="Confirm the modelling plan before running models.",
                progress_events=progress_events,
            )

        emit_progress(
            progress_callback,
            progress_events,
            phase="validation",
            status="completed",
            message="Configuration is ready for modelling.",
        )

        raise_if_cancelled(cancel_check, phase="ingestion")
        emit_progress(
            progress_callback,
            progress_events,
            phase="ingestion",
            status="started",
            message="Loading cached price histories.",
        )
        price_response = fetch_price_history_for_assets(
            [_asset_id(asset) for asset in selected_assets],
            force_refresh=force_refresh_prices,
        )
        raise_if_cancelled(cancel_check, phase="ingestion")
        if not price_response.get("ok"):
            errors = _storage_errors(price_response.get("errors", []))
            emit_progress(
                progress_callback,
                progress_events,
                phase="ingestion",
                status="failed",
                message="One or more price histories could not be loaded.",
            )
            return _result(
                ok=False,
                errors=errors,
                user_message="Price history could not be loaded for every selected asset.",
                progress_events=progress_events,
            )
        emit_progress(
            progress_callback,
            progress_events,
            phase="ingestion",
            status="completed",
            message="Price histories are ready.",
        )

        generated = generate_modelling_outputs(
            selected_assets=selected_assets,
            price_history_by_id=price_response.get("prices", {}),
            selected_models=selected_models,
            output_dir=output_dir,
            cancel_check=cancel_check,
            progress_callback=lambda event: _relay_progress(
                progress_callback,
                progress_events,
                event,
            ),
        )

        raise_if_cancelled(cancel_check, phase="outputs")
        artifacts, missing_artifacts = _split_artifacts(generated.get("artifacts", []))
        failed_models = list(generated.get("failed_models", []))
        successful_models = list(generated.get("successful_models", []))
        raise_if_cancelled(cancel_check, phase="outputs")
        return _result(
            ok=bool(generated.get("ok")),
            successful_models=successful_models,
            failed_models=failed_models,
            artifacts=artifacts,
            missing_artifacts=missing_artifacts,
            user_message=_success_message(successful_models, failed_models),
            progress_events=progress_events,
            dataset_metadata=generated.get("dataset_metadata", {}),
            output_dir=generated.get("output_dir"),
        )
    except ModellingCancelled as exc:
        emit_progress(
            progress_callback,
            progress_events,
            phase=exc.phase,
            status="failed",
            message="Modelling was cancelled.",
        )
        return _result(
            ok=False,
            errors=[
                {
                    "code": "modelling_cancelled",
                    "message": "Modelling was cancelled.",
                }
            ],
            user_message="Modelling was cancelled.",
            progress_events=progress_events,
        )
    except Exception as exc:
        logger.exception("Active modelling run failed")
        emit_progress(
            progress_callback,
            progress_events,
            phase="outputs",
            status="failed",
            message="Modelling failed before outputs were ready.",
        )
        return _result(
            ok=False,
            errors=[_exception_error(exc)],
            user_message=DEFAULT_USER_ERROR,
            progress_events=progress_events,
        )


def modelling_contract() -> dict[str, Any]:
    """Return the stable frontend-callable modelling contract."""
    return {
        "function": "app.processing.run_active_modelling",
        "supported_model_ids": list(SUPPORTED_MODELS),
        "supports_cancellation": True,
        "cancellation": {
            "callback": "cancel_check",
            "error_code": "modelling_cancelled",
            "returns_frontend_safe_result": True,
        },
        "progress_phases": [
            "validation",
            "ingestion",
            "datasets",
            "modelling",
            "analysis",
            "outputs",
        ],
        "return_fields": [
            "ok",
            "successful_models",
            "failed_models",
            "artifacts",
            "missing_artifacts",
            "errors",
            "user_message",
            "progress_events",
            "dataset_metadata",
            "output_dir",
        ],
        "backend_handoff": {
            "modelling_artifacts": "artifacts",
            "failed_models": "failed_models",
            "missing_artifacts": "missing_artifacts",
        },
    }


def _relay_progress(
    callback: ProgressCallback | None,
    events: list[dict[str, object]],
    event: dict[str, object],
) -> None:
    events.append(event)
    if callback is not None:
        callback(event)


def _result(
    *,
    ok: bool,
    successful_models: list[str] | None = None,
    failed_models: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    missing_artifacts: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    user_message: str,
    progress_events: list[dict[str, object]],
    dataset_metadata: dict[str, Any] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "successful_models": successful_models or [],
        "failed_models": failed_models or [],
        "artifacts": artifacts or [],
        "missing_artifacts": missing_artifacts or [],
        "errors": errors or [],
        "user_message": user_message,
        "progress_events": progress_events,
        "dataset_metadata": dataset_metadata or {},
        "output_dir": output_dir,
    }


def _selected_assets(user_inputs: Any) -> list[dict[str, Any]]:
    assets = user_inputs.get("selected_assets", []) if isinstance(user_inputs, dict) else []
    return [asset for asset in assets if isinstance(asset, dict)]


def _selected_models(user_inputs: Any) -> tuple[list[str], list[str]]:
    models = user_inputs.get("selected_models", []) if isinstance(user_inputs, dict) else []
    selected = [str(model) for model in models]
    return (
        [model for model in selected if model in SUPPORTED_MODELS],
        [model for model in selected if model not in SUPPORTED_MODELS],
    )


def _asset_id(asset: dict[str, Any]) -> str:
    return str(asset.get("id", "")).strip()


def _split_artifacts(
    artifacts: list[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    available: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        if artifact.get("output_type") == "failed_models":
            continue
        if artifact.get("status") == "missing":
            missing.append(artifact)
        else:
            available.append(artifact)
    return available, missing


def _validation_errors(issues: Any) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(issues, list):
        return [{"code": "invalid_configuration", "message": "Configuration is invalid."}]
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        errors.append(
            {
                "code": str(issue.get("code", "invalid_configuration")),
                "field": issue.get("field"),
                "message": str(issue.get("message", "Configuration is invalid.")),
            }
        )
    return errors or [{"code": "invalid_configuration", "message": "Configuration is invalid."}]


def _storage_errors(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return [{"code": "price_history_unavailable", "message": "Price history is unavailable."}]
    return [
        {
            "code": str(row.get("code", "price_history_unavailable")),
            "id": row.get("id"),
            "message": str(row.get("message", "Price history is unavailable.")),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def _exception_error(exc: Exception) -> dict[str, str]:
    return {
        "code": _error_code(exc),
        "message": _friendly_exception_message(exc),
        "exception_type": type(exc).__name__,
    }


def _error_code(exc: Exception) -> str:
    name = type(exc).__name__
    if "Dataset" in name:
        return "dataset_build_failed"
    if "Model" in name:
        return "model_execution_failed"
    return "modelling_failed"


def _friendly_exception_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message or DEFAULT_USER_ERROR


def _success_message(successful_models: list[str], failed_models: list[dict[str, Any]]) -> str:
    if successful_models and failed_models:
        return "Some models completed successfully. Failed models are shown with reasons."
    if successful_models:
        return "Modelling completed successfully."
    return "No models completed successfully. You can retry the run or cancel back to Configuration."
