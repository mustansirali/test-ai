import streamlit as st
import json
from hashlib import sha256
from datetime import datetime
from utils.summarizer import extract_and_summarize

def article_browser(redis_client, openai_client, tavily_client):
    st.header("🗞️ Browse Articles & Generate Posts")

    def search_articles(query, location="Austin, Texas"):
        try:
            profile = redis_client.hgetall("user:demo:profile")
            include_domains = [u.strip() for u in profile.get("urls", "").split(",") if u.strip()]
            print(include_domains)
            result = tavily_client.search(query=f"{query} {location}", include_domains=include_domains)
        except Exception as e:
            st.error(f"Tavily search error: {e}")

    if st.button("🔍 Run News Search"):
        redis_client.delete("user:demo:search_results")
        search_articles("Top News concerning")

    for idx, entry in enumerate(articles):
        article = json.loads(entry)
        st.markdown("---")
        st.write(f"**{article['title']}**")
        st.write(f"🔗 [Read Article]({article['url']})")
        custom_perspective = st.text_area("Add perspective", key=f"perspective_{idx}")

        if st.button("Generate Draft Post", key=f"generate_{idx}"):
            summary = extract_and_summarize(article["url"], tavily_client, openai_client)
            if summary:
                key = store_embedding(redis_client, openai_client, summary, "demo")
                if key:
                    profile = redis_client.hgetall("user:demo:profile")
                    personality = profile.get("bio", "a social media personality")
                    tone = profile.get("tone", "Bold")
                    prompts = {
                        "short_post_50": f"Write a {tone} post under 50 characters",
                        "short_post_100": f"Write a {tone} post under 100 characters",
                        "short_post_500": f"Write a {tone} post under 500 characters"
                    }

                    for label, prompt in prompts.items():
                        prompt_text = f"{prompt} from {personality}:\n\n{summary}\n\nPerspective: {custom_perspective}"
                        response = openai_client.chat.completions.create(
                            model="gpt-4", messages=[{"role": "system", "content": prompt_text}]
                        )
                        redis_client.hset(key, label, response.choices[0].message.content.strip())
                    st.success("✅ Drafts saved!")

def store_embedding(redis_client, openai_client, text, user_id):
    try:
        response = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
        vector = response.data[0].embedding
        key = f"user:{user_id}:post:{sha256(text.encode()).hexdigest()}"
        redis_client.hset(key, mapping={
            "summary": text,
            "embedding": json.dumps(vector),
            "timestamp": datetime.now().isoformat()
        })
        return key
    except Exception as e:
        st.error(f"Embedding error: {e}")
        return None