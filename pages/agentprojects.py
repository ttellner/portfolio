"""
AI Agent Engineering Projects
Multi-agent lending demos: fraud triage, credit underwriting, default risk, and cross-sell.
https://via.placeholder.com/400x200?text=AI+Agent+Projects
"""
import importlib.util
import re
from pathlib import Path

import streamlit as st

from theme import apply_theme

st.set_page_config(
    page_title="Thomas Tellner | AI Agent Projects",
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

st.title("AI Agent Engineering Projects")
st.write(
    """
    Agentic AI demos inspired by cognitive architecture patterns (perceive → reason → plan → act → learn).
    Current focus: lender workflows for application fraud, creditworthiness, default-risk scoring,
    and relationship cross-sell — all running on mock data for portfolio-safe deployment.
    """
)

base_dir = Path(__file__).parent / "agentprojects"

query_params = st.query_params
if "project" in query_params:
    project_file = query_params["project"]
    project_path = base_dir / project_file

    if project_path.exists():
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

if not base_dir.exists():
    st.warning(f"No agent project directory found at: {base_dir}")
else:
    project_files = [
        f.name
        for f in base_dir.iterdir()
        if f.suffix == ".py" and "_functions" not in f.name and f.name != "__init__.py"
    ]

    def sort_key(filename: str):
        if "lending_underwriting_demo" in filename:
            return (0, filename)
        return (1, filename)

    project_files = sorted(project_files, key=sort_key)

    if not project_files:
        st.info("No agent projects found in this folder.")
    else:
        num_cols = 3
        for i in range(0, len(project_files), num_cols):
            cols = st.columns(num_cols)
            for j, project_file in enumerate(project_files[i : i + num_cols]):
                with cols[j]:
                    path = base_dir / project_file
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring:
                        lines = [line.strip() for line in docstring.group(1).split("\n") if line.strip()]
                        title = lines[0] if lines else project_file.replace(".py", "")
                        desc = lines[1] if len(lines) > 1 else ""
                    else:
                        title, desc = project_file.replace(".py", ""), ""

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
                        key=f"open_{project_file}",
                        on_click=lambda f=project_file: st.query_params.update({"project": f}),
                    )
                    st.markdown("---")
