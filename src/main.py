import streamlit as st
import sys
import os

st.title("🕵️‍♂️ Focus Ring 품질 분석 에이전트")
st.write(f"Python Version: {sys.version}")

if os.getenv("OPENAI_API_KEY"):
    st.success("개발 환경 세팅 완료")
else:
    st.error("개발 환경 세팅 실패")