"""
Single Cell Analysis Part 1
R/Seurat Data Ingestion, QC and Prep
https://via.placeholder.com/400x200?text=Single+Cell+Analysis
"""
import streamlit as st
import subprocess
import os
import tempfile

st.set_page_config(layout="wide")

st.markdown("## Single-Cell Analysis Workflow - R/Seurat Analysis")
st.markdown("#### R/Seurat Data Ingestion, QC and Prep - Be patient! There's a lot to render below.")

# Paths - use dynamic paths based on file location
from pathlib import Path
BASE_DIR = Path(__file__).parent
RMD_FILE = BASE_DIR / "Tellner_Thomas_Capstone_Project_Part1.Rmd"
WORK_DIR = BASE_DIR

# Try to find R - check common locations
R_PATH = None
possible_r_paths = [
    r"C:/Program Files/R/R-4.4.1/bin/x64/Rscript.exe",
    r"C:/Program Files/R/R-4.3.3/bin/x64/Rscript.exe",
    r"C:/Program Files/R/R-4.3.2/bin/x64/Rscript.exe",
    "Rscript",  # Try system PATH
    "/usr/bin/Rscript",  # Linux
    "/usr/local/bin/Rscript",  # Linux alternative
]

for r_path in possible_r_paths:
    try:
        # Try to run R with --version to check if it exists
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
            R_PATH = r_path
            break
    except (FileNotFoundError, OSError):
        continue

# First, check if pandoc is available and try to find RStudio's pandoc
check_pandoc_script = '''# Check if pandoc is available and find it
library(rmarkdown)

# Common pandoc installation paths to check
username <- Sys.getenv("USERNAME", "")
local_appdata <- Sys.getenv("LOCALAPPDATA", "")
program_files <- Sys.getenv("PROGRAMFILES", "")
program_files_x86 <- Sys.getenv("PROGRAMFILES(X86)", "")

common_paths <- c(
    "C:/Program Files/RStudio/resources/app/bin/pandoc",
    "C:/Program Files (x86)/RStudio/resources/app/bin/pandoc",
    "C:/Program Files/Pandoc",
    "C:/Program Files (x86)/Pandoc"
)

if (username != "") {
    common_paths <- c(common_paths, paste0("C:/Users/", username, "/AppData/Local/Pandoc"))
}
if (local_appdata != "") {
    common_paths <- c(common_paths, file.path(local_appdata, "Pandoc"))
}
if (program_files != "") {
    common_paths <- c(common_paths, file.path(program_files, "Pandoc"))
}
if (program_files_x86 != "") {
    common_paths <- c(common_paths, file.path(program_files_x86, "Pandoc"))
}

# Ensure common_paths is always defined
if (!exists("common_paths") || is.null(common_paths)) {
    common_paths <- character(0)
}

# Function to check if pandoc exists at a path
check_pandoc_path <- function(base_path) {
    if (is.na(base_path) || base_path == "") return(NULL)
    
    # Try different executable names
    exe_names <- c("pandoc.exe", "pandoc")
    for (exe_name in exe_names) {
        full_path <- file.path(base_path, exe_name)
        if (file.exists(full_path)) {
            return(full_path)
        }
    }
    return(NULL)
}

# Try to find pandoc using rmarkdown::find_pandoc first
pandoc_info <- tryCatch({
    find_pandoc()
}, error = function(e) {
    NULL
})

pandoc_path <- NULL

# If rmarkdown found it, use that
if (!is.null(pandoc_info) && !is.null(pandoc_info$dir)) {
    pandoc_path <- file.path(pandoc_info$dir, "pandoc.exe")
    if (!file.exists(pandoc_path)) {
        pandoc_path <- file.path(pandoc_info$dir, "pandoc")
    }
    if (file.exists(pandoc_path)) {
        Sys.setenv(PANDOC = pandoc_path)
        cat("PANDOC_PATH:", pandoc_path, "\\n")
    } else {
        pandoc_path <- NULL
    }
}

# If not found, try common paths
if ((is.null(pandoc_path) || !file.exists(pandoc_path)) && exists("common_paths") && length(common_paths) > 0) {
    for (base_path in common_paths) {
        if (!is.na(base_path) && base_path != "") {
            found_path <- check_pandoc_path(base_path)
            if (!is.null(found_path)) {
                pandoc_path <- found_path
                Sys.setenv(PANDOC = pandoc_path)
                Sys.setenv(PATH = paste(Sys.getenv("PATH"), dirname(pandoc_path), sep = ";"))
                cat("PANDOC_PATH:", pandoc_path, "\\n")
                break
            }
        }
    }
}

# Also check system PATH
if (is.null(pandoc_path) || !file.exists(pandoc_path)) {
    system_pandoc <- Sys.which("pandoc")
    if (system_pandoc != "") {
        pandoc_path <- system_pandoc
        Sys.setenv(PANDOC = pandoc_path)
        cat("PANDOC_PATH:", pandoc_path, "\\n")
    }
}

# Check if pandoc is now available
if (pandoc_available()) {
    cat("PANDOC_FOUND\\n")
    cat("PANDOC_VERSION:", as.character(pandoc_version()), "\\n")
    if (!is.null(pandoc_path)) {
        cat("PANDOC_DIR:", dirname(pandoc_path), "\\n")
    }
    quit(status = 0)
} else {
    cat("PANDOC_NOT_FOUND\\n")
    if (!is.null(pandoc_path)) {
        cat("ATTEMPTED_PATH:", pandoc_path, "\\n")
    }
    quit(status = 1)
}
'''

