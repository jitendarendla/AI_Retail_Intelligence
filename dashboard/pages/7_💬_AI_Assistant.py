import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.rag_assistant import get_rag_assistant

st.set_page_config(page_title="AI Assistant | AI Retail Platform", layout="wide")
st.title("💬 RAG Business AI Assistant")

assistant = get_rag_assistant()

user_q = st.text_input("Ask a business question:")
if st.button("Ask Assistant") and user_q:
    with st.spinner("Analyzing knowledge base..."):
        ans = assistant.query(user_q)
    st.markdown(ans)
