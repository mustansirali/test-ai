import streamlit as st
from models.profile import UserProfile

def profile_setup(redis_client):
    st.title("🧠 AI-Powered Social Agent Setup")

    with st.expander("1. 👤 Representative Profile"):
        name = st.text_input("Name or Alias")
        bio = st.text_area("Describe yourself and how the AI should represent you")
        urls = st.text_area("Enter URLs for current events (comma-separated)")
        stances = st.text_area("Key stances")
        tone = st.selectbox("Preferred tone", ["Neutral", "Witty", "Serious", "Bold", "Empathetic", "Professional"])
        post_freq = st.selectbox("Post frequency", ["Daily", "Weekly", "Weekdays", "Bi-weekly"])
        avoid_topics = st.text_area("Topics to avoid")

        if st.button("Save Profile"):
            try:
                profile = UserProfile(
                    name=name, bio=bio, urls=urls, stances=stances,
                    tone=tone, post_freq=post_freq, avoid_topics=avoid_topics
                )
                redis_client.hset("user:demo:profile", mapping=profile.dict())
                st.success("✅ Profile saved!")
            except Exception as e:
                st.error(f"Error saving profile: {e}")