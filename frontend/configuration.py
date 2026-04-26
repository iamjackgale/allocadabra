"""Configuration phase UI and active workflow input controls."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.ai.data_api import generate_modelling_plan
from app.ai.models import DEFAULT_MODEL_IDS
from app.storage import abandon_generated_plan, list_token_options, reset_configuration, update_active_inputs, validate_active_configuration
from frontend.constants import (
    MODEL_HELP,
    MODEL_LABELS,
    RISK_APPETITE_HELP,
    RISK_APPETITES,
    TREASURY_OBJECTIVE_HELP,
    TREASURY_OBJECTIVES,
)
from frontend.runtime import (
    bump_token_refresh_nonce,
    clear_confirmation,
    confirmation_state,
    request_confirmation,
    reset_review_ui,
    set_chat_feedback,
    start_modelling_run,
    token_refresh_nonce,
)


def render_configuration_panel(workflow: dict[str, Any]) -> None:
    """Render the full Configuration workflow pane."""
    st.markdown('<div class="alloca-phase">MODEL CONFIGURATION</div>', unsafe_allow_html=True)

    inputs = dict(workflow.get("user_inputs", {}))
    selected_models = list(inputs.get("selected_models") or DEFAULT_MODEL_IDS)
    if not inputs.get("selected_models"):
        inputs["selected_models"] = selected_models
        update_active_inputs({"selected_models": selected_models})

    plan = workflow.get("modelling_plan", {})
    if plan.get("status") in {"generated", "confirmed"} and plan.get("markdown"):
        render_plan_preview(workflow)
    else:
        render_configuration_form(workflow)


def render_configuration_form(workflow: dict[str, Any]) -> None:
    """Render the editable configuration form."""
    inputs = dict(workflow.get("user_inputs", {}))
    selected_assets = list(inputs.get("selected_assets", []))
    objective = inputs.get("treasury_objective")
    risk_appetite = inputs.get("risk_appetite")
    selected_models = list(inputs.get("selected_models") or DEFAULT_MODEL_IDS)
    constraints = dict(inputs.get("constraints") or {})
    issues = _issues_by_field(validate_active_configuration().get("issues", []))

    _render_asset_selector(selected_assets)
    _render_selected_assets(selected_assets)
    _render_field_issues(issues, "selected_assets")

    st.markdown("##### Treasury Objective")
    objective = _render_single_choice_cards(
        key_prefix="objective",
        options=TREASURY_OBJECTIVES,
        selected_value=objective,
        help_lookup=TREASURY_OBJECTIVE_HELP,
    )
    _render_field_issues(issues, "treasury_objective")

    st.markdown("##### Risk Appetite")
    risk_appetite = _render_single_choice_cards(
        key_prefix="risk",
        options=RISK_APPETITES,
        selected_value=risk_appetite,
        help_lookup=RISK_APPETITE_HELP,
    )
    _render_field_issues(issues, "risk_appetite")

    st.markdown("##### Selected Models")
    selected_models = _render_model_cards(selected_models)
    if selected_models != inputs.get("selected_models"):
        update_active_inputs({"selected_models": selected_models})
    _render_field_issues(issues, "selected_models")

    with st.expander("Optional Constraints"):
        constraints = _render_constraints(selected_assets, constraints, issues)

    updated_inputs = {
        "selected_assets": selected_assets,
        "treasury_objective": objective,
        "risk_appetite": risk_appetite,
        "selected_models": selected_models,
        "constraints": constraints,
    }
    if updated_inputs != inputs:
        update_active_inputs(updated_inputs)

    if issues:
        st.markdown('<div class="alloca-note">Current deterministic validation issues are shown below the relevant controls and will be checked again before plan generation.</div>', unsafe_allow_html=True)
        _render_issue_summary(issues)

    action_cols = st.columns([1.3, 1])
    with action_cols[0]:
        if st.button("Generate Plan", type="primary", width="stretch"):
            _handle_generate_plan(updated_inputs)
    with action_cols[1]:
        if st.button("Reset Configuration", width="stretch"):
            request_confirmation(
                "reset_configuration",
                "This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.",
            )

    _render_confirmation_panel()


def render_plan_preview(workflow: dict[str, Any]) -> None:
    """Render the generated-plan confirmation state."""
    plan = workflow.get("modelling_plan", {})
    st.markdown("#### Confirm The Modelling Plan")
    st.markdown(str(plan.get("markdown", "")))

    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Run", type="primary", width="stretch"):
            start_modelling_run()
            st.rerun()
    with action_cols[1]:
        if st.button("Regenerate", width="stretch"):
            _handle_generate_plan(dict(workflow.get("user_inputs", {})))
    with action_cols[2]:
        if st.button("Reconfigure", width="stretch"):
            request_confirmation(
                "reconfigure_plan",
                "This abandons the current plan and returns to Configuration with your previous selections still filled in.",
            )

    if st.button("Reset Configuration", width="stretch"):
        request_confirmation(
            "reset_configuration",
            "This clears your selected assets, preferences, constraints, generated plan, chats, and outputs.",
        )

    _render_confirmation_panel()


def _handle_generate_plan(active_inputs: dict[str, Any]) -> None:
    validation = validate_active_configuration()
    if not validation.get("valid"):
        set_chat_feedback(
            "configuration",
            _validation_summary(validation.get("issues", [])),
        )
        return

    with st.spinner("Generating modelling plan..."):
        result = generate_modelling_plan(active_inputs=active_inputs)

    if result.get("ok"):
        set_chat_feedback("configuration", None)
        st.rerun()

    issues = result.get("issues", [])
    if issues:
        set_chat_feedback(
            "configuration",
            "The configuration still needs attention before the AI plan can be used:\n- "
            + "\n- ".join(str(issue) for issue in issues),
        )
    else:
        set_chat_feedback(
            "configuration",
            str(result.get("message", "The modelling plan could not be generated.")),
        )


def _render_asset_selector(selected_assets: list[dict[str, Any]]) -> None:
    st.markdown("##### Select Assets")
    search_term = st.text_input(
        "Select Assets",
        key="asset_search_term",
        placeholder="Search CoinGecko symbol or name",
        label_visibility="collapsed",
    )
    try:
        tokens = list_token_options(
            search_term=search_term or None,
            force_refresh=bool(token_refresh_nonce()),
        ).get("tokens", [])
    except Exception as exc:
        st.error(f"Token list could not be loaded. {exc}")
        retry_cols = st.columns(2)
        with retry_cols[0]:
            if st.button("Check again", width="stretch"):
                bump_token_refresh_nonce()
                st.rerun()
        with retry_cols[1]:
            st.caption("If this keeps failing, reload the app and check the CoinGecko API key.")
        return

    if search_term and not tokens:
        st.warning("No assets matched the current search.")
        if st.button("Refresh token list", width="content"):
            bump_token_refresh_nonce()
            st.rerun()
        return

    option_map = {
        _asset_option_label(token, selected_assets): token
        for token in tokens[:250]
    }
    option_labels = [""] + list(option_map)
    selected_label = st.selectbox(
        "Add asset",
        options=option_labels,
        format_func=lambda label: "Select an asset" if not label else label,
        key="asset_option_select",
        label_visibility="collapsed",
    )
    add_disabled = not selected_label or len(selected_assets) >= 10
    add_cols = st.columns([1.4, 1])
    with add_cols[0]:
        st.caption(f"Selected assets: {len(selected_assets)} / 10. Minimum to generate a plan: 2.")
    with add_cols[1]:
        if st.button("Add Asset", width="stretch", disabled=add_disabled):
            asset = option_map.get(selected_label)
            if asset:
                next_assets = list(selected_assets)
                if asset["id"] not in {row.get("id") for row in next_assets}:
                    next_assets.append(asset)
                    update_active_inputs({"selected_assets": next_assets})
                    st.rerun()


def _render_selected_assets(selected_assets: list[dict[str, Any]]) -> None:
    if not selected_assets:
        st.caption("No assets selected yet.")
        return

    st.markdown("##### Selected Assets")
    chunk_size = 3
    chunks = [selected_assets[i : i + chunk_size] for i in range(0, len(selected_assets), chunk_size)]
    for chunk in chunks:
        cols = st.columns(chunk_size)
        for col, asset in zip(cols, chunk):
            with col:
                st.markdown(
                    f'<div class="alloca-chip alloca-chip-wrapper">'
                    f'<div class="alloca-chip-symbol">{_chip_symbol(asset)}</div>'
                    f'<div class="alloca-chip-name">{_chip_name(asset, selected_assets)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("✕", key=f"remove_{asset['id']}", help="Remove asset"):
                    next_assets = [row for row in selected_assets if row.get("id") != asset["id"]]
                    update_active_inputs({"selected_assets": next_assets})
                    st.rerun()


def _render_single_choice_cards(
    *,
    key_prefix: str,
    options: list[str],
    selected_value: str | None,
    help_lookup: dict[str, str],
) -> str | None:
    current = selected_value
    rows = [options[i : i + 5] for i in range(0, len(options), 5)]
    for row_index, row in enumerate(rows):
        cols = st.columns(len(row))
        for col, option in zip(cols, row):
            with col:
                if st.button(
                    option,
                    key=f"{key_prefix}_{row_index}_{option}",
                    width="stretch",
                    type="primary" if current == option else "secondary",
                    help=help_lookup[option],
                ):
                    current = option
    return current


def _render_model_cards(selected_models: list[str]) -> list[str]:
    current = list(selected_models)
    cols = st.columns(3)
    for col, (model_id, label) in zip(cols, MODEL_LABELS.items()):
        with col:
            is_selected = model_id in current
            if st.button(
                label,
                key=f"model_{model_id}",
                width="stretch",
                type="primary" if is_selected else "secondary",
                help=MODEL_HELP[model_id],
            ):
                if is_selected and len(current) > 1:
                    current.remove(model_id)
                elif not is_selected:
                    current.append(model_id)
    return current


def _render_constraints(
    selected_assets: list[dict[str, Any]],
    constraints: dict[str, Any],
    issues: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    asset_options = {f"{_chip_symbol(asset)} · {_chip_name(asset, selected_assets)}": asset["id"] for asset in selected_assets}

    # Min/max number of assets — moved to top per user request
    count_cols = st.columns(2)
    with count_cols[0]:
        min_assets = st.number_input(
            "Min number of assets in portfolio",
            min_value=0,
            max_value=max(10, len(selected_assets)),
            value=int(constraints.get("min_assets_in_portfolio") or 0),
            step=1,
            key="constraint_min_assets",
        )
        _render_field_issues(issues, "constraints.min_assets_in_portfolio")
    with count_cols[1]:
        max_assets = st.number_input(
            "Max number of assets in portfolio",
            min_value=0,
            max_value=max(10, len(selected_assets)),
            value=int(constraints.get("max_assets_in_portfolio") or len(selected_assets) or 0),
            step=1,
            key="constraint_max_assets",
        )
        _render_field_issues(issues, "constraints.max_assets_in_portfolio")

    global_cols = st.columns(2)
    with global_cols[0]:
        global_min = st.number_input(
            "Min allocation per asset (%)",
            min_value=0,
            max_value=100,
            value=int(constraints.get("global_min_allocation_percent") or 0),
            step=1,
            key="constraint_global_min",
        )
        _render_field_issues(issues, "constraints.global_min_allocation_percent")
    with global_cols[1]:
        global_max = st.number_input(
            "Max allocation per asset (%)",
            min_value=0,
            max_value=100,
            value=int(constraints.get("global_max_allocation_percent") or 100),
            step=1,
            key="constraint_global_max",
        )
        _render_field_issues(issues, "constraints.global_max_allocation_percent")

    selected_min_assets = st.multiselect(
        "Assets for selected-asset minimum",
        options=list(asset_options),
        default=[
            label
            for label, asset_id in asset_options.items()
            if asset_id in (constraints.get("selected_asset_min_allocation") or {}).get("asset_ids", [])
        ],
        key="constraint_selected_min_assets",
    )
    _render_field_issues(issues, "constraints.selected_asset_min_allocation.asset_ids")
    selected_min_percent = st.number_input(
        "Min allocation to selected asset (%)",
        min_value=0,
        max_value=100,
        value=int((constraints.get("selected_asset_min_allocation") or {}).get("percent") or 0),
        step=1,
        key="constraint_selected_min_percent",
    )
    _render_field_issues(issues, "constraints.selected_asset_min_allocation.percent")

    selected_max_assets = st.multiselect(
        "Assets for selected-asset maximum",
        options=list(asset_options),
        default=[
            label
            for label, asset_id in asset_options.items()
            if asset_id in (constraints.get("selected_asset_max_allocation") or {}).get("asset_ids", [])
        ],
        key="constraint_selected_max_assets",
    )
    _render_field_issues(issues, "constraints.selected_asset_max_allocation.asset_ids")
    selected_max_percent = st.number_input(
        "Max allocation to selected asset (%)",
        min_value=0,
        max_value=100,
        value=int((constraints.get("selected_asset_max_allocation") or {}).get("percent") or 100),
        step=1,
        key="constraint_selected_max_percent",
    )
    _render_field_issues(issues, "constraints.selected_asset_max_allocation.percent")

    _render_field_issues(issues, "constraints")

    return {
        "global_min_allocation_percent": global_min,
        "global_max_allocation_percent": global_max,
        "selected_asset_min_allocation": {
            "asset_ids": [asset_options[label] for label in selected_min_assets],
            "percent": selected_min_percent,
        }
        if selected_min_assets
        else None,
        "selected_asset_max_allocation": {
            "asset_ids": [asset_options[label] for label in selected_max_assets],
            "percent": selected_max_percent,
        }
        if selected_max_assets
        else None,
        "min_assets_in_portfolio": min_assets,
        "max_assets_in_portfolio": max_assets,
    }


def _render_confirmation_panel() -> None:
    confirmation = confirmation_state()
    if not confirmation:
        return

    st.warning(confirmation["message"])
    cols = st.columns(2)
    with cols[0]:
        if st.button("Confirm", type="primary", width="stretch"):
            action = confirmation["action"]
            clear_confirmation()
            if action == "reconfigure_plan":
                abandon_generated_plan()
            elif action == "reset_configuration":
                reset_configuration()
                reset_review_ui()
            st.rerun()
    with cols[1]:
        if st.button("Keep current state", width="stretch"):
            clear_confirmation()
            st.rerun()


def _validation_summary(issues: list[dict[str, Any]]) -> str:
    messages = [str(issue.get("message", "Configuration is invalid.")) for issue in issues if isinstance(issue, dict)]
    return "The configuration still needs attention:\n- " + "\n- ".join(messages)


def _issues_by_field(issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        field = str(issue.get("field") or "general")
        grouped.setdefault(field, []).append(issue)
    return grouped


def _render_issue_summary(grouped: dict[str, list[dict[str, Any]]]) -> None:
    for rows in grouped.values():
        for issue in rows:
            st.caption(f"- {_issue_message(issue)}")


def _render_field_issues(grouped: dict[str, list[dict[str, Any]]], field: str) -> None:
    for issue in grouped.get(field, []):
        st.caption(f":red[{_issue_message(issue)}]")


def _issue_message(issue: dict[str, Any]) -> str:
    return str(issue.get("message", "Configuration issue"))


def _asset_option_label(token: dict[str, str], selected_assets: list[dict[str, Any]]) -> str:
    return f"${str(token.get('symbol', '')).upper()} · {str(token.get('name', ''))}"


def _chip_symbol(asset: dict[str, Any]) -> str:
    return f"${str(asset.get('symbol', '')).upper()}"


def _chip_name(asset: dict[str, Any], selected_assets: list[dict[str, Any]]) -> str:
    symbol = str(asset.get("symbol", "")).lower()
    same_symbol = [row for row in selected_assets if str(row.get("symbol", "")).lower() == symbol]
    if len(same_symbol) == 1:
        return str(asset.get("name", ""))

    name = str(asset.get("name", ""))
    same_name = [
        row for row in same_symbol if str(row.get("name", "")).lower() == name.lower()
    ]
    if len(same_name) == 1:
        return name
    return str(asset.get("id", name))
