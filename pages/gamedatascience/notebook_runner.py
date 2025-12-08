"""
Helper module for executing notebook cells in Streamlit.
Supports both Python and R code execution.
"""
import streamlit as st
import subprocess
import tempfile
import os
from pathlib import Path
import json
import sys

def find_r_executable():
    """Find R executable on the system."""
    possible_paths = [
        r"C:/Program Files/R/R-4.4.1/bin/x64/Rscript.exe",
        r"C:/Program Files/R/R-4.3.3/bin/x64/Rscript.exe",
        r"C:/Program Files/R/R-4.3.2/bin/x64/Rscript.exe",
        "Rscript",  # Try system PATH
        "/usr/bin/Rscript",  # Linux
        "/usr/local/bin/Rscript",  # Linux alternative
    ]
    
    for r_path in possible_paths:
        try:
            test_process = subprocess.Popen(
                [r_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                test_result = test_process.communicate(timeout=5)
            except Exception:
                test_process.kill()
                test_process.wait()
                continue
            if test_process.returncode == 0 or (test_result[0] and len(test_result[0]) > 0):
                return r_path
        except (FileNotFoundError, OSError):
            continue
    return None

def get_persistent_namespace():
    """Get or create a persistent namespace for code execution."""
    if 'notebook_namespace' not in st.session_state:
        # Initialize namespace with common libraries
        namespace = {
            '__builtins__': __builtins__,
            'st': st,
        }
        
        # Try to import common libraries
        try:
            namespace['pd'] = __import__('pandas')
        except:
            pass
        try:
            namespace['np'] = __import__('numpy')
        except:
            pass
        try:
            namespace['plt'] = __import__('matplotlib.pyplot')
            # Configure matplotlib to work with Streamlit
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
        except:
            pass
        try:
            namespace['sns'] = __import__('seaborn')
        except:
            pass
        try:
            namespace['scipy'] = __import__('scipy')
            namespace['stats'] = __import__('scipy.stats')
        except:
            pass
        try:
            namespace['sklearn'] = __import__('sklearn')
        except:
            pass
        
        st.session_state.notebook_namespace = namespace
    
    return st.session_state.notebook_namespace

def execute_python_code(code, cell_index):
    """Execute Python code and return output using persistent namespace."""
    try:
        # Get persistent namespace
        namespace = get_persistent_namespace()
        
        # Capture stdout and stderr
        from io import StringIO
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_output = StringIO()
        sys.stderr = captured_error = StringIO()
        
        try:
            # Check if code is a single expression (like a variable or function call)
            code_stripped = code.strip()
            is_expression = (not code_stripped.startswith('#') and 
                           not any(keyword in code_stripped for keyword in ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'with ']) and
                           '\n' not in code_stripped)
            
            # Execute code
            if is_expression:
                # For expressions, use eval to get the result
                try:
                    result = eval(code, namespace)
                    if result is not None:
                        # Display the result
                        st.write("Result:")
                        st.write(result)
                except:
                    # If eval fails, try exec
                    exec(code, namespace)
            else:
                exec(code, namespace)
            
            # Get outputs
            stdout_output = captured_output.getvalue()
            stderr_output = captured_error.getvalue()
            
            # Combine outputs
            output_parts = []
            if stdout_output:
                output_parts.append(stdout_output)
            if stderr_output:
                output_parts.append(f"Warnings/Errors:\n{stderr_output}")
            
            output = "\n".join(output_parts) if output_parts else None
            
            # Check if matplotlib figure was created
            if 'plt' in namespace:
                try:
                    fig = namespace['plt'].gcf()
                    if fig.get_axes():  # If figure has axes, it was plotted
                        st.pyplot(fig)
                        namespace['plt'].close(fig)  # Close to free memory
                except:
                    pass
            
            return output, None
        except Exception as e:
            error_msg = str(e)
            stderr_value = captured_error.getvalue()
            if stderr_value:
                error_msg += f"\n\nStderr: {stderr_value}"
            return None, error_msg
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    except Exception as e:
        return None, f"Execution error: {str(e)}"

def execute_r_code(code, cell_index, working_dir=None):
    """Execute R code using Rscript and return output."""
    r_path = find_r_executable()
    
    if not r_path:
        return None, "R is not installed or not found in PATH. Please install R to run R code."
    
    try:
        # Create a temporary R script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(code)
            tmp_script_path = tmp_file.name
        
        try:
            # Execute R script
            if working_dir:
                process = subprocess.Popen(
                    [r_path, tmp_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(working_dir)
                )
            else:
                process = subprocess.Popen(
                    [r_path, tmp_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            stdout, stderr = process.communicate(timeout=30)
            
            if process.returncode == 0:
                return stdout, None
            else:
                return None, f"R error: {stderr}"
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_script_path)
            except:
                pass
    except subprocess.TimeoutExpired:
        process.kill()
        return None, "R script execution timed out (30 seconds)"
    except Exception as e:
        return None, f"Error executing R code: {str(e)}"

def is_r_code(code):
    """Detect if code is R code (simple heuristic)."""
    r_indicators = [
        'library(',
        'require(',
        '<-',  # R assignment operator
        'c(',   # R vector constructor
        'data.frame(',
        'read.csv(',
    ]
    code_lower = code.lower()
    return any(indicator in code_lower for indicator in r_indicators)

def display_notebook_interactive(notebook_path):
    """Display notebook with interactive code execution."""
    base_dir = Path(notebook_path).parent
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
    except Exception as e:
        st.error(f"Error loading notebook: {e}")
        return
    
    cells = notebook.get('cells', [])
    
    # Check if R is available
    r_available = find_r_executable() is not None
    if not r_available:
        st.info("ℹ️ R is not available. R code cells will not be executable. Install R to enable R code execution.")
    
    # Add a button to clear/reset the namespace
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Clear Variables", help="Clear all variables and reset the execution environment"):
            if 'notebook_namespace' in st.session_state:
                del st.session_state.notebook_namespace
            st.success("Variables cleared! Re-run cells to start fresh.")
            st.rerun()
    
    # Display cells
    for i, cell in enumerate(cells):
        cell_type = cell.get('cell_type', 'code')
        source = cell.get('source', [])
        
        if isinstance(source, list):
            source = ''.join(source)
        
        if cell_type == 'markdown':
            st.markdown(source)
        elif cell_type == 'code':
            # Check if this is R code
            is_r = is_r_code(source)
            
            # Display code
            language = 'r' if is_r else 'python'
            st.code(source, language=language)
            
            # Execution button
            col1, col2 = st.columns([1, 4])
            with col1:
                if is_r:
                    execute_button = st.button(f"▶ Run R Code", key=f"run_r_{i}", disabled=not r_available)
                else:
                    execute_button = st.button(f"▶ Run Python", key=f"run_py_{i}")
            
            # Execute code when button is clicked
            if execute_button:
                with st.spinner("Executing code..."):
                    if is_r:
                        output, error = execute_r_code(source, i, working_dir=base_dir)
                        if error:
                            st.error(f"R Error: {error}")
                        elif output:
                            st.text("R Output:")
                            st.code(output, language='text')
                        else:
                            st.success("R code executed successfully (no output)")
                    else:
                        output, error = execute_python_code(source, i)
                        if error:
                            st.error(f"Python Error: {error}")
                        elif output:
                            st.text("Python Output:")
                            st.code(output, language='text')
                        else:
                            st.success("Python code executed successfully (no output or plot displayed above)")
            
            st.divider()