# Create a temporary R script to render the RMD file
# Convert paths to R-friendly format (forward slashes)
work_dir_r = str(WORK_DIR).replace("\\", "/")
rmd_file_r = str(RMD_FILE).replace("\\", "/")

render_script = f'''# Set working directory
setwd("{work_dir_r}")

# Load rmarkdown library
library(rmarkdown)

# Common pandoc installation paths to check
username <- Sys.getenv("USERNAME", "")
local_appdata <- Sys.getenv("LOCALAPPDATA", "")
program_files <- Sys.getenv("PROGRAMFILES", "")
program_files_x86 <- Sys.getenv("PROGRAMFILES(X86)", "")

common_paths <- c(
    "C:/Program Files/RStudio/resources/app/bin/pandoc",
    "C:/Program Files (x86)/RStudio/resources/app/bin/pandoc",
    "C:/Program Files/Pandoc",
    "C:/Program Files (x86)/Pandoc"
)

if (username != "") {{
    common_paths <- c(common_paths, paste0("C:/Users/", username, "/AppData/Local/Pandoc"))
}}
if (local_appdata != "") {{
    common_paths <- c(common_paths, file.path(local_appdata, "Pandoc"))
}}
if (program_files != "") {{
    common_paths <- c(common_paths, file.path(program_files, "Pandoc"))
}}
if (program_files_x86 != "") {{
    common_paths <- c(common_paths, file.path(program_files_x86, "Pandoc"))
}}

# Ensure common_paths is always defined
if (!exists("common_paths") || is.null(common_paths)) {{
    common_paths <- character(0)
}}

# Function to check if pandoc exists at a path
check_pandoc_path <- function(base_path) {{
    if (is.na(base_path) || base_path == "") return(NULL)
    exe_names <- c("pandoc.exe", "pandoc")
    for (exe_name in exe_names) {{
        full_path <- file.path(base_path, exe_name)
        if (file.exists(full_path)) {{
            return(full_path)
        }}
    }}
    return(NULL)
}}

# Try to find pandoc using rmarkdown::find_pandoc first
pandoc_info <- tryCatch({{
    find_pandoc()
}}, error = function(e) {{
    NULL
}})

pandoc_path <- NULL

# If rmarkdown found it, use that
if (!is.null(pandoc_info) && !is.null(pandoc_info$dir)) {{
    pandoc_path <- file.path(pandoc_info$dir, "pandoc.exe")
    if (!file.exists(pandoc_path)) {{
        pandoc_path <- file.path(pandoc_info$dir, "pandoc")
    }}
    if (file.exists(pandoc_path)) {{
        Sys.setenv(PANDOC = pandoc_path)
        Sys.setenv(PATH = paste(Sys.getenv("PATH"), dirname(pandoc_path), sep = ";"))
    }} else {{
        pandoc_path <- NULL
    }}
}}

# If not found, try common paths
if ((is.null(pandoc_path) || !file.exists(pandoc_path)) && exists("common_paths") && length(common_paths) > 0) {{
    for (base_path in common_paths) {{
        if (!is.na(base_path) && base_path != "") {{
            found_path <- check_pandoc_path(base_path)
            if (!is.null(found_path)) {{
                pandoc_path <- found_path
                Sys.setenv(PANDOC = pandoc_path)
                Sys.setenv(PATH = paste(Sys.getenv("PATH"), dirname(pandoc_path), sep = ";"))
                break
            }}
        }}
    }}
}}

# Also check system PATH
if (is.null(pandoc_path) || !file.exists(pandoc_path)) {{
    system_pandoc <- Sys.which("pandoc")
    if (system_pandoc != "") {{
        pandoc_path <- system_pandoc
        Sys.setenv(PANDOC = pandoc_path)
    }}
}}

# Check pandoc availability
if (!pandoc_available()) {{
    cat("PANDOC_ERROR: pandoc is not available. Please install pandoc.\\n")
    cat("Installation options:\\n")
    cat("1. Install RStudio (includes pandoc): ")
    cat("https://www.rstudio.com/products/rstudio/download/\\n")
    cat("2. Install pandoc directly: https://pandoc.org/installing.html\\n")
    cat("3. Use chocolatey: choco install pandoc\\n")
    stop("pandoc not available")
}}

# Render the R Markdown file to HTML
output_file <- "Tellner_Thomas_Capstone_Project_Part1.html"
tryCatch({{
    render(
        input = "{rmd_file_r}",
        output_file = output_file,
        output_dir = "{work_dir_r}",
        output_format = "html_document",
        quiet = FALSE
    )
    # Print the output file path
    cat("HTML_OUTPUT:", file.path("{work_dir_r}", output_file), "\\n")
    cat("RENDER_SUCCESS\\n")
}}, error = function(e) {{
    cat("RENDER_ERROR:", conditionMessage(e), "\\n")
    stop(e)
}})
'''

