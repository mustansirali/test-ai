import streamlit as st
from openai import OpenAI

@st.cache_resource
def get_openai_client():
    try:
        return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception as e:
        st.error(f"OpenAI key error: {e}")
        st.stop()