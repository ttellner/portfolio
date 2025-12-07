import streamlit as st
from nbconvert import HTMLExporter
import nbformat

st.set_page_config(layout="wide")

with open("D:\\Repos\\portfolio\\pages\\gamedatascience\\Chapter_3\\Chapter3_Lab1.ipynb", "r", encoding="utf-8") as f:
    notebook = nbformat.read(f, as_version=4)

html_exporter = HTMLExporter()
(body, _) = html_exporter.from_notebook_node(notebook)

st.components.v1.html(body, height=800, scrolling=True)
