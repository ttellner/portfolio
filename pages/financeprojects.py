"""
Machine Learning for Finance and Investments
ML/AI for Finance and Investments. Explore and run machine learning demos below.
https://via.placeholder.com/400x200?text=Finance+Investments
"""
import re
from pathlib import Path

import streamlit as st

from project_router import init_hub_page, load_project_module, render_profile_sidebar, title_from_file

base_dir = Path(__file__).parent / "financeprojects"
project_file = st.query_params.get("project")

if project_file:
    project_path = base_dir / project_file
    init_hub_page(
        index_title="Finance and Investments",
        project_title=title_from_file(project_path, "Finance Project"),
    )
    load_project_module(project_path)
else:
    init_hub_page(index_title="Thomas Tellner | Data Science Portfolio")

render_profile_sidebar()

st.title("Machine Learning for Finance and Investments")
st.write("ML/AI for Finance and Investments. Explore and run machine learning demos below.")

if not base_dir.exists():
    st.warning(f"No ML project directory found at: {base_dir}")
else:
    project_files = [f.name for f in base_dir.iterdir() if f.suffix == ".py"]
    if not project_files:
        st.info("No ML projects found in this folder.")
    else:
        num_cols = 3
        for i in range(0, len(project_files), num_cols):
            cols = st.columns(num_cols)
            for j, project_name in enumerate(project_files[i : i + num_cols]):
                with cols[j]:
                    path = base_dir / project_name
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring:
                        lines = [
                            line.strip()
                            for line in docstring.group(1).split("\n")
                            if line.strip()
                        ]
                        title = lines[0] if lines else project_name.replace(".py", "")
                        desc = lines[1] if len(lines) > 1 else ""
                    else:
                        title, desc = project_name.replace(".py", ""), ""

                    st.markdown(
                        f"""
                        <div class="project-card">
                            <h3>{title}</h3>
                            <p>{desc}</p>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "▶ Open Project",
                        key=f"open_{project_name}",
                        on_click=lambda f=project_name: st.query_params.update({"project": f}),
                    )
