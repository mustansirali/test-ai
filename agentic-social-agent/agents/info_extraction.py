import os
from openai import OpenAI

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_info(article_content: str):
    prompt = f"Extract the 5W1H (Who, What, When, Where, Why, How) from the following article:\n\n{article_content}"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()