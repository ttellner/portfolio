"""Shared routing helpers for portfolio section project hubs."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import streamlit as st

from theme import apply_theme

_NAV_HIDE_CSS = """
<style>
section[data-testid="stSidebarNav"] { display: none; }
nav[aria-label="Secondary"] { display: none; }
</style>
"""


def title_from_file(path: Path, fallback: str = "Project") -> str:
    if not path.exists():
        return fallback
    content = path.read_text(encoding="utf-8")
    docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if docstring:
        lines = [line.strip() for line in docstring.group(1).split("\n") if line.strip()]
        if lines:
            return lines[0]
    return path.stem.replace("_", " ")


def init_hub_page(*, index_title: str, project_title: str | None = None) -> None:
    st.set_page_config(page_title=project_title or index_title, layout="wide")
    apply_theme()
    st.markdown(_NAV_HIDE_CSS, unsafe_allow_html=True)


def load_project_module(path: Path) -> None:
    if not path.exists() or path.suffix != ".py":
        st.error(f"Project file not found: {path}")
        st.stop()

    spec = importlib.util.spec_from_file_location("project_module", str(path))
    if not spec or not spec.loader:
        st.error(f"Could not load: {path}")
        st.stop()

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "main"):
        module.main()
    st.stop()


def render_profile_sidebar() -> None:
    with st.sidebar:
        st.title("Thomas Tellner")
        st.markdown("Data Science | ML & AI | GenAI")
        st.markdown("---")
        st.markdown("**Contact:**")
        st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
        st.markdown("[💻 GitHub](https://github.com/ttellner)")
        st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
        st.markdown("---")
        st.caption("Made using Streamlit")
