# Handle internal navigation (when a project is selected)
query_params = st.query_params
if "project" in query_params:
    project_file = query_params["project"]
    project_path = os.path.join(base_dir, project_file)

    # --- BACK BUTTON & BREADCRUMB TITLE ---
    # Format filename like "1_Chapter_2_Lab_1.py" → "Chapter 2 Lab 1"
    project_name = " ".join(project_file.replace(".py", "").split("_")[1:])

    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        if st.button("⬅ Back"):
            st.query_params.clear()
            st.rerun()
    with col2:
        st.markdown(f"### 📁 {project_name}")
    st.markdown("---")

    # --- Load and execute selected project ---
    if os.path.exists(project_path):
        spec = importlib.util.spec_from_file_location("project_module", project_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            st.stop()  # stop rendering this page and show the project
        else:
            st.error(f"Could not load: {project_path}")
    else:
        st.error(f"Project file not found: {project_path}")

import os
import streamlit as st
import re
from theme import apply_theme

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Thomas Tellner | Data Science Portfolio",
    page_icon="📊",
    layout="wide",
)

# ---- HIDE STREAMLIT DEFAULT NAVIGATION ----
st.markdown("""
<style>
/* Hide Streamlit's automatic page navigation */
nav[aria-label="Secondary"] { display: none; }
div[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

apply_theme()

# ---- SIDEBAR ----
with st.sidebar:
    st.title("Thomas Tellner")
    st.markdown("Data Science | ML & AI | GenAI")
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")

    # --- Custom Sidebar Navigation ---
    st.subheader("📂 Projects")

    # Dynamically detect pages
    pages_dir = "pages"
    page_files = sorted([f for f in os.listdir(pages_dir) if f.endswith(".py")])

    for file in page_files:
        # Format title nicely
        page_title = file.replace(".py", "").replace("_", " ").title()
        page_path = os.path.join("pages", file)
        st.page_link(page_path, label=page_title, icon="📘")

    st.markdown("---")
    st.caption("Made using Streamlit")
