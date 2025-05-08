import streamlit as st
from tavily import TavilyClient

@st.cache_resource
def get_tavily_client():
    try:
        return TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
    except Exception as e:
        st.error(f"Tavily key error: {e}")
        st.stop()