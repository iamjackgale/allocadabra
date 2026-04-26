"""Review phase UI built from the export manifest and modelling artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.ai.data_api import generate_review_opening
from app.storage import return_to_configure_from_review, start_new_model
from frontend.chat import render_chat_panel
from frontend.constants import (
    CHART_SECTION_DOWNLOAD_FORMAT,
    METRIC_SPECS,
    MODEL_LABELS,
    PER_MODEL_REVIEW_SECTIONS,
    REVIEW_SECTIONS,
    SECTION_HELP,
)
from frontend.data import (
    allocation_weights_matrix,
    artifacts_from_manifest,
    build_ranking_summary,
    failed_models_from_manifest,
    get_artifact_file_info,
    get_download_all_payload,
    get_review_manifest,
    load_artifact_dataframe,
    load_artifact_text,
    metric_display_value,
    metric_row_styles,
    missing_artifact_reason,
    model_output_dataframe,
    preferred_download_artifact,
    successful_model_ids,
    summary_for_review_ai,
    summary_metrics_matrix,
)
from frontend.runtime import (
    clear_confirmation,
    confirmation_state,
    current_review_model_id,
    current_review_section,
    note_review_opening_attempt,
    request_confirmation,
    reset_review_ui,
    review_opening_attempted_for,
    set_chat_feedback,
    set_review_model_id,
    set_review_section,
)


def render_review_page(workflow: dict[str, Any]) -> None:
    """Render the Review phase with chat plus model review controls."""
    manifest = get_review_manifest()
    artifacts = artifacts_from_manifest(manifest)
    failed_models = failed_models_from_manifest(artifacts)
    model_order = successful_model_ids(artifacts, workflow, failed_models)
    raw_summary, summary_matrix = summary_metrics_matrix(artifacts, model_order)
    ranking_summary = build_ranking_summary(
        raw_summary,
        objective=workflow.get("user_inputs", {}).get("treasury_objective"),
        risk_appetite=workflow.get("user_inputs", {}).get("risk_appetite"),
        failed_models=failed_models,
    )
    model_output_summary = summary_for_review_ai(
        raw_summary,
        model_order=model_order,
        failed_models=failed_models,
    )

    selected_section = current_review_section()
    selected_model_id = _ensure_selected_model(model_order, failed_models)
    visible_context, detailed_context = _review_ai_context(
        artifacts=artifacts,
        selected_section=selected_section,
        selected_model_id=selected_model_id,
        summary_matrix=summary_matrix,
        raw_summary=raw_summary,
        failed_models=failed_models,
        model_order=model_order,
    )

    opened = _ensure_review_opening(
        manifest_key=str(workflow.get("model_outputs", {}).get("manifest_path") or ""),
        ranking_summary=ranking_summary,
        model_output_summary=model_output_summary,
        has_messages=bool(workflow.get("chat_sessions", {}).get("review")),
    )
    if opened:
        st.rerun()

    chat_col, review_col = st.columns([0.92, 1.08], gap="large")
    with chat_col:
        render_chat_panel(
            mode="review",
            workflow=workflow,
            model_output_summary=model_output_summary,
            visible_context=visible_context,
            detailed_context=detailed_context,
        )

    objective = workflow.get("user_inputs", {}).get("treasury_objective") or "Not set"
    risk = workflow.get("user_inputs", {}).get("risk_appetite") or "Not set"
    with review_col:
        st.markdown('<div class="alloca-phase">REVIEW</div>', unsafe_allow_html=True)
        with st.container(height=900, border=True):
            st.markdown(
                "Compare model outputs against your selected objective and risk appetite. Green/yellow/red rankings compare these models within this run only."
            )
            _render_review_controls(
                artifacts=artifacts,
                model_order=model_order,
                failed_models=failed_models,
                selected_section=selected_section,
                objective=objective,
                risk=risk,
            )
            if failed_models:
                for failed in failed_models:
                    st.error(f"{failed.get('label', failed.get('model_id', 'Model'))}: {failed.get('reason', 'Failed during modelling.')}")

            _render_sections(
                workflow=workflow,
                artifacts=artifacts,
                model_order=model_order,
                selected_model_id=selected_model_id,
                selected_section=selected_section,
                raw_summary=raw_summary,
                summary_matrix=summary_matrix,
            )
            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("Return To Configure", width="stretch"):
                    request_confirmation(
                        "return_to_configure",
                        "This returns to Configuration and clears the current outputs and Review chat. Download results first if you want to keep them.",
                    )
            with action_cols[1]:
                if st.button("Start New Model", width="stretch"):
                    request_confirmation(
                        "start_new_model",
                        "This clears the current configuration, outputs, and Review chat. Download results first if you want to keep them.",
                    )
            _render_review_confirmation()


def _render_review_controls(
    *,
    artifacts: list[dict[str, Any]],
    model_order: list[str],
    failed_models: list[dict[str, Any]],
    selected_section: str,
    objective: str,
    risk: str,
) -> None:
    cols = st.columns([1.1, 1])
    download_all = get_download_all_payload()
    model_labels = _model_selector_labels(model_order, failed_models)
    with cols[0]:
        st.caption(f"Ranked for: {objective} · {risk} risk appetite")
        if download_all.get("ok") and download_all.get("path"):
            path = str(download_all["path"])
            st.download_button(
                "Download All",
                data=Path(path).read_bytes(),
                file_name=str(download_all.get("filename") or "allocadabra-results.zip"),
                mime="application/zip",
                width="stretch",
            )
        else:
            st.button(
                "Download All",
                disabled=True,
                help=str(download_all.get("reason") or "Download bundle unavailable."),
                width="stretch",
            )

    with cols[1]:
        if model_labels:
            chosen_label = st.selectbox(
                "Selected Model",
                options=list(model_labels),
                index=list(model_labels).index(_current_model_label(model_labels)),
                key="review_model_selector",
                disabled=selected_section not in PER_MODEL_REVIEW_SECTIONS,
            )
            set_review_model_id(model_labels[chosen_label])
        else:
            st.selectbox(
                "Selected Model",
                options=["No successful models"],
                index=0,
                disabled=True,
                key="review_model_selector_empty",
            )


def _render_sections(
    *,
    workflow: dict[str, Any],
    artifacts: list[dict[str, Any]],
    model_order: list[str],
    selected_model_id: str | None,
    selected_section: str,
    raw_summary: pd.DataFrame | None,
    summary_matrix: pd.DataFrame | None,
) -> None:
    for section_id, label in REVIEW_SECTIONS:
        with st.container(border=True):
            active = selected_section == section_id
            if st.button(
                label,
                key=f"section_{section_id}",
                type="primary" if active else "secondary",
                width="stretch",
                help=SECTION_HELP[section_id],
            ):
                set_review_section(section_id)
                st.rerun()

            if not active:
                continue

            st.caption(SECTION_HELP[section_id])
            if section_id == "summary_metrics":
                _render_summary_metrics(artifacts, raw_summary, summary_matrix)
            elif section_id == "allocation_weights":
                _render_allocation_weights(artifacts, model_order)
            elif section_id == "modelling_plan":
                _render_modelling_plan(artifacts)
            else:
                _render_model_section(
                    artifacts=artifacts,
                    section_id=section_id,
                    selected_model_id=selected_model_id,
                )


def _render_summary_metrics(
    artifacts: list[dict[str, Any]],
    raw_summary: pd.DataFrame | None,
    summary_matrix: pd.DataFrame | None,
) -> None:
    if raw_summary is None or summary_matrix is None or summary_matrix.empty:
        st.info("Summary metrics were not generated for this run.")
        return

    styles = summary_matrix.copy()
    styler = styles.style
    for metric_key, spec in METRIC_SPECS.items():
        label = spec["label"]
        if label in summary_matrix.index:
            styler = styler.apply(
                metric_row_styles,
                axis=1,
                subset=pd.IndexSlice[[label], :],
                better=spec["better"],
            )
    styler = styler.format(metric_display_value)
    st.dataframe(styler, width="stretch", height=520)

    with st.expander("Metric guide"):
        for spec in METRIC_SPECS.values():
            st.markdown(f"**{spec['label']}**: {spec['description']}")

    _render_manifest_download(
        preferred_download_artifact(
            artifacts,
            output_type="summary_metrics",
        )
    )


def _render_allocation_weights(
    artifacts: list[dict[str, Any]],
    model_order: list[str],
) -> None:
    table = allocation_weights_matrix(artifacts, model_order)
    if table is None or table.empty:
        st.info("Allocation weights were not generated for this run.")
        return

    st.dataframe(table, width="stretch", hide_index=True)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download section",
        data=csv_bytes,
        file_name="allocation-weights-comparison.csv",
        mime="text/csv",
        width="content",
    )


def _render_modelling_plan(artifacts: list[dict[str, Any]]) -> None:
    artifact = next((row for row in artifacts if row.get("output_type") == "modelling_plan"), None)
    if not artifact:
        st.info("Accepted modelling plan was not generated for this run.")
        return
    text = load_artifact_text(str(artifact["artifact_id"]))
    if not text:
        st.info("Accepted modelling plan was not generated for this run.")
        return
    st.markdown(text)
    _render_manifest_download(artifact)


def _render_model_section(
    *,
    artifacts: list[dict[str, Any]],
    section_id: str,
    selected_model_id: str | None,
) -> None:
    if not selected_model_id:
        st.info("No successful model is available for this section.")
        return

    df = model_output_dataframe(artifacts, model_id=selected_model_id, output_type=section_id)
    download_artifact = preferred_download_artifact(
        artifacts,
        output_type=section_id,
        model_id=selected_model_id,
    )
    if df is None and not download_artifact:
        missing = next(
            (
                artifact
                for artifact in artifacts
                if artifact.get("output_type") == section_id and artifact.get("model_id") == selected_model_id
            ),
            None,
        )
        st.button(
            "Download section",
            disabled=True,
            help=missing_artifact_reason(missing),
            width="content",
        )
        st.info(missing_artifact_reason(missing))
        return

    if section_id == "dendrogram":
        _render_dendrogram(download_artifact)
    else:
        fig = _figure_for_section(section_id, df, selected_model_id)
        if fig is not None:
            st.plotly_chart(fig, width="stretch")
        elif download_artifact and str(download_artifact.get("format")) == "png":
            metadata = get_artifact_file_info(str(download_artifact["artifact_id"]))
            path = metadata.get("path")
            if metadata.get("ok") and isinstance(path, str):
                st.image(path, width="stretch")
    _render_manifest_download(download_artifact)


def _render_dendrogram(download_artifact: dict[str, Any] | None) -> None:
    if not download_artifact:
        st.info("This artifact was not generated for this run.")
        return
    metadata = get_artifact_file_info(str(download_artifact["artifact_id"]))
    path = metadata.get("path")
    if metadata.get("ok") and isinstance(path, str):
        st.image(path, width="stretch")
    else:
        st.info("This artifact was not generated for this run.")


def _figure_for_section(
    section_id: str,
    df: pd.DataFrame | None,
    model_id: str,
) -> go.Figure | None:
    if df is None or df.empty:
        return None

    if section_id == "allocation_over_time":
        value_columns = [column for column in df.columns if column != "date"]
        fig = px.area(df, x="date", y=value_columns, title=f"{MODEL_LABELS[model_id]} allocation over time")
        fig.update_layout(yaxis_title="Weight")
        return fig
    if section_id == "cumulative_performance":
        return px.line(df, x="date", y="cumulative_return", title=f"{MODEL_LABELS[model_id]} cumulative performance")
    if section_id == "drawdown":
        return px.line(df, x="date", y="drawdown", title=f"{MODEL_LABELS[model_id]} drawdown")
    if section_id == "rolling_volatility":
        return px.line(df, x="date", y="rolling_volatility", title=f"{MODEL_LABELS[model_id]} rolling volatility")
    if section_id == "risk_contribution":
        return px.bar(df, x="asset", y="risk_contribution", title=f"{MODEL_LABELS[model_id]} risk contribution")
    if section_id == "efficient_frontier":
        value_columns = [column for column in df.columns if column != "frontier_point"]
        return px.line(df, x="frontier_point", y=value_columns, title=f"{MODEL_LABELS[model_id]} efficient frontier")
    return None


def _render_manifest_download(artifact: dict[str, Any] | None) -> None:
    if not artifact:
        st.button(
            "Download section",
            disabled=True,
            help="This artifact was not generated for this run.",
            width="content",
        )
        return

    metadata = get_artifact_file_info(str(artifact["artifact_id"]))
    path = metadata.get("path")
    if not metadata.get("ok") or not isinstance(path, str):
        st.button(
            "Download section",
            disabled=True,
            help=str(metadata.get("reason") or "This artifact was not generated for this run."),
            width="content",
        )
        return

    st.download_button(
        "Download section",
        data=Path(path).read_bytes(),
        file_name=Path(path).name,
        mime=_mime_type_for(path),
        width="content",
    )


def _ensure_review_opening(
    *,
    manifest_key: str,
    ranking_summary: dict[str, Any],
    model_output_summary: dict[str, Any],
    has_messages: bool,
) -> bool:
    """Generate the review opening message if not yet present. Returns True if generated."""
    if has_messages or review_opening_attempted_for() == manifest_key:
        return False
    result = generate_review_opening(
        ranking_summary=ranking_summary,
        model_output_summary=model_output_summary,
    )
    note_review_opening_attempt(manifest_key)
    if not result.get("ok"):
        set_chat_feedback(
            "review",
            str(result.get("message", "The Review opening could not be generated.")),
        )
    return bool(result.get("ok"))


def _review_ai_context(
    *,
    artifacts: list[dict[str, Any]],
    selected_section: str,
    selected_model_id: str | None,
    summary_matrix: pd.DataFrame | None,
    raw_summary: pd.DataFrame | None,
    failed_models: list[dict[str, Any]],
    model_order: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    visible_context: dict[str, Any] = {
        "visible_section": selected_section,
        "visible_output_type": selected_section,
        "open_expander_ids": [selected_section],
    }
    detailed_context: dict[str, Any] = {
        "warnings": failed_models,
    }

    if raw_summary is not None:
        detailed_context["summary_metrics"] = raw_summary.to_dict("records")
    if summary_matrix is not None and selected_section == "summary_metrics":
        visible_context["chart_table_headers"] = list(summary_matrix.columns)
        visible_context["visible_table_data"] = summary_matrix.reset_index().to_dict("records")

    if selected_model_id:
        visible_context["selected_model_id"] = selected_model_id
        model_payload: dict[str, Any] = {}
        for output_type in {"allocation_weights", selected_section}:
            df = model_output_dataframe(artifacts, model_id=selected_model_id, output_type=output_type)
            if df is not None:
                model_payload[output_type] = df.to_dict("records")
                if output_type == selected_section:
                    visible_context["chart_table_headers"] = list(df.columns)
                    visible_context["visible_table_data"] = df.to_dict("records")
        if model_payload:
            detailed_context["models"] = {selected_model_id: model_payload}
    return visible_context, detailed_context


def _model_selector_labels(
    model_order: list[str],
    failed_models: list[dict[str, Any]],
) -> dict[str, str]:
    labels = {MODEL_LABELS[model_id]: model_id for model_id in model_order}
    for failed in failed_models:
        model_id = str(failed.get("model_id", ""))
        label = str(failed.get("label") or MODEL_LABELS.get(model_id, model_id))
        labels[f"{label} (failed)"] = model_id
    return labels


def _ensure_selected_model(
    model_order: list[str],
    failed_models: list[dict[str, Any]],
) -> str | None:
    options = _model_selector_labels(model_order, failed_models)
    current = current_review_model_id()
    if current in options.values():
        return current
    next_model = model_order[0] if model_order else (failed_models[0].get("model_id") if failed_models else None)
    set_review_model_id(str(next_model) if next_model else None)
    return str(next_model) if next_model else None


def _current_model_label(model_labels: dict[str, str]) -> str:
    if not model_labels:
        return ""
    current = current_review_model_id()
    for label, model_id in model_labels.items():
        if model_id == current:
            return label
    return next(iter(model_labels))


def _render_review_confirmation() -> None:
    confirmation = confirmation_state()
    if not confirmation:
        return
    st.warning(confirmation["message"])
    cols = st.columns(2)
    with cols[0]:
        if st.button("Confirm", type="primary", width="stretch"):
            action = confirmation["action"]
            clear_confirmation()
            if action == "return_to_configure":
                return_to_configure_from_review()
                reset_review_ui()
            elif action == "start_new_model":
                start_new_model()
                reset_review_ui()
            st.rerun()
    with cols[1]:
        if st.button("Keep current outputs", width="stretch"):
            clear_confirmation()
            st.rerun()


def _mime_type_for(path: str) -> str:
    if path.endswith(".png"):
        return "image/png"
    if path.endswith(".csv"):
        return "text/csv"
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".md") or path.endswith(".txt"):
        return "text/plain"
    if path.endswith(".zip"):
        return "application/zip"
    return "application/octet-stream"
