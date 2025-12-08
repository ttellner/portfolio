import streamlit as st
from pathlib import Path
import sys

st.set_page_config(layout="wide")

# Get the directory containing this file
base_dir = Path(__file__).parent
notebook_path = base_dir / "Chapter6_Lab2.ipynb"

# Add the gamedatascience directory to path to import notebook_runner
gamedatascience_dir = base_dir.parent
if str(gamedatascience_dir) not in sys.path:
    sys.path.insert(0, str(gamedatascience_dir))

try:
    from notebook_runner import display_notebook_interactive
except ImportError:
    st.error("Could not import notebook_runner module. Please ensure notebook_runner.py exists in the gamedatascience directory.")
    st.stop()

if not notebook_path.exists():
    st.error(f"Notebook file not found: {notebook_path}")
    st.info("Please ensure the notebook file exists in the same directory as this script.")
else:
    st.title("Chapter 6 Lab 2 - Interactive Notebook")
    st.markdown("---")
    display_notebook_interactive(notebook_path)
