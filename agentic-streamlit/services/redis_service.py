import redis
import streamlit as st

@st.cache_resource
def get_redis_client():
    try:
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        st.error(f"Redis error: {e}")
        st.stop()