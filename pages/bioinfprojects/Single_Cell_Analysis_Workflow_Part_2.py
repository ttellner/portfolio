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

def clean_code(code):
    """Remove commented lines containing KNN references"""
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Check if line is a comment and contains KNN (case-insensitive)
        stripped = line.lstrip()
        if stripped.startswith('#') and 'knn' in stripped.lower():
            # Skip this commented KNN line
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def extract_summary_df_from_outputs(outputs):
    """Extract summary_df from cell outputs - looks for DataFrame with cluster, cell_types, confidence, reasoning columns"""
    import pandas as pd
    import re
    from io import StringIO
    
    # Combine all text outputs first
    all_text = ""
    for output in outputs:
        output_type = output.get('output_type', '')
        data = output.get('data', {})
        
        # Check text/plain output
        if 'text/plain' in data:
            text = data['text/plain']
            if isinstance(text, list):
                text = ''.join(text)
            all_text += text + "\n"
        
        # Check stream output (print statements)
        if output_type == 'stream':
            text = output.get('text', '')
            if isinstance(text, list):
                text = ''.join(text)
            all_text += text
    
    # Now search in combined text
    if all_text:
        # Look for "Summary DataFrame:" pattern
        if 'Summary DataFrame:' in all_text or ('cluster' in all_text.lower() and 'cell_types' in all_text.lower() and 'confidence' in all_text.lower()):
            # Try to extract the table part
            lines = all_text.split('\n')
            start_idx = None
            for i, line in enumerate(lines):
                # Look for header line with cluster and cell_types
                if 'cluster' in line.lower() and 'cell_types' in line.lower():
                    start_idx = i
                    break
            
            if start_idx is not None:
                # Extract header and data rows
                try:
                    # Read the table section - get lines until we hit a separator or empty line
                    table_lines = []
                    for line in lines[start_idx:start_idx+20]:  # Check up to 20 lines (should be enough for 9 clusters)
                        stripped = line.strip()
                        if not stripped:
                            if len(table_lines) > 1:  # We have at least header + 1 data row
                                break
                            continue
                        # Skip separator lines
                        if stripped.startswith('=') and len(stripped) > 10:
                            if len(table_lines) > 1:
                                break
                            continue
                        table_lines.append(line)
                    
                    if len(table_lines) > 1:
                        # Create a string representation of the table
                        table_str = '\n'.join(table_lines)
                        # Try to parse with pandas - first try fixed width (for to_string() format)
                        try:
                            df = pd.read_fwf(StringIO(table_str), header=0)
                            # Clean column names
                            df.columns = df.columns.str.strip()
                            if 'cluster' in df.columns and 'cell_types' in df.columns:
                                return df
                        except:
                            pass
                        
                        # Try space-separated as fallback
                        try:
                            df = pd.read_csv(StringIO(table_str), sep=r'\s{2,}', header=0, engine='python')
                            df.columns = df.columns.str.strip()
                            if 'cluster' in df.columns and 'cell_types' in df.columns:
                                return df
                        except:
                            pass
                except Exception as e:
                    pass
        
    # Also check HTML outputs separately
    for output in outputs:
        output_type = output.get('output_type', '')
        data = output.get('data', {})
        
        # Check HTML output for dataframe
        if 'text/html' in data:
            html = data['text/html']
            if isinstance(html, list):
                html = ''.join(html)
            
            if 'dataframe' in html.lower() and 'cluster' in html.lower() and 'cell_types' in html.lower():
                try:
                    df_list = pd.read_html(html)
                    for df in df_list:
                        if 'cluster' in df.columns and 'cell_types' in df.columns:
                            # Select only the required columns
                            required_cols = ['cluster', 'cell_types', 'confidence', 'reasoning']
                            available_cols = [col for col in required_cols if col in df.columns]
                            if len(available_cols) >= 2:  # At least cluster and cell_types
                                return df[available_cols]
                except:
                    pass
    
    # Fallback: Try to extract from JSON in text outputs
    import json
    for output in outputs:
        output_type = output.get('output_type', '')
        data = output.get('data', {})
        text = ""
        
        if 'text/plain' in data:
            text = data['text/plain']
            if isinstance(text, list):
                text = ''.join(text)
        elif output_type == 'stream':
            text = output.get('text', '')
            if isinstance(text, list):
                text = ''.join(text)
        
        # Try to find JSON structure with cluster data
        if text and ('cluster_' in text or '"cluster' in text):
            try:
                # Try to extract JSON from text
                # Look for JSON-like structure
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text[json_start:json_end]
                    parsed = json.loads(json_str)
                    # Check if it has cluster data
                    if isinstance(parsed, dict) and any('cluster' in str(k).lower() for k in parsed.keys()):
                        # Reconstruct DataFrame from JSON
                        summary_data = []
                        for key, value in parsed.items():
                            if 'cluster' in str(key).lower() and isinstance(value, dict):
                                cluster_num = int(str(key).replace('cluster_', '').replace('cluster', ''))
                                summary_data.append({
                                    'cluster': cluster_num,
                                    'cell_types': ', '.join(value.get('cell_types', [])) if isinstance(value.get('cell_types'), list) else str(value.get('cell_types', 'Unknown')),
                                    'confidence': value.get('confidence', 'Unknown'),
                                    'reasoning': value.get('reasoning', '')
                                })
                        if summary_data:
                            df = pd.DataFrame(summary_data)
                            return df
            except:
                pass
    
    return None

def display_cell(cell, cell_num, cell_index, is_last_cell=False):
    """Display a single notebook cell"""
    cell_type = cell.get('cell_type', '')
    execution_count = cell.get('execution_count')
    
    if cell_type == 'code':
        code = extract_cell_content(cell)
        if code.strip():
            # Display cell number
            st.markdown(f"### Cell {cell_num}")
            
            # Clean code to remove commented KNN lines
            cleaned_code = clean_code(code)
            
            # Display code in read-only format
            st.code(cleaned_code, language='python')
            
            # Check if this is the training loop cell (suppress long outputs)
            is_training_loop = (
                'for i in range(1,n)' in code or 
                'vae_fit(i)' in code or
                ('losses = []' in code and 'vae_fit' in code)
            )
            
            # Check if this is the LLM cell (last cell)
            is_llm_cell = 'identify_cell_types_with_llm' in code
            
            # Display outputs in expandable sections
            outputs = cell.get('outputs', [])
            if outputs:
                # For LLM cell (last cell), only show summary_df
                if is_llm_cell or is_last_cell:
                    summary_df = extract_summary_df_from_outputs(outputs)
                    if summary_df is not None:
                        # Select only required columns
                        required_cols = ['cluster', 'cell_types', 'confidence', 'reasoning']
                        available_cols = [col for col in required_cols if col in summary_df.columns]
                        if available_cols:
                            display_df = summary_df[available_cols].copy()
                            st.dataframe(display_df, use_container_width=True)
                        else:
                            st.dataframe(summary_df, use_container_width=True)
                    else:
                        st.info("Summary DataFrame not found in outputs.")
                # Suppress outputs for training loop cell
                elif is_training_loop:
                    st.info(f"⚠️ Output suppressed (extremely long training output with {len(outputs)} output(s)). This cell contains the VAE training loop.")
                else:
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
                                # Check if this is a DataFrame HTML output (contains table structure)
                                if 'dataframe' in content.lower() and '<table' in content.lower():
                                    try:
                                        import pandas as pd
                                        # Parse HTML table and convert to DataFrame
                                        # pd.read_html can parse HTML directly
                                        df_list = pd.read_html(content)
                                        if df_list:
                                            df = df_list[0]
                                            # Display with proper alignment
                                            st.dataframe(df, use_container_width=True)
                                        else:
                                            # Fallback to HTML rendering
                                            st.components.v1.html(content, height=400, scrolling=True)
                                    except Exception as e:
                                        # If parsing fails, fallback to HTML rendering
                                        st.components.v1.html(content, height=400, scrolling=True)
                                else:
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
    
    # Find the last code cell
    last_code_cell_index = None
    for i in range(len(notebook.get('cells', [])) - 1, -1, -1):
        cell = notebook.get('cells', [])[i]
        if cell.get('cell_type') == 'code':
            code = extract_cell_content(cell)
            if code.strip():
                last_code_cell_index = i
                break
    
    cell_num = 1
    for i, cell in enumerate(notebook.get('cells', [])):
        cell_type = cell.get('cell_type', '')
        
        if cell_type == 'code':
            code = extract_cell_content(cell)
            if code.strip():  # Only display non-empty cells
                is_last = (i == last_code_cell_index)
                display_cell(cell, cell_num, i, is_last_cell=is_last)
                cell_num += 1
        elif cell_type == 'markdown':
            display_cell(cell, cell_num, i, is_last_cell=False)
            cell_num += 1
    
    st.markdown("---")
    st.markdown("### Summary")
    st.success(f"✅ Displayed {cell_num-1} cells from the notebook")
    
else:
    st.error("Could not load notebook. Please check the file path.")
