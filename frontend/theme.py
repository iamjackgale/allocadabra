"""Streamlit page theme and shared presentation helpers."""

from __future__ import annotations

import streamlit as st

from frontend.constants import PHASE_ACCENTS


def apply_theme(phase: str) -> None:
    """Apply shared CSS and phase accent styling."""
    accent = PHASE_ACCENTS.get(phase, PHASE_ACCENTS["configuration"])
    st.markdown(
        f"""
        <style>
        :root {{
          --alloca-accent-rgb: {accent["rgb"]};
          --alloca-accent: {accent["solid"]};
          --alloca-accent-muted: {accent["muted"]};
          --alloca-panel: rgba(255, 255, 255, 0.74);
          --alloca-border: rgba(var(--alloca-accent-rgb), 0.24);
          --alloca-text-soft: rgba(33, 37, 41, 0.72);
        }}

        [data-testid="stAppViewContainer"] {{
          background:
            radial-gradient(circle at 12% 14%, rgba(var(--alloca-accent-rgb), 0.18), transparent 34%),
            radial-gradient(circle at 88% 10%, rgba(var(--alloca-accent-rgb), 0.12), transparent 28%),
            linear-gradient(180deg, rgba(246, 248, 251, 0.98) 0%, rgba(238, 242, 246, 0.98) 100%);
        }}

        [data-testid="stAppViewContainer"]::before {{
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at center top, rgba(var(--alloca-accent-rgb), 0.10), transparent 42%);
          z-index: 0;
        }}

        .block-container {{
          padding-top: 2.2rem;
          padding-bottom: 2rem;
          max-width: 1380px;
        }}

        .alloca-panel {{
          background: var(--alloca-panel);
          border: 1px solid rgba(18, 24, 40, 0.08);
          border-radius: 22px;
          padding: 1rem 1.1rem;
          box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
          backdrop-filter: blur(12px);
        }}

        .alloca-phase {{
          display: inline-block;
          letter-spacing: 0.18em;
          font-size: 0.78rem;
          font-weight: 700;
          color: var(--alloca-accent);
          margin-bottom: 0.8rem;
        }}

        .alloca-phase-center {{
          display: block;
          text-align: center;
          letter-spacing: 0.28em;
          font-size: 0.84rem;
          font-weight: 700;
          color: var(--alloca-accent);
          margin-bottom: 1rem;
        }}

        .alloca-subtle {{
          color: var(--alloca-text-soft);
          font-size: 0.95rem;
        }}

        .alloca-chip {{
          border: 1px solid var(--alloca-border);
          border-radius: 18px;
          padding: 0.7rem 0.85rem;
          background: rgba(var(--alloca-accent-rgb), 0.08);
          min-height: 88px;
        }}

        .alloca-chip-symbol {{
          font-weight: 800;
          font-size: 1rem;
        }}

        .alloca-chip-name {{
          margin-top: 0.18rem;
          color: var(--alloca-text-soft);
          font-size: 0.82rem;
        }}

        .alloca-card {{
          border: 1px solid rgba(18, 24, 40, 0.09);
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.58);
          padding: 0.85rem;
          min-height: 122px;
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
          color: var(--alloca-text-soft);
          font-size: 0.85rem;
          text-align: center;
        }}

        .alloca-mobile-overlay {{
          display: none;
        }}

        @media (max-width: 768px) {{
          .alloca-mobile-overlay {{
            display: flex;
            position: fixed;
            inset: 0;
            z-index: 999999;
            background: linear-gradient(180deg, rgba(245, 247, 250, 0.98), rgba(234, 239, 244, 0.98));
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
          }}

          .alloca-mobile-card {{
            width: min(92vw, 32rem);
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(18, 24, 40, 0.08);
            border-radius: 22px;
            padding: 1.4rem;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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

