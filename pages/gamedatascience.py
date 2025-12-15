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

# Check if user clicked into a specific project
query_params = st.query_params  # NO parentheses
if "chapter" in query_params and "project" in query_params:
    chapter = query_params["chapter"]
    project_file = query_params["project"]  # exact filename must include .py
    
    # Full path to the project file - use dynamic path based on file location
    base_dir = Path(__file__).parent / "gamedatascience"
    project_path = base_dir / chapter / project_file

    if project_path.exists():
        spec = importlib.util.spec_from_file_location("project_module", str(project_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            st.stop()  # Prevent rendering homepage content
        else:
            st.error(f"Failed to load the module spec: {project_path}")
    else:
        st.error(f"Project file not found: {project_path}")
        
st.title("Game Data Science")
st.write("""Game Data Science
         Labs for the book "Game Data Science", converted from R to Python.""")

# Base folder for the book project - use dynamic path
base_dir = Path(__file__).parent / "gamedatascience"

# Scan chapters (folders)
chapter_dirs = sorted([d.name for d in base_dir.iterdir() if d.is_dir()])

for chapter in chapter_dirs:
    st.header(f"🗂 {chapter.replace('_', ' ')}")
    
    chapter_path = base_dir / chapter
    project_files = sorted([f.name for f in chapter_path.iterdir() if f.suffix == ".py"])
    
    if not project_files:
        st.info("No projects found in this chapter.")
        continue

    # Display projects in rows of 3 columns
    num_cols = 3
    for i in range(0, len(project_files), num_cols):
        cols = st.columns(num_cols)
        for j, project_file in enumerate(project_files[i:i+num_cols]):
            with cols[j]:
                project_path = chapter_path / project_file
                # Read top docstring for metadata
                with open(project_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring_match:
                        lines = [line.strip() for line in docstring_match.group(1).split("\n") if line.strip()]
                        title = lines[0] if len(lines) > 0 else project_file.replace(".py", "")
                        desc = lines[1] if len(lines) > 1 else ""
                        img = lines[2] if len(lines) > 2 else "https://via.placeholder.com/400x200?text=Project"
                    else:
                        title, desc, img = project_file.replace(".py", ""), "", "https://via.placeholder.com/400x200?text=Project"
                
                pretty_title = " ".join(project_file.replace(".py", "").split("_")[1:])

                #st.image(img, use_container_width=True)
                st.markdown(f"""
                <div class="project-card">
                        <h3>{pretty_title}</h3>
                        <p>{desc}</p>
                        </div>""", unsafe_allow_html=True)
                #st.markdown('</div>', unsafe_allow_html=True)
                
                # Create full file path for internal navigation
                page_file = project_file  # keep original .py
                page_path = os.path.join("pages", "gamedatascience", chapter, page_file)  # exact location for Streamlit

                # Create a clean display name for the link label
                page_title = page_file.replace(".py", "").replace("_", " ")

                # Internal link that opens in the same tab
                st.button(
                    "▶ Open Project",
                    key=f"{chapter}_{page_file}",
                    on_click=lambda c=chapter, f=page_file:
                        st.query_params.update({"chapter":c, "project":f})
                )
                
                
                # Navigation link
                #page_link = f"pages/gamedatascience/{chapter}/{project_file}"
                #st.page_link(page_path, label="▶ Open Project")
                st.markdown("---")
