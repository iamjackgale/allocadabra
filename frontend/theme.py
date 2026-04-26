"""Streamlit page theme and shared presentation helpers."""

from __future__ import annotations

import streamlit as st

from frontend.constants import PHASE_ACCENTS


def apply_theme(phase: str) -> None:
    """Apply shared CSS and phase accent styling, respecting dark mode session state."""
    from frontend.runtime import get_dark_mode
    dark_mode = get_dark_mode()
    accent = PHASE_ACCENTS.get(phase, PHASE_ACCENTS["configuration"])

    if dark_mode:
        panel_bg = "rgba(28, 32, 44, 0.90)"
        body_bg_1 = "rgba(14, 18, 30, 0.99)"
        body_bg_2 = "rgba(10, 14, 24, 0.99)"
        border_col = "rgba(255, 255, 255, 0.18)"
        text_soft = "rgba(200, 210, 220, 0.72)"
        text_main = "rgba(230, 235, 245, 0.95)"
        card_bg = "rgba(255, 255, 255, 0.05)"
        shadow = "rgba(0, 0, 0, 0.40)"
        input_bg = "rgba(255, 255, 255, 0.05)"
        chip_bg = f"rgba({accent['rgb']}, 0.12)"
        chat_box_bg = "rgba(255, 255, 255, 0.05)"
        mobile_bg_1 = "rgba(14, 18, 30, 0.98)"
        mobile_bg_2 = "rgba(10, 14, 24, 0.98)"
        mobile_card_bg = "rgba(28, 32, 44, 0.90)"
    else:
        panel_bg = "rgba(255, 255, 255, 0.74)"
        body_bg_1 = "rgba(246, 248, 251, 0.98)"
        body_bg_2 = "rgba(238, 242, 246, 0.98)"
        border_col = "rgba(18, 24, 40, 0.18)"
        text_soft = "rgba(33, 37, 41, 0.72)"
        text_main = "rgba(20, 24, 35, 0.95)"
        card_bg = "rgba(255, 255, 255, 0.58)"
        shadow = "rgba(15, 23, 42, 0.08)"
        input_bg = "rgba(255, 255, 255, 0.85)"
        chip_bg = f"rgba({accent['rgb']}, 0.08)"
        chat_box_bg = "rgba(252, 253, 255, 0.90)"
        mobile_bg_1 = "rgba(245, 247, 250, 0.98)"
        mobile_bg_2 = "rgba(234, 239, 244, 0.98)"
        mobile_card_bg = "rgba(255, 255, 255, 0.90)"

    # Dark-mode component overrides (built as a plain string to avoid nested f-string issues)
    if dark_mode:
        dark_css = (
            f'[data-testid="stAppViewContainer"] p,'
            f'[data-testid="stAppViewContainer"] label,'
            f'[data-testid="stAppViewContainer"] span,'
            f'[data-testid="stMarkdown"] {{ color: {text_main}; }}'
            f'[data-testid="stTextInput"] input,'
            f'[data-testid="stNumberInput"] input {{'
            f'  background: {input_bg} !important;'
            f'  color: {text_main} !important;'
            f'  border-color: {border_col} !important;'
            f'}}'
            f'[data-testid="stSelectbox"] > div > div {{'
            f'  background: {input_bg} !important;'
            f'  color: {text_main} !important;'
            f'  border-color: {border_col} !important;'
            f'}}'
            f'[data-testid="stMultiSelect"] > div > div {{'
            f'  background: {input_bg} !important;'
            f'  color: {text_main} !important;'
            f'}}'
            f'[data-testid="stExpander"] {{'
            f'  background: {input_bg} !important;'
            f'  border-color: {border_col} !important;'
            f'}}'
            f'[data-testid="stChatMessage"] {{ background: {chat_box_bg} !important; }}'
            f'.stAlert {{ background: {card_bg} !important; color: {text_main} !important; }}'
        )
    else:
        dark_css = ""

    st.markdown(
        f"""
        <style>
        /* ── Variables ─────────────────────────────────────────────── */
        :root {{
          --alloca-accent-rgb: {accent["rgb"]};
          --alloca-accent: {accent["solid"]};
          --alloca-accent-muted: {accent["muted"]};
          --alloca-panel: {panel_bg};
          --alloca-border: rgba(var(--alloca-accent-rgb), 0.24);
          --alloca-text-soft: {text_soft};
        }}

        /* ── Hide Streamlit native chrome ──────────────────────────── */
        [data-testid="stHeader"] {{ display: none !important; }}
        #MainMenu {{ display: none !important; }}
        [data-testid="stToolbar"] {{ display: none !important; }}
        [data-testid="stDecoration"] {{ display: none !important; }}
        [data-testid="stStatusWidget"] {{ display: none !important; }}

        /* ── Page background ────────────────────────────────────────── */
        [data-testid="stAppViewContainer"] {{
          background:
            radial-gradient(circle at 12% 14%, rgba(var(--alloca-accent-rgb), 0.18), transparent 34%),
            radial-gradient(circle at 88% 10%, rgba(var(--alloca-accent-rgb), 0.12), transparent 28%),
            linear-gradient(180deg, {body_bg_1} 0%, {body_bg_2} 100%);
          color: {text_main};
        }}

        [data-testid="stAppViewContainer"]::before {{
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(circle at center top, rgba(var(--alloca-accent-rgb), 0.10), transparent 42%);
          z-index: 0;
        }}

        /* ── Layout ─────────────────────────────────────────────────── */
        .block-container {{
          padding-top: 0.5rem;
          padding-bottom: 2rem;
          max-width: 1380px;
        }}

        /* ── Custom header ──────────────────────────────────────────── */
        .alloca-header-title {{
          font-size: 1.55rem;
          font-weight: 800;
          letter-spacing: 0.04em;
          color: {text_main};
          line-height: 1;
          padding: 0.3rem 0 0.1rem 0;
        }}

        .alloca-header-subtitle {{
          font-size: 0.9rem;
          font-weight: 400;
          color: {text_main};
          padding: 0 0 0.5rem 0;
        }}

        /* Dark mode toggle: pin to right edge of header, transparent appearance */
        [data-testid="stHorizontalBlock"]:has(.alloca-header-title) {{
          position: relative !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.alloca-header-title) > [data-testid="column"]:last-child {{
          position: absolute !important;
          right: 0 !important;
          top: 0 !important;
          width: auto !important;
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.alloca-header-title) > [data-testid="column"]:last-child [data-testid="stButton"],
        [data-testid="stHorizontalBlock"]:has(.alloca-header-title) > [data-testid="column"]:last-child [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"]:has(.alloca-header-title) > [data-testid="column"]:last-child button {{
          background: transparent !important;
          background-color: transparent !important;
          border: none !important;
          box-shadow: none !important;
          outline: none !important;
          color: {text_main} !important;
        }}

        /* ── Panel columns via :has() ───────────────────────────────── */
        /* Only columns containing a phase label get the frosted-glass panel style */
        [data-testid="column"]:has(.alloca-phase) {{
          background: {panel_bg};
          border: 1px solid {border_col};
          border-radius: 22px;
          padding: 0.9rem 1rem !important;
          box-shadow: 0 20px 50px {shadow};
          backdrop-filter: blur(12px);
        }}

        /* Nested columns inside panel columns are reset to transparent */
        [data-testid="column"]:has(.alloca-phase) [data-testid="column"] {{
          background: transparent !important;
          border: none !important;
          border-radius: 0 !important;
          box-shadow: none !important;
          padding: 0 !important;
          backdrop-filter: none !important;
        }}

        /* ── Scrollable layout ──────────────────────────────────────── */
        /* Align panel columns to top so heights differ independently */
        [data-testid="stHorizontalBlock"]:has(.alloca-phase) {{
          align-items: flex-start !important;
        }}

        /* Left column (chat): sticky, bounded, no internal scroll */
        [data-testid="stHorizontalBlock"]:has(.alloca-phase) > [data-testid="column"]:first-child {{
          position: sticky;
          top: 4px;
          max-height: calc(100vh - 90px);
          overflow: hidden;
        }}


        /* Right column (config/review): scrollable container */
        [data-testid="stHorizontalBlock"]:has(.alloca-phase) > [data-testid="column"]:last-child {{
          max-height: calc(100vh - 90px);
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: {border_col} transparent;
        }}

        /* ── Phase labels ───────────────────────────────────────────── */
        .alloca-phase {{
          display: inline-block;
          letter-spacing: 0.18em;
          font-size: 1rem;
          font-weight: 700;
          color: {text_main};
          margin-bottom: 0.8rem;
        }}

        .alloca-phase-center {{
          display: block;
          text-align: center;
          letter-spacing: 0.28em;
          font-size: 1rem;
          font-weight: 700;
          color: {text_main};
          margin-bottom: 1rem;
        }}

        /* ── Section headers in configuration ───────────────────────── */
        [data-testid="column"]:has(.alloca-phase) h5 {{
          font-size: 1.25rem !important;
          font-weight: 600 !important;
          font-family: 'Source Sans Pro', 'Source Sans 3', sans-serif !important;
          color: {text_main} !important;
          margin-top: 0.6rem !important;
          margin-bottom: 0.3rem !important;
        }}

        /* ── Chat message container and input: matching borders ─────── */
        [data-testid="stVerticalBlockBorderWrapper"] {{
          border: 1.5px solid {border_col} !important;
          border-radius: 14px !important;
          background: {chat_box_bg} !important;
        }}

        [data-testid="stChatInput"] {{
          border: 1.5px solid {border_col} !important;
          border-radius: 14px !important;
          background: {chat_box_bg} !important;
          overflow: hidden;
          box-shadow: none !important;
          outline: none !important;
        }}

        [data-testid="stChatInput"] textarea {{
          color: {text_main} !important;
          background: transparent !important;
        }}

        /* ── Secondary buttons: transparent with matching text ──────── */
        button[data-testid="baseButton-secondary"] {{
          background: transparent !important;
          color: {text_main} !important;
          border: 1px solid {border_col} !important;
        }}

        button[data-testid="baseButton-secondary"]:hover {{
          background: rgba(var(--alloca-accent-rgb), 0.10) !important;
          border-color: var(--alloca-accent) !important;
        }}

        /* ── Asset chip grid: X button overlay ──────────────────────── */
        [data-testid="column"]:has(.alloca-chip-wrapper) {{
          position: relative !important;
        }}

        [data-testid="column"]:has(.alloca-chip-wrapper) [data-testid="stButton"] {{
          position: absolute !important;
          top: 0.2rem !important;
          right: 0.2rem !important;
          margin: 0 !important;
          padding: 0 !important;
          width: auto !important;
          z-index: 5;
        }}

        [data-testid="column"]:has(.alloca-chip-wrapper) [data-testid="stButton"] button {{
          width: 1.5rem !important;
          height: 1.5rem !important;
          min-height: 1.5rem !important;
          padding: 0 !important;
          border-radius: 50% !important;
          font-size: 0.72rem !important;
          line-height: 1 !important;
        }}

        /* ── Misc elements ──────────────────────────────────────────── */
        .alloca-subtle {{
          color: {text_soft};
          font-size: 0.95rem;
        }}

        .alloca-chip {{
          border: 1px solid {border_col};
          border-radius: 14px;
          padding: 0.7rem 0.85rem;
          background: {chip_bg};
          min-height: 80px;
        }}

        .alloca-chip-symbol {{
          font-weight: 800;
          font-size: 1rem;
          color: {text_main};
        }}

        .alloca-chip-name {{
          margin-top: 0.18rem;
          color: {text_soft};
          font-size: 0.82rem;
        }}

        .alloca-card {{
          border: 1px solid {border_col};
          border-radius: 18px;
          background: {card_bg};
          padding: 0.85rem;
        }}

        .alloca-card strong {{
          display: block;
          margin-bottom: 0.35rem;
        }}

        .alloca-note {{
          border-left: 3px solid var(--alloca-accent);
          padding: 0.85rem 0.9rem;
          background: rgba(var(--alloca-accent-rgb), 0.08);
          border-radius: 10px;
          font-size: 0.94rem;
        }}

        .alloca-footer {{
          margin-top: 2rem;
          color: {text_soft};
          font-size: 0.85rem;
          text-align: center;
        }}

        /* ── Dark-mode component overrides ──────────────────────────── */
        {dark_css}

        /* ── Mobile overlay ─────────────────────────────────────────── */
        .alloca-mobile-overlay {{
          display: none;
        }}

        @media (max-width: 768px) {{
          .alloca-mobile-overlay {{
            display: flex;
            position: fixed;
            inset: 0;
            z-index: 999999;
            background: linear-gradient(180deg, {mobile_bg_1}, {mobile_bg_2});
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
          }}

          .alloca-mobile-card {{
            width: min(92vw, 32rem);
            background: {mobile_card_bg};
            border: 1px solid {border_col};
            border-radius: 22px;
            padding: 1.4rem;
            box-shadow: 0 20px 50px {shadow};
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the Allocadabra brand title and light/dark mode toggle."""
    from frontend.runtime import get_dark_mode, toggle_dark_mode
    dark_mode = get_dark_mode()

    title_col, toggle_col = st.columns([8, 1])
    with title_col:
        st.markdown(
            '<div class="alloca-header-title">Allocadabra</div>'
            '<div class="alloca-header-subtitle">Making portfolio allocation magical.</div>',
            unsafe_allow_html=True,
        )
    with toggle_col:
        icon = "☀" if dark_mode else "☾"
        if st.button(icon, key="dark_mode_toggle", help="Toggle light / dark mode"):
            toggle_dark_mode()
            st.rerun()


def render_mobile_overlay() -> None:
    """Render a CSS-driven mobile holding screen."""
    st.markdown(
        """
        <div class="alloca-mobile-overlay">
          <div class="alloca-mobile-card">
            <div class="alloca-phase">MOBILE</div>
            <h3 style="margin-top: 0;">Allocadabra has not yet been optimized for mobile.</h3>
            <p class="alloca-subtle" style="margin-bottom: 0;">
              Please reopen this app on a desktop or laptop screen for the intended workflow layout.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the persistent product footer."""
    st.markdown(
        """
        <div class="alloca-footer">
          Experimental project produced for educational purposes only. No warranty as to correctness. Licence: MIT<br/>
          &copy; 2026 <a href="https://jackgale.uk" target="_blank">Jack Harry Gale</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
