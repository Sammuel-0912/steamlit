import streamlit as st
import pyodbc

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + st.secrets["34.110.188.240"]
        + ";DATABASE="
        + st.secrets["SMES_Production"]
        + ";UID="
        + st.secrets["smesuser"]
        + ";PWD="
        + st.secrets["smesP@ssw0rd"]
    )

conn = init_connection()

