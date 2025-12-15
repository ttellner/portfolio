"""
Single Cell Analysis Part 1
R/Seurat Data Ingestion, QC and Prep
Displays pre-rendered HTML from R Markdown
"""
import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide")

st.markdown("## Single-Cell Analysis Workflow - R/Seurat Analysis")
st.markdown("#### R/Seurat Data Ingestion, QC and Prep")

# Path to pre-rendered HTML file
BASE_DIR = Path(__file__).parent
HTML_FILE = BASE_DIR / "Tellner_Thomas_Capstone_Project_Part1.html"

# Check if HTML file exists
if not HTML_FILE.exists():
    st.error(f"**HTML file not found:** {HTML_FILE}")
    st.info("""
    The pre-rendered HTML file is missing. 
    
    To generate it:
    1. Open `Tellner_Thomas_Capstone_Project_Part1.Rmd` in RStudio
    2. Click "Knit" to render the document
    3. Save the resulting HTML file as `Tellner_Thomas_Capstone_Project_Part1.html`
    4. Place it in the same directory as this Python file
    """)
    st.stop()

# Read and display the HTML file
try:
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Display the HTML content
    st.components.v1.html(html_content, height=800, scrolling=True)
    
    # Also provide a download link
    with open(HTML_FILE, 'rb') as f:
        st.download_button(
            label="📥 Download HTML Report",
            data=f.read(),
            file_name="Tellner_Thomas_Capstone_Project_Part1.html",
            mime="text/html"
        )
    
except Exception as e:
    st.error(f"**Error loading HTML file:** {e}")
    st.exception(e)
