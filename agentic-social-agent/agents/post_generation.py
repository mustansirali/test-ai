import os
from openai import OpenAI

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_posts(summary: str, persona: str, tone: str, user_perspective: str = ""):
    posts = {}
    for cap in [50, 100, 500]:
        prompt = (
            f"Write a {tone} social media post in under {cap} characters from the perspective of "
            f"{persona}.\n\nSummary: {summary}\n\nAdditional thoughts: {user_perspective}"
        )
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        posts[f"post_{cap}"] = response.choices[0].message.content.strip()
    return posts