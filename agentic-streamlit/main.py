import streamlit as st
from services.redis_service import get_redis_client
from services.openai_service import get_openai_client
from services.tavily_service import get_tavily_client
from ui.profile_setup import profile_setup
from ui.article_browser import article_browser

st.set_page_config(page_title="AI Social Agent", layout="wide")

# Instantiate services
redis_client = get_redis_client()
openai_client = get_openai_client()
tavily_client = get_tavily_client()

# UI Modules
profile_setup(redis_client)
article_browser(redis_client, openai_client, tavily_client)