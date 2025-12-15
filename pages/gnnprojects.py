import streamlit as st
import os
import re
import importlib.util
from theme import apply_theme

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Thomas Tellner | Data Science Portfolio",
    page_icon="📊",
    layout="wide",
)

apply_theme()

# Hide Streamlit's built-in navigation
st.markdown("""
<style>
section[data-testid="stSidebarNav"] { display: none; }
nav[aria-label="Secondary"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---- SIDEBAR PROFILE ----
with st.sidebar:
    #st.image("https://via.placeholder.com/150", width=200) 
    st.title("Thomas Tellner")
    st.markdown("Data Science | ML & AI | GenAI")
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")
    st.caption("Made using Streamlit")

# --- Main Page ---
st.title("Machine Learning for Graph Neural Network Explorations")
st.write("""Graph Neural Networks
         Explore and run machine learning demos below.""")

# --- Base directory for project files ---
base_dir = os.path.join(os.getcwd(), "pages", "gnnprojects")

# Handle internal navigation (when a project is selected)
query_params = st.query_params
if "project" in query_params:
    project_file = query_params["project"]
    project_path = os.path.join(base_dir, project_file)

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

# --- Scan for available ML projects (.py files) ---
if not os.path.exists(base_dir):
    st.warning(f"No ML project directory found at: {base_dir}")
else:
    project_files = [f for f in os.listdir(base_dir) if f.endswith(".py")]
    if not project_files:
        st.info("No ML projects found in this folder.")
    else:
        num_cols = 3
        for i in range(0, len(project_files), num_cols):
            cols = st.columns(num_cols)
            for j, project_file in enumerate(project_files[i:i + num_cols]):
                with cols[j]:
                    # Extract metadata from docstring if available
                    path = os.path.join(base_dir, project_file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                        if docstring:
                            lines = [line.strip() for line in docstring.group(1).split("\n") if line.strip()]
                            title = lines[0] if len(lines) > 0 else project_file.replace(".py", "")
                            desc = lines[1] if len(lines) > 1 else ""
                            img = lines[2] if len(lines) > 2 else "https://via.placeholder.com/400x200?text=ML+Project"
                        else:
                            title, desc, img = project_file.replace(".py", ""), "", "https://via.placeholder.com/400x200?text=ML+Project"

                    # --- Display card ---
                    #st.image(img, use_container_width=True)
                    st.markdown(f"""
                    <div class="project-card"> 
                            <h3>{title}</h3>
                            <p>{desc}</p>
                        </div>""", unsafe_allow_html=True)

                    # Button for internal navigation
                    st.button(
                        "▶ Open Project",
                        key=f"open_{project_file}",
                        on_click=lambda f=project_file: st.query_params.update({"project": f})
                    )

                    st.markdown("---")
