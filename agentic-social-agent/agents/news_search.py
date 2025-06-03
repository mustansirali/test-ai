import os
from tavily import TavilyClient

def search_news(query: str, domains: list, max_results: int = 8):
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = tavily.search(
        query=query,
        topic="news",
        include_domains=domains,
        max_results=max_results,
        search_depth="advanced"
    )
    return results.get("results", [])