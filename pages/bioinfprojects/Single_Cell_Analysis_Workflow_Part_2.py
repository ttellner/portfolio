"""
Single Cell Analysis Part 2
Python/TensorFlow VAE Analysis and Clustering
"""
import streamlit as st
import json
import os
from pathlib import Path

st.set_page_config(layout="wide", page_title="Single-Cell Analysis Part 2")

st.markdown("## Single-Cell Analysis Workflow - Python/TensorFlow Analysis")
st.markdown("#### VAE-based Dimensionality Reduction and Clustering - Code Display Only")

# Path to notebook
NOTEBOOK_PATH = Path(__file__).parent / "Tellner_Thomas_Capstone5.ipynb"

@st.cache_data
def load_notebook():
    """Load and parse the Jupyter notebook"""
    try:
        with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        return notebook
    except Exception as e:
        st.error(f"Error loading notebook: {e}")
        return None

def extract_cell_content(cell):
    """Extract code or markdown content from a cell"""
    if 'source' in cell:
        if isinstance(cell['source'], list):
            return ''.join(cell['source'])
        return cell['source']
    return ""

def format_output(output):
    """Format output for display"""
    output_type = output.get('output_type', '')
    
    if output_type == 'stream':
        # Text output
        text = output.get('text', '')
        if isinstance(text, list):
            text = ''.join(text)
        return ('text', text)
    
    elif output_type == 'display_data' or output_type == 'execute_result':
        # Data output (HTML, images, etc.)
        data = output.get('data', {})
        
        # Check for images
        if 'image/png' in data:
            import base64
            img_data = data['image/png']
            return ('image', img_data)
        
        # Check for HTML
        if 'text/html' in data:
            html = data['text/html']
            if isinstance(html, list):
                html = ''.join(html)
            return ('html', html)
        
        # Check for plain text
        if 'text/plain' in data:
            text = data['text/plain']
            if isinstance(text, list):
                text = ''.join(text)
            return ('text', text)
    
    elif output_type == 'error':
        # Error output
        error_name = output.get('ename', 'Error')
        error_value = output.get('evalue', '')
        traceback = output.get('traceback', [])
        if isinstance(traceback, list):
            traceback = '\n'.join(traceback)
        return ('error', f"{error_name}: {error_value}\n{traceback}")
    
    return ('text', str(output))

def display_cell(cell, cell_num, cell_index):
    """Display a single notebook cell"""
    cell_type = cell.get('cell_type', '')
    execution_count = cell.get('execution_count')
    
    if cell_type == 'code':
        code = extract_cell_content(cell)
        if code.strip():
            # Display cell number
            st.markdown(f"### Cell {cell_num}")
            
            # Display code in read-only format
            st.code(code, language='python')
            
            # Display outputs in expandable sections
            outputs = cell.get('outputs', [])
            if outputs:
                with st.expander(f"📊 View Outputs ({len(outputs)} output(s))", expanded=False):
                    for i, output in enumerate(outputs):
                        output_type, content = format_output(output)
                        unique_key = f"cell_{cell_index}_output_{i}"
                        
                        if output_type == 'image':
                            try:
                                import base64
                                from io import BytesIO
                                from PIL import Image
                                img_bytes = base64.b64decode(content)
                                img = Image.open(BytesIO(img_bytes))
                                st.image(img, caption=f"Output {i+1}: Image")
                            except Exception as e:
                                st.error(f"Error displaying image: {e}")
                        
                        elif output_type == 'html':
                            st.markdown(f"**Output {i+1}: HTML**")
                            # For very long HTML, show in expandable
                            if len(content) > 50000:
                                with st.expander("View HTML Output"):
                                    st.components.v1.html(content, height=600, scrolling=True)
                            else:
                                st.components.v1.html(content, height=400, scrolling=True)
                        
                        elif output_type == 'error':
                            st.error(f"**Output {i+1}: Error**")
                            st.code(content, language='text')
                        
                        else:  # text
                            st.markdown(f"**Output {i+1}: Text**")
                            # Truncate very long outputs
                            if len(content) > 5000:
                                st.text(content[:5000] + f"\n\n... (truncated, {len(content)} total characters)")
                                with st.expander("View full output"):
                                    st.text_area("Full output", content, height=400, key=f"{unique_key}_full")
                            else:
                                st.text_area("", content, height=min(200, len(content.split('\n')) * 20), key=f"{unique_key}_text", label_visibility="collapsed")
            
            st.divider()
    
    elif cell_type == 'markdown':
        markdown_content = extract_cell_content(cell)
        if markdown_content.strip():
            st.markdown(f"### Cell {cell_num} (Markdown)")
            st.markdown(markdown_content)
            st.divider()

# Main app
notebook = load_notebook()

if notebook:
    st.sidebar.markdown("### Navigation")
    
    # Get all code cells for navigation
    code_cells = []
    for i, cell in enumerate(notebook.get('cells', [])):
        if cell.get('cell_type') == 'code':
            code = extract_cell_content(cell)
            if code.strip():
                code_cells.append(i)
    
    # Sidebar navigation
    if code_cells:
        selected_cell_idx = st.sidebar.selectbox(
            "Jump to Cell",
            options=code_cells,
            format_func=lambda x: f"Cell {x+1}"
        )
        
        if st.sidebar.button("Go to Selected Cell"):
            st.session_state.scroll_to = selected_cell_idx
    
    # Display all cells
    st.markdown("---")
    st.markdown("### Notebook Contents")
    st.info("💡 **Note**: This is a read-only display. Code cannot be executed here. Outputs are shown in expandable sections below each code cell.")
    
    # Statistics
    total_cells = len([c for c in notebook.get('cells', []) if c.get('cell_type') == 'code' and extract_cell_content(c).strip()])
    total_outputs = sum(len(c.get('outputs', [])) for c in notebook.get('cells', []) if c.get('cell_type') == 'code')
    st.caption(f"📊 {total_cells} code cells | {total_outputs} total outputs")
    
    cell_num = 1
    for i, cell in enumerate(notebook.get('cells', [])):
        cell_type = cell.get('cell_type', '')
        
        if cell_type == 'code':
            code = extract_cell_content(cell)
            if code.strip():  # Only display non-empty cells
                display_cell(cell, cell_num, i)
                cell_num += 1
        elif cell_type == 'markdown':
            display_cell(cell, cell_num, i)
            cell_num += 1
    
    st.markdown("---")
    st.markdown("### Summary")
    st.success(f"✅ Displayed {cell_num-1} cells from the notebook")
    
else:
    st.error("Could not load notebook. Please check the file path.")
