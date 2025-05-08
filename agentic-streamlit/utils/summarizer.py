import streamlit as st

def extract_and_summarize(url, tavily_client, openai_client):
    try:
        result = tavily_client.extract(urls=[url])
        raw = result["results"][0].get("raw_content", "")
        if not raw.strip():
            st.warning("No content to summarize.")
            return ""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize this article in plain English."},
                {"role": "user", "content": raw}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Summarization error: {e}")
        return ""