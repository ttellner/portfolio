"""
Game Data Science
Game Data Science projects. Explore and run machine learning demos below.
https://via.placeholder.com/400x200?text=Game+Data+Science
"""
import re
from pathlib import Path

import streamlit as st

from project_router import init_hub_page, load_project_module, render_profile_sidebar, title_from_file

base_dir = Path(__file__).parent / "gamedatascience"
chapter = st.query_params.get("chapter")
project_file = st.query_params.get("project")

if chapter and project_file:
    project_path = base_dir / chapter / project_file
    init_hub_page(
        index_title="Game Data Science",
        project_title=title_from_file(project_path, "Game Data Science Lab"),
    )
    load_project_module(project_path)
else:
    init_hub_page(index_title="Thomas Tellner | Data Science Portfolio")

render_profile_sidebar()

st.title("Game Data Science")
st.write(
    """Game Data Science Labs for the book "Game Data Science", converted from R to Python."""
)

chapter_dirs = sorted([d.name for d in base_dir.iterdir() if d.is_dir()])

for chapter_name in chapter_dirs:
    st.header(f"🗂 {chapter_name.replace('_', ' ')}")
    chapter_path = base_dir / chapter_name
    project_files = sorted([f.name for f in chapter_path.iterdir() if f.suffix == ".py"])

    if not project_files:
        st.info("No projects found in this chapter.")
        continue

    num_cols = 3
    for i in range(0, len(project_files), num_cols):
        cols = st.columns(num_cols)
        for j, lab_file in enumerate(project_files[i : i + num_cols]):
            with cols[j]:
                project_path = chapter_path / lab_file
                with open(project_path, "r", encoding="utf-8") as f:
                    content = f.read()
                docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if docstring_match:
                    lines = [
                        line.strip()
                        for line in docstring_match.group(1).split("\n")
                        if line.strip()
                    ]
                    desc = lines[1] if len(lines) > 1 else ""
                else:
                    desc = ""

                pretty_title = " ".join(lab_file.replace(".py", "").split("_")[1:])
                st.markdown(
                    f"""
                    <div class="project-card">
                        <h3>{pretty_title}</h3>
                        <p>{desc}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.button(
                    "▶ Open Project",
                    key=f"{chapter_name}_{lab_file}",
                    on_click=lambda c=chapter_name, f=lab_file: st.query_params.update(
                        {"chapter": c, "project": f}
                    ),
                )
                st.markdown("---")