# Check if R is available
if not R_PATH:
    st.error("**R is not available**")
    st.markdown("""
    This project requires R and R Markdown to render the analysis.
    
    **Note:** R is not available on Streamlit Community Cloud. This project is designed
    to run locally on a machine with R and RStudio installed.
    
    ### To run this project locally:
    
    1. **Install R**: https://cran.r-project.org/
    2. **Install RStudio**: https://www.rstudio.com/products/rstudio/download/
    3. **Install required R packages**:
       ```r
       install.packages(c("rmarkdown", "Seurat", "dplyr", "ggplot2"))
       ```
    4. **Run Streamlit locally**:
       ```bash
       streamlit run pages/bioinfprojects.py
       ```
    
    ### Alternative: View the pre-rendered HTML
    
    If the HTML file has been pre-rendered, you can view it directly.
    """)
    
    # Try to display pre-rendered HTML if it exists
    html_file = BASE_DIR / "Tellner_Thomas_Capstone_Project_Part1.html"
    if html_file.exists():
        st.info("Found pre-rendered HTML file. Displaying it below:")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=1200, scrolling=True)
    else:
        st.warning("No pre-rendered HTML file found. Please run this project locally with R installed.")
    
    st.stop()

# Write the render script to a temporary file
tmp_script_path = None
try:
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.R', delete=False, encoding='utf-8'
    ) as tmp_script:
        tmp_script.write(render_script)
        tmp_script_path = tmp_script.name

    # First check for pandoc
    check_process = subprocess.Popen(
        [R_PATH, "-e", check_pandoc_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(WORK_DIR)
    )
    check_result = check_process.communicate()
    
    # Parse check output to see if pandoc was found
    pandoc_found = False
    pandoc_path = None
    pandoc_version = None
    
    if check_result[0]:
        for line in check_result[0].split('\n'):
            if 'PANDOC_FOUND' in line:
                pandoc_found = True
            if 'PANDOC_PATH:' in line:
                pandoc_path = line.split('PANDOC_PATH:')[1].strip()
            if 'PANDOC_VERSION:' in line:
                pandoc_version = line.split('PANDOC_VERSION:')[1].strip()
            if 'PANDOC_DIR:' in line:
                pandoc_path = line.split('PANDOC_DIR:')[1].strip()
    
    if check_process.returncode != 0 or not pandoc_found:
        st.error("**Pandoc is not installed or not found**")
        
        # Show attempted paths from the output
        attempted_paths = []
        if check_result[0]:
            for line in check_result[0].split('\n'):
                if 'ATTEMPTED_PATH:' in line:
                    attempted_paths.append(line.split('ATTEMPTED_PATH:')[1].strip())
                if 'PANDOC_PATH:' in line:
                    attempted_paths.append(line.split('PANDOC_PATH:')[1].strip())
        
        if attempted_paths:
            st.info(" **Paths checked:**")
            for path in attempted_paths:
                st.write(f"  - {path}")
        
        st.markdown("""
        **Pandoc is required to render R Markdown documents.**
        
        ### If you have RStudio installed:
        
        RStudio includes pandoc, but it might not be in your system PATH.
        The code will try to find it automatically. If it still fails:
        
        1. **Make sure RStudio is installed** and up to date
        2. **Restart your Streamlit app** after installing/updating RStudio
        3. RStudio's pandoc is typically located at:
           - `C:\\Program Files\\RStudio\\resources\\app\\bin\\pandoc\\`
           - Or in your user directory
        
        ### Other Installation Options:
        
        1. **Install Pandoc directly**:
           - Download from: https://pandoc.org/installing.html
           - Windows installer: https://github.com/jgm/pandoc/releases/latest
        
        2. **Using Chocolatey** (if you have it installed):
           ```powershell
           choco install pandoc
           ```
        
        3. **Using winget** (Windows Package Manager):
           ```powershell
           winget install --id JohnMacFarlane.Pandoc
           ```
        
        After installing pandoc, **restart your Streamlit app** and try again.
        """)
        
        if check_result[0]:
            st.write("**Check Output:**")
            st.code(check_result[0])
        if check_result[1]:
            st.write("**Check Errors:**")
            st.code(check_result[1])
        
        st.stop()
    
    # Pandoc is available, proceed with rendering
    process = subprocess.Popen(
        [R_PATH, tmp_script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(WORK_DIR)
    )
    result = process.communicate()
    
    # Check for rendering errors
    if process.returncode != 0:
        st.error("R script failed to render the document.")
        
        # Check if it's a pandoc error
        error_text = result[1] + result[0]
        if "pandoc" in error_text.lower():
            st.error("**Pandoc Error Detected**")
            st.markdown("""
            It appears pandoc is still not available or there's a
            version issue.

            **Troubleshooting:**
            1. Make sure pandoc is installed and in your system PATH
            2. If you just installed pandoc, restart your Streamlit app
            3. Try running `pandoc --version` in PowerShell to verify
            4. RStudio includes pandoc - if you have RStudio installed,
               make sure it's in your PATH or restart your computer
            """)
        
        if result[1]:
            st.write("**R Rendering Errors (stderr):**")
            st.code(result[1])
        if result[0]:
            st.write("**R Rendering Output (stdout):**")
            st.code(result[0])
        st.stop()
    
    # Extract HTML output path from stdout
    html_output_path = None
    render_success = False
    for line in result[0].split('\n'):
        if 'HTML_OUTPUT:' in line:
            html_output_path = line.split('HTML_OUTPUT:')[1].strip()
        if 'RENDER_SUCCESS' in line:
            render_success = True
        if 'RENDER_ERROR:' in line:
            error_msg = line.split('RENDER_ERROR:')[1].strip()
            st.error(f"Rendering error: {error_msg}")
            st.stop()
    
    # If not found in stdout, try default location
    if not html_output_path:
        html_output_path = str(WORK_DIR / "Tellner_Thomas_Capstone_Project_Part1.html")
    
    # Display the rendered HTML
    if os.path.exists(html_output_path):
        with open(html_output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Display the HTML content
        st.components.v1.html(html_content, height=1200, scrolling=True)
    else:
        st.error(f"HTML output file not found at: {html_output_path}")
        st.write("**Debug Info:**")
        st.write(f"Working Directory: {WORK_DIR}")
        st.write(f"RMD File Exists: {RMD_FILE.exists()}")
        st.write(f"Expected HTML Path: {html_output_path}")
        st.write(f"Return Code: {process.returncode}")
        
        if result[1]:
            st.write("**Error Details:**")
            st.code(result[1])

except FileNotFoundError:
    st.error("**R executable not found**")
    st.markdown("""
    R is required to run this project but could not be found on the system.
    
    **To run this project locally:**
    1. Install R from https://cran.r-project.org/
    2. Install RStudio from https://www.rstudio.com/products/rstudio/download/
    3. Make sure R is in your system PATH
    """)
    st.stop()
except Exception as e:
    st.error(f"**Error running R script:** {str(e)}")
    st.markdown("""
    An error occurred while trying to execute the R script.
    
    **Common issues:**
    - R is not installed or not in PATH
    - Required R packages are not installed
    - Pandoc is not available
    
    **To troubleshoot:**
    1. Check that R is installed and accessible
    2. Install required packages: `install.packages(c("rmarkdown", "Seurat"))`
    3. Install pandoc if needed
    """)
    st.exception(e)
    st.stop()
finally:
    # Clean up temporary script
    if tmp_script_path and os.path.exists(tmp_script_path):
        try:
            os.remove(tmp_script_path)
        except Exception:
            pass  # Ignore cleanup errors
