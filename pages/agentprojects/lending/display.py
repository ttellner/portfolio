"""Lightweight UI helpers that avoid fragile Streamlit frontend widgets."""

from __future__ import annotations

import html
import json
from typing import Any

import pandas as pd
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


def _cell(value: Any) -> str:
    """Serialize nested values so Arrow/Streamlit table rendering stays flat."""
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str)
    return str(value)


def flatten_records(records: list[dict] | dict) -> pd.DataFrame:
    """Build a flat string DataFrame from dict rows (safe for Streamlit tables)."""
    if isinstance(records, dict):
        records = [records]
    if not records:
        return pd.DataFrame()
    flat_rows = [{key: _cell(val) for key, val in row.items()} for row in records]
    return pd.DataFrame(flat_rows)


def render_table(records: list[dict] | dict, *, caption: str | None = None) -> None:
    """Render tabular data without nested Arrow types or lazy Metric chunks."""
    frame = flatten_records(records)
    if frame.empty:
        st.caption("No rows.")
        return
    st.table(frame)
    if caption:
        st.caption(caption)
