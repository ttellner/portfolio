"""Lightweight UI helpers that avoid lazy-loaded Streamlit frontend chunks."""

from __future__ import annotations

import html

import streamlit as st


def render_stat_cards(items: list[tuple[str, str]]) -> None:
    """Render metric-style values using HTML instead of st.metric."""
    if not items:
        return
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        safe_label = html.escape(str(label))
        safe_value = html.escape(str(value))
        with col:
            st.markdown(
                (
                    '<div style="background:#f0f2f6;border-radius:8px;'
                    'padding:0.75rem 1rem;">'
                    f'<div style="color:#444;font-size:0.8rem;">{safe_label}</div>'
                    f'<div style="font-size:1.4rem;font-weight:600;'
                    f'color:#262730;">{safe_value}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
