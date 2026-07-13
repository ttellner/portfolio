"""
Machine Learning for Banking and Finance
ML/AI for Banking and Lending. Explore and run machine learning demos below.
https://via.placeholder.com/400x200?text=Banking+Finance
"""
import re
from pathlib import Path

import streamlit as st

from project_router import init_hub_page, load_project_module, render_profile_sidebar, title_from_file

base_dir = Path(__file__).parent / "bankingprojects"
project_file = st.query_params.get("project")

if project_file:
    project_path = base_dir / project_file
    init_hub_page(
        index_title="Banking and Finance",
        project_title=title_from_file(project_path, "Banking ML Project"),
    )
    load_project_module(project_path)
else:
    init_hub_page(index_title="Thomas Tellner | Data Science Portfolio")

render_profile_sidebar()

st.title("Machine Learning for Banking and Finance")
st.write(
    """ML/AI for Banking and Lending. Explore and run machine learning demos below.

Projects that are spread across multiple Project Cards can be followed in order
by the numbering in the title:

PD: Probability of Default. Currently PD.1-PD.6

LGD: Loss Given Default. Currently under construction.

EAD: Exposure at Default. Currently under construction.

Any projects without a number similar to these is standalone."""
)

if not base_dir.exists():
    st.warning(f"No ML project directory found at: {base_dir}")
else:
    project_files = [
        f.name for f in base_dir.iterdir() if f.suffix == ".py" and "_functions" not in f.name
    ]

    def sort_key(filename):
        if "data_pipeline" in filename and "functions" not in filename:
            return (0, filename)
        if "var_metadata_analysis" in filename:
            return (1, filename)
        if "feat_eng_analysis" in filename:
            return (2, filename)
        if "iv_woe_analysis" in filename:
            return (3, filename)
        if "collinear_analysis" in filename:
            return (4, filename)
        if "logreg_model_analysis" in filename:
            return (5, filename)
        if "streamlit_app" in filename:
            return (6, filename)
        return (7, filename)

    project_files = sorted(project_files, key=sort_key)

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
                    st.markdown("---")
