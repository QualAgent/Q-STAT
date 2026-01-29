import streamlit as st
import pandas as pd
import os
import psycopg2
import importlib.metadata

st.set_page_config(page_title="Dev Environment Check", page_icon="🕵️‍♂️")

st.title("개발 환경 점검")
st.divider()

st.subheader("1. System Info")
try:
    lg_version = importlib.metadata.version("langgraph")
    st.success(f"LangGraph Installed! (v{lg_version})")
except Exception as e:
    st.warning(f"⚠️ LangGraph is installed, but version check failed: {e}")
st.subheader("2. Security (.env)")
if os.getenv("OPENAI_API_KEY"):
    st.success("OpenAI API Key Loaded")
else:
    st.error("API Key Missing")

st.subheader("3. Database Connection")
db_host = os.getenv("POSTGRES_HOST")
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
try:
    conn = psycopg2.connect(
        host= db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    st.success("PostgreSQL Connected.")
    
    df = pd.read_sql("SELECT version();", conn)
    st.code(df.iloc[0,0], language="sql")
    
except Exception as e:
    st.error(f"DB Connection Failed: {e}")