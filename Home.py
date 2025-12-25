import os
import streamlit as st
import re
from theme import apply_theme

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Thomas Tellner | Data Science Portfolio",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Hide Streamlit Pages navigation in sidebar */
    nav[aria-label="Secondary"] { 
        display: none; 
    }
    
    /* Force white background for main content area - prevents dark mode issues */
    .main .block-container {
        background-color: #ffffff !important;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Ensure main page background is white */
    .stApp {
        background-color: #f0f2f6 !important;  /* Light gray background */
    }
    
    /* Force text colors in main content */
    .main h1, .main h2, .main h3 {
        color: #262730 !important;
    }
    
    .main p, .main div {
        color: #262730 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- CUSTOM CARD STYLES ----
st.markdown("""
<style>
/* 🎨 Card container */
.card {
    border: 1px solid #e0e0e0 !important;             /* Light border */
    border-radius: 15px;
    background-color: #ffffff !important;  /* Force white background - always visible */
    padding: 1rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08); /* Soft shadow */
    transition: all 0.3s ease-in-out;
    text-align: center;                    /* Center image & text */
    margin-bottom: 1rem;
    color: #262730 !important;  /* Default text color for card */
}

/* ✨ Hover effect */
.card:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    transform: translateY(-4px);
}

/* 🖼️ Image styling inside cards */
.card img {
    border-radius: 10px;
    margin-bottom: 0.75rem;
    width: 100%;
    height: auto;
}

/* 🏷️ Title & description tweaks */
.card h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    color: #262730 !important;  /* Dark text - always visible on white background */
}

/* 🔘 Button inside card */
.card button {
    background-color: #1f77b4;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s ease-in-out;
}

.card p {
    font-size: 0.9rem;
    color: #555 !important;  /* Dark gray text - always visible on white background */
    margin-bottom: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* --- Stylish Page Link Button --- */
.stPageLink {
    display: inline-block;
    background: linear-gradient(135deg, #0072ff, #00c6ff);
    color: white !important;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    text-decoration: none !important;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    margin-top: 0.5rem;
}

a[data-testid="stPageLink"]:hover {
    background: linear-gradient(135deg, #005fcc, #00a2cc);
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

# Hide Streamlit's built-in navigation
st.markdown("""
<style>
section[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---- SIDEBAR PROFILE ----
with st.sidebar:
    #st.image("https://via.placeholder.com/150", width=200) 
    st.title("Thomas Tellner")
    st.markdown("Data Science | ML & AI | GenAI")
    st.markdown("---")
    st.markdown("**Contact:**")
    st.markdown("[🌐 LinkedIn](https://linkedin.com/in/thomastellner)")
    st.markdown("[💻 GitHub](https://github.com/ttellner)")
    st.markdown("[✉️ Email](mailto:ttellner@gmail.com)")
    st.markdown("---")
    st.caption("Made using Streamlit")

# ---- MAIN PAGE ----
st.title("Welcome to My Data Science Portfolio")
st.write("""
Hello! I'm **Thomas Tellner**, and this is my interactive - and still under construction - portfolio of data science projects.  
Each page demonstrates models used in a specific use case — from Banking/Lending to Finance/Investments to Bioinformatics. I've also included some newer types of models of interest to me.
""")

st.markdown("""
Use the sidebar to navigate through the different projects, or explore highlights below 👇
""")

# ---- SCAN PROJECT PAGES ----
project_dir = "pages"

# ---- SCAN PROJECT PAGES ----
project_dir = "pages"

# Define custom order manually (list exact filenames)
custom_order = [
    "bioinfprojects.py",
    "bankingprojects.py",
    "financeprojects.py",
    "gnnprojects.py",
    "gamedatascience.py",
]

# Keep only existing files that match your preferred order
project_files = [f for f in custom_order if os.path.exists(os.path.join(project_dir, f))]

# Optional fallback if no matches (so app doesn’t break)
if not project_files:
    project_files = sorted([f for f in os.listdir(project_dir) if f.endswith(".py")])

#The following line was replaced!!
#project_files = sorted([f for f in os.listdir(project_dir) if f.endswith(".py")])
#st.write("DEBUG:", project_files)
projects = []
for f in project_files:
    file_path = os.path.join(project_dir, f)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                lines = [line.strip() for line in docstring_match.group(1).split("\n") if line.strip()]
                title = lines[0] if len(lines) > 0 else f.replace(".py", "").replace("_", " ").title()
                desc = lines[1] if len(lines) > 1 else "No description provided."
                img = lines[2] if len(lines) > 2 else "https://via.placeholder.com/400x200?text=Data+Science+App"
            else:
                # Fallback if no docstring found
                title = f.replace(".py", "").replace("_", " ").title()
                desc = "No description provided."
                img = "https://via.placeholder.com/400x200?text=Data+Science+App"
            projects.append({"file": f, "title": title, "description": desc, "image": img})
    except Exception:
        # If file can't be read, still add it with default values
        title = f.replace(".py", "").replace("_", " ").title()
        projects.append({"file": f, "title": title, "description": "No description available.", "image": "https://via.placeholder.com/400x200?text=Data+Science+App"})
#st.write("DEBUG:", projects)

# ---- DISPLAY PROJECT CARDS DYNAMICALLY ----
num_cols = 3

if projects:
    for i in range(0, len(projects), num_cols):
        cols = st.columns(num_cols)
        for j, p in enumerate(projects[i:i+num_cols]):
            with cols[j]:
                #st.image(p["image"], use_container_width=True)
                page_file = p["file"]  # Keep the original file name with .py
                page_path = f"pages/{page_file}"  # Full path required by Streamlit
                page_title = page_file.replace(".py", "").replace("_", " ")  # Display label only
                
                # Wrap each project in a custom HTML "card" container
                st.markdown(f"""
                <div class="card">
                    <h3>{p['title']}</h3>
                    <p>{p['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.page_link(page_path, label="▶ Open Project")
                st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("⚠️ No projects found in the /pages directory.")

# ---- ABOUT SECTION ----

# ---- FOOTER ----
st.markdown(
    """
    <div style='text-align: center; padding-top: 1rem; font-size: 0.9rem; color: #777;'>
        © 2025 Thomas Tellner | Built with <a href="https://streamlit.io">Streamlit</a>
    </div>
    """,
    unsafe_allow_html=True
)
