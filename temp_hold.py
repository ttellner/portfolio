import streamlit as st
import os
import re

# ---- SIDEBAR PROFILE ----
with st.sidebar:
    #st.image("https://via.placeholder.com/150", width=200) 
    st.title("Thomas Tellner")
    st.markdown("📈 Data Science | ML & AI | GenAI")
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")

st.title("📚 Game Data Science")
st.write("""Game Data Science
         Labs for each chapter of the book "Game Data Science", converted from R to Python.""")

# Optional: scan the Book_Project folder to list chapters
chapter_dir = "pages/gamedatascience"
chapter_files = sorted([f for f in os.listdir(chapter_dir) if f.endswith(".py")])

chapters = []
for f in chapter_files:
    file_path = os.path.join(chapter_dir, f)
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            lines = [line.strip() for line in docstring_match.group(1).split("\n") if line.strip()]
            title = lines[0] if len(lines) > 0 else f.replace(".py", "")
            desc = lines[1] if len(lines) > 1 else ""
            chapters.append({"file": f, "title": title, "description": desc})

# Display chapters
for ch in chapters:
    st.subheader(ch["title"])
    st.write(ch["description"])
    page_name = "Book_Project/" + ch["file"]
    st.markdown(f"[➡ Open Chapter]({page_name})")


# ---- ABOUT SECTION ----
st.header("💡 About This Portfolio")
st.write("""
This portfolio was built with **Streamlit**, a Python framework for building data-driven web apps.
Each project highlights different aspects of data science, including:
- Predictive modeling and evaluation
- Natural language processing
- Data visualization and storytelling
- Integration with cloud services (AWS & Azure)
""")

st.markdown("---")

# ---- FOOTER ----
st.markdown(
    """
    <div style='text-align: center; padding-top: 1rem; font-size: 0.9rem; color: #777;'>
        © 2025 Thomas Tellner | Built with <a href="https://streamlit.io">Streamlit</a>
    </div>
    """,
    unsafe_allow_html=True
)

# Second version Monday October 27 2025

import streamlit as st
import os
import re
import importlib.util

# Check if user clicked into a specific project
query_params = st.query_params  # NO parentheses
if "chapter" in query_params and "project" in query_params:
    chapter = query_params["chapter"][0]
    project_file = query_params["project"][0]  # exact filename must include .py
    
    # Full path to the project file
    project_path = os.path.join(os.getcwd(), "pages", "gamedatascience", chapter, project_file)
    
    if os.path.exists(project_path):
        spec = importlib.util.spec_from_file_location("project_module", project_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            st.stop()  # Prevent rendering homepage content
        else:
            st.error(f"Failed to load the module spec: {project_path}")
    else:
        st.error(f"Project file not found: {project_path}")

st.title("📚 Game Data Science")
st.write("""Game Data Science
         Labs for each chapter of the book "Game Data Science", converted from R to Python.""")

# Base folder for the book project
base_dir = "pages/gamedatascience"

# Scan chapters (folders)
chapter_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

for chapter in chapter_dirs:
    st.header(f"🗂 {chapter.replace('_', ' ')}")
    
    chapter_path = os.path.join(base_dir, chapter)
    project_files = sorted([f for f in os.listdir(chapter_path) if f.endswith(".py")])
    
    if not project_files:
        st.info("No projects found in this chapter.")
        continue

    # Display projects in rows of 3 columns
    num_cols = 3
    for i in range(0, len(project_files), num_cols):
        cols = st.columns(num_cols)
        for j, project_file in enumerate(project_files[i:i+num_cols]):
            with cols[j]:
                project_path = os.path.join(chapter_path, project_file)
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
                
                #st.image(img, use_container_width=True)
                st.subheader(title)
                st.caption(desc)
                # Create full file path for internal navigation
                page_file = project_file  # keep original .py
                page_path = f"pages/gamedatascience/{chapter}/{page_file}.py"  # exact location for Streamlit

                # Create a clean display name for the link label
                page_title = page_file.replace(".py", "").replace("_", " ")

                # Internal link that opens in the same tab
                st.button(
                    "▶ Open Project",
                    key=f"{chapter}_{page_file}",
                    on_click=lambda c=chapter, f=page_file:
                        st.query_params.update({"chapter":c, "project":f})
                )

                # st.page_link(page_path, label=f"▶ {page_title}")

                
                # Navigation link
                #page_link = f"pages/gamedatascience/{chapter}/{project_file}"
                #st.page_link(page_path, label="▶ Open Project")
                st.markdown("---")
