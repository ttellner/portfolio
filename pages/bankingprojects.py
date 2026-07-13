"""
Machine Learning for Banking and Finance
ML/AI for Banking and Lending. Explore and run machine learning demos below.
Projects that are spread across multiple Project Cards can be followed in order
by the numbering in the title:

PD: Probability of Default. Currently PD.1-PD.6
LGD: Loss Given Default. Currently under construction.
EAD: Exposure at Default. Currently under construction.

Any projects without a number similar to these is standalone.
https://via.placeholder.com/400x200?text=Banking+Finance
"""
import importlib.util
import re
from pathlib import Path

import streamlit as st

from theme import apply_theme

base_dir = Path(__file__).parent / "bankingprojects"


def _project_title(project_path: Path) -> str:
    content = project_path.read_text(encoding="utf-8")
    docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if docstring:
        lines = [line.strip() for line in docstring.group(1).split("\n") if line.strip()]
        if lines:
            return lines[0]
    return project_path.stem.replace("_", " ").title()


project_file = st.query_params.get("project")

if project_file:
    project_path = base_dir / project_file
    page_title = _project_title(project_path) if project_path.exists() else "Banking ML Project"
    st.set_page_config(page_title=page_title, layout="wide")
else:
    st.set_page_config(
        page_title="Thomas Tellner | Data Science Portfolio",
        layout="wide",
    )

apply_theme()

st.markdown(
    """
<style>
section[data-testid="stSidebarNav"] { display: none; }
nav[aria-label="Secondary"] { display: none; }
</style>
""",
    unsafe_allow_html=True,
)

if project_file:
    project_path = base_dir / project_file
    if project_path.exists() and project_path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("project_module", str(project_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "main"):
                module.main()
            st.stop()
        st.error(f"Could not load: {project_path}")
    else:
        st.error(f"Project file not found: {project_path}")
    st.stop()

with st.sidebar:
    st.title("Thomas Tellner")
    st.markdown("Data Science | ML & AI | GenAI")
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")
    st.caption("Made using Streamlit")

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
        f.name
        for f in base_dir.iterdir()
        if f.suffix == ".py" and "_functions" not in f.name
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
            for j, project_file_name in enumerate(project_files[i : i + num_cols]):
                with cols[j]:
                    path = base_dir / project_file_name
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring:
                        lines = [
                            line.strip()
                            for line in docstring.group(1).split("\n")
                            if line.strip()
                        ]
                        title = lines[0] if lines else project_file_name.replace(".py", "")
                        desc = lines[1] if len(lines) > 1 else ""
                    else:
                        title, desc = project_file_name.replace(".py", ""), ""

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
                        key=f"open_{project_file_name}",
                        on_click=lambda f=project_file_name: st.query_params.update(
                            {"project": f}
                        ),
                    )
                    st.markdown("---")
