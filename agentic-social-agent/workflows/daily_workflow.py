from langgraph.graph import StateGraph, START
from agents import news_search, article_storage, info_extraction, post_generation, poll_creation

def build_workflow():
    builder = StateGraph(dict)

    # Define nodes
    builder.add_node("search_news", news_search.search_news)
    builder.add_node("store_articles", article_storage.store_articles)
    builder.add_node("extract_info", info_extraction.extract_info)
    builder.add_node("generate_posts", post_generation.generate_posts)
    builder.add_node("create_poll", poll_creation.create_daily_poll)

    # Define edges
    builder.add_edge(START, "search_news")
    builder.add_edge("search_news", "store_articles")
    builder.add_edge("store_articles", "extract_info")
    builder.add_edge("extract_info", "generate_posts")
    builder.add_edge("generate_posts", "create_poll")

    return builder.compile()