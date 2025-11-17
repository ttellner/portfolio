# theme.py
import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
    /* === SIDEBAR WIDTH === */
    section[data-testid="stSidebar"] {
        width: 300px !important;
    }

    /* === PROJECT CARD STYLE === */
    .project-card {
        background-color: var(--background-color);
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }
    .project-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.15);
    }

    /* === GLOBAL BUTTON STYLE === */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0066ff, #00b4ff);
        color: white !important;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }

    /* === PAGE LINK STYLE === */
    a[data-testid="stPageLink"] {
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
    
    nav[aria-label="Secondary"] { 
        display: none; 
    }

    </style>
    """, unsafe_allow_html=True)
