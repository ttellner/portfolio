import streamlit as st
import os
import re
import importlib.util
from pathlib import Path
from theme import apply_theme

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Thomas Tellner | Data Science Portfolio",
    page_icon="📊",
    layout="wide",
)

apply_theme()

# ---- SIDEBAR PROFILE ----
with st.sidebar:
    #st.image("https://via.placeholder.com/150", width=200) 
    st.title("Thomas Tellner")
    st.markdown("Data Science | ML & AI | GenAI")
    st.markdown("---")
    
    # Navigation links - context aware
    st.markdown("**Navigation:**")
    st.page_link("Home.py", label="🏠 Home", icon="🏠")
    
    # Check if we're on a specific project (via query params)
    query_params = st.query_params
    if "project" in query_params:
        # We're on a specific project, show link back to this page
        st.page_link("pages/bioinfprojects.py", label="📂 ML/AI for Bioinformatics", icon="📂")
        project_name = query_params["project"].replace(".py", "").replace("_", " ").title()
        st.markdown(f"📍 **{project_name}** (Current)")
    else:
        # We're on the project page itself
        st.markdown("📍 **ML/AI for Bioinformatics and Omics** (Current)")
    
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")
    st.caption("Made using Streamlit")


st.title("Machine Learning for Bioinformatics and Omics")
st.write("""ML/AI for Bioinformatics and Omics.
         Explore and run machine learning demos below.""")
st.write("""The format below is HTML markdown from RStudio.
         For technical reasons, both AWS and Railway could not render the file with ggplot2.""")

# --- Base directory for project files ---
# Use Path(__file__).parent to get the directory containing this file
# Then navigate to bioinfprojects relative to this file's location
base_dir = Path(__file__).parent / "bioinfprojects"

# Handle internal navigation (when a project is selected)
# Note: query_params is also used in sidebar above, so we check it again here
query_params = st.query_params
if "project" in query_params:
    project_file = query_params["project"]
    project_path = base_dir / project_file

    if project_path.exists():
        spec = importlib.util.spec_from_file_location("project_module", str(project_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Call main() if it exists (for Streamlit apps loaded via importlib)
            if hasattr(module, 'main'):
                module.main()
            st.stop()  # stop rendering this page and show the project
        else:
            st.error(f"Could not load: {project_path}")
    else:
        st.error(f"Project file not found: {project_path}")

# --- Scan for available ML projects (.py files) ---
if not base_dir.exists():
    st.warning(f"No ML project directory found at: {base_dir}")
else:
    project_files = [f.name for f in base_dir.iterdir() if f.suffix in [".py", ".RMD"]]
    if not project_files:
        st.info("No ML projects found in this folder.")
    else:
        # Sort project files so Part_1 comes before Part_2
        def sort_key(filename):
            # Extract part number if it exists (e.g., "Part_1" -> 1, "Part_2" -> 2)
            if "Part_1" in filename:
                return (0, filename)  # Part_1 comes first
            elif "Part_2" in filename:
                return (1, filename)  # Part_2 comes second
            else:
                return (2, filename)  # Others come last
        
        project_files = sorted(project_files, key=sort_key)
        
        num_cols = 3
        for i in range(0, len(project_files), num_cols):
            cols = st.columns(num_cols)
            for j, project_file in enumerate(project_files[i:i + num_cols]):
                with cols[j]:
                    # Extract metadata from docstring if available
                    path = base_dir / project_file
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


