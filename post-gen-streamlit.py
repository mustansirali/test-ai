import streamlit as st
import redis
import openai
import requests
import json
from datetime import datetime
from hashlib import sha256

# Setup Redis & OpenAI
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
openai.api_key = st.secrets["OPENAI_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

# -- PROFILE SETUP -- #
st.title("🧠 AI-Powered Social Agent Setup")

with st.expander("1. 👤 Representative Profile"):
    name = st.text_input("Name or Alias")
    bio = st.text_area("Describe yourself and how the AI should represent you")
    urls = st.text_area("Enter URLs for current events (comma-separated)")
    stances = st.text_area("List your key stances (e.g., Pro education reform, Anti-censorship)")
    tone = st.selectbox("Preferred tone for posts", ["Neutral", "Witty", "Serious", "Bold", "Empathetic", "Professional"])
    post_freq = st.selectbox("How often do you want to post?", ["Daily", "Weekly", "Weekdays", "Bi-weekly"])
    avoid_topics = st.text_area("Topics you want to avoid")
    if st.button("Save Profile"):
        redis_client.hset("user:demo:profile", mapping={
            "name": name, "bio": bio, "urls": urls, "stances": stances,
            "tone": tone, "post_freq": post_freq, "avoid_topics": avoid_topics
        })
        st.success("✅ Profile saved!")

# -- TAVILY SEARCH & SUMMARY -- #
def search_articles(query, location="New York"):
    res = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
        json={"query": f"{query} news in {location}", "include_answers": False}
    )
    return res.json().get("results", [])

def extract_and_summarize(url):
    res = requests.post(
        "https://api.tavily.com/extract",
        headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
        json={"url": url}
    )
    text = res.json().get("content", "")
    summary = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize the article briefly."},
            {"role": "user", "content": text}
        ]
    )["choices"][0]["message"]["content"]
    return summary

def embed_and_store(text, user_id):
    vector = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )["data"][0]["embedding"]
    key = f"user:{user_id}:post:{sha256(text.encode()).hexdigest()}"
    redis_client.hset(key, mapping={"summary": text, "embedding": json.dumps(vector), "timestamp": datetime.now().isoformat()})
    return key

with st.expander("2. 🚀 Run News Agent Now"):
    if st.button("Run Agent Now"):
        articles = search_articles("politics")
        for article in articles[:3]:
            summary = extract_and_summarize(article["url"])
            key = embed_and_store(summary, user_id="demo")
            st.write(f"✅ Stored: {key}")

# -- POST GENERATION & FEEDBACK -- #
st.header("📝 Review & Edit Draft Posts")
keys = redis_client.keys("user:demo:post:*")
draft_options = [redis_client.hget(k, "summary")[:100] + "..." for k in keys]

if draft_options:
    selected_index = st.selectbox("Select a summary", range(len(draft_options)), format_func=lambda i: draft_options[i])
    selected_key = keys[selected_index]
    summary = redis_client.hget(selected_key, "summary")

    st.subheader("📄 AI Drafted Post")
    profile = redis_client.hgetall("user:demo:profile")
    personality = profile.get("bio", "a social media personality")
    tone = profile.get("tone", "Bold")

    prompt = f"Write a social media post in a {tone} tone from the perspective of {personality} based on this summary:\n\n{summary}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    draft = response["choices"][0]["message"]["content"]
    st.text_area("Generated Post", draft, height=200)

    feedback = st.text_area("✏️ Feedback or edits")
    if st.button("Submit Feedback"):
        redis_client.hset(selected_key, "feedback", feedback)
        st.success("✅ Feedback saved!")
else:
    st.info("No posts available yet.")
