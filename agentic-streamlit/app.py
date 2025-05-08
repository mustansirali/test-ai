import streamlit as st
import redis, json
from openai import OpenAI
from tavily import TavilyClient
from hashlib import sha256
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="AI Social Agent", page_icon="🧠")
st.title("🧠 AI Social Agent")

# --- Initialize Services ---
try:
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    redis_client.ping()
except Exception as e:
    st.error(f"❌ Redis error: {e}")
    st.stop()

try:
    openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    st.error(f"❌ API key setup error: {e}")
    st.stop()

# --- Profile Section ---
with st.expander("1. 👤 Setup Profile"):
    profile = {
        "name": st.text_input("Name or Alias"),
        "bio": st.text_area("Bio / Perspective"),
        "stances": st.text_area("Stances (comma-separated)"),
        "tone": st.selectbox("Tone", ["Neutral", "Witty", "Serious", "Bold", "Empathetic", "Professional"]),
        "post_freq": st.selectbox("Post Frequency", ["Daily", "Weekly", "Bi-weekly"]),
        "avoid_topics": st.text_area("Topics to Avoid")
    }
    if st.button("💾 Save Profile"):
        redis_client.hset("user:demo:profile", mapping=profile)
        st.success("✅ Profile saved.")

# --- News Search ---
st.header("2. 🗞️ Search & Summarize News")
if st.button("🔍 Search Austin News"):
    try:
        domains = [
            "fox7austin.com", "texastribune.org", "austintexas.gov", 
            "kxan.com", "ksat.com", "cbsaustin.com"
        ]
        results = tavily.search(
            query="Austin Texas latest news", 
            topic="news",
            include_domains=domains, 
            max_results=8, 
            search_depth="advanced"
        )
        redis_client.delete("user:demo:search_results")
        for r in results.get("results", []):
            redis_client.rpush("user:demo:search_results", json.dumps(r))
        st.success(f"🔎 Found {len(results.get('results', []))} articles.")
    except Exception as e:
        st.error(f"❌ Tavily search error: {e}")

# --- List Articles ---
articles = [json.loads(a) for a in redis_client.lrange("user:demo:search_results", 0, -1)]
for idx, article in enumerate(articles):
    st.markdown("---")
    st.subheader(article.get("title", "No Title"))
    st.write(f"[Read Full Article]({article.get('url', '')})")

    user_perspective = st.text_area("Your perspective (optional)", key=f"persp_{idx}")
    if st.button("📝 Generate Post", key=f"genpost_{idx}"):
        try:
            # Summarize article
            extract = tavily.extract(urls=[article["url"]])
            raw_text = extract.get("results", [{}])[0].get("raw_content", "").strip()
            if not raw_text:
                st.warning("⚠️ No content found.")
                continue

            summary_resp = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Summarize the following article in plain English."},
                    {"role": "user", "content": raw_text}
                ]
            )
            summary = summary_resp.choices[0].message.content.strip()

            # Store embedding
            emb_resp = openai.embeddings.create(
                input=summary, model="text-embedding-3-small"
            )
            embedding = emb_resp.data[0].embedding
            key = f"user:demo:post:{sha256(summary.encode()).hexdigest()}"
            redis_client.hset(key, mapping={
                "summary": summary,
                "embedding": json.dumps(embedding),
                "timestamp": datetime.now().isoformat()
            })

            # Generate posts
            profile_data = redis_client.hgetall("user:demo:profile")
            persona = profile_data.get("bio", "a concerned citizen")
            tone = profile_data.get("tone", "Neutral")

            for cap in [50, 100, 500]:
                prompt = (
                    f"Write a {tone} social media post in under {cap} characters from the perspective of "
                    f"{persona}.\n\nSummary: {summary}\n\nAdditional thoughts: {user_perspective}"
                )
                result = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": prompt}]
                )
                redis_client.hset(key, f"short_post_{cap}", result.choices[0].message.content.strip())

            st.success("✅ Posts generated and saved.")

        except Exception as e:
            st.error(f"❌ Generation error: {e}")

# --- Review Drafts ---
st.header("3. 📝 Review Posts")
for key in redis_client.keys("user:demo:post:*"):
    data = redis_client.hgetall(key)
    st.markdown("---")
    st.text_area("📰 Summary", data.get("summary", ""), height=100)
    for cap in [50, 100, 500]:
        draft = data.get(f"short_post_{cap}")
        if draft:
            st.text_area(f"{cap}-char Post", draft, height=80, key=f"{key}_post_{cap}")
    feedback = st.text_area("✏️ Feedback", key=f"{key}_feedback")
    if st.button("Submit Feedback", key=f"{key}_submit"):
        redis_client.hset(key, "feedback", feedback)
        st.success("✅ Feedback saved.")