import streamlit as st
from pathlib import Path
import json

st.set_page_config(layout="wide")

# Get the directory containing this file
base_dir = Path(__file__).parent
notebook_path = base_dir / "Chapter2_Lab3.ipynb"

# Try to import nbconvert, but handle gracefully if not available
try:
    from nbconvert import HTMLExporter
    import nbformat
    NBCONVERT_AVAILABLE = True
except ImportError:
    NBCONVERT_AVAILABLE = False

if not notebook_path.exists():
    st.error(f"Notebook file not found: {notebook_path}")
    st.info("Please ensure the notebook file exists in the same directory as this script.")
else:
    if NBCONVERT_AVAILABLE:
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)
            
            html_exporter = HTMLExporter()
            (body, _) = html_exporter.from_notebook_node(notebook)
            
            st.components.v1.html(body, height=800, scrolling=True)
        except Exception as e:
            st.error(f"Error converting notebook to HTML: {e}")
            st.info("Falling back to JSON display...")
            # Fallback: display as JSON
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook_data = json.load(f)
            st.json(notebook_data)
    else:
        # Fallback: read and display notebook as JSON
        st.warning("⚠️ `nbconvert` is not installed. Displaying notebook as JSON.")
        st.info("To see the notebook rendered as HTML, install nbconvert: `pip install nbconvert`")
        
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook_data = json.load(f)
            
            # Try to display cells in a readable format
            st.markdown("## Notebook Contents")
            for i, cell in enumerate(notebook_data.get("cells", [])):
                cell_type = cell.get("cell_type", "unknown")
                with st.expander(f"Cell {i+1} ({cell_type})"):
                    source = cell.get("source", [])
                    if isinstance(source, list):
                        source = "".join(source)
                    if cell_type == "code":
                        st.code(source, language="python")
                    elif cell_type == "markdown":
                        st.markdown(source)
                    else:
                        st.text(source)
        except Exception as e:
            st.error(f"Error reading notebook: {e}")
            st.info(f"Notebook path: {notebook_path}")
