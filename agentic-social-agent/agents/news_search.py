import os
import time
from typing import Dict, Any, List
from tavily import TavilyClient
from tavily.errors import BadRequestError, ForbiddenError, InvalidAPIKeyError, MissingAPIKeyError, TimeoutError, UsageLimitExceededError
from utils.logger import with_error_handling, create_workflow_logger

# Global logger instance
logger = create_workflow_logger()

@with_error_handling(logger, "search_articles")
def search_articles(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for news articles using Tavily API with comprehensive error handling
    """
    try:
        # Validate required environment variables
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")
        
        # Validate input state
        place = state.get("place")
        if not place:
            raise ValueError("'place' is required in state but not provided")
        
        domains = state.get("domains", [])
        if not domains:
            logger.logger.warning("No domains specified, will search across all domains")
        
        # Initialize Tavily client
        tavily = TavilyClient(api_key=tavily_api_key)
        
        # Construct search query
        query = f"{place} latest news"
        logger.logger.info(f"🔍 Searching for: {query}")
        logger.logger.info(f"📰 Domains: {domains}")
        
        # Perform search with timing
        search_start = time.time()
        try:
            results = tavily.search(
                query=query,
                topic="news",
                include_domains=domains,
                max_results=50,
                search_depth="advanced"
            )
            search_duration = time.time() - search_start
            
            # Log API call success
            logger.log_api_call(
                service="Tavily",
                endpoint="search",
                status="success",
                duration=search_duration,
                query=query,
                results_count=len(results.get("results", []))
            )
            
        except (BadRequestError, ForbiddenError, InvalidAPIKeyError, MissingAPIKeyError, TimeoutError, UsageLimitExceededError) as e:
            search_duration = time.time() - search_start
            logger.log_api_call(
                service="Tavily",
                endpoint="search",
                status="error",
                duration=search_duration,
                error=str(e)
            )
            raise
        
        # Extract and validate results
        articles = results.get("results", [])
        
        # Log data metrics
        logger.log_data_metrics("search_articles", {
            "articles_found": len(articles),
            "query": query,
            "domains_count": len(domains),
            "search_duration": search_duration
        })
        
        # Validate article structure
        valid_articles = []
        for i, article in enumerate(articles):
            if not isinstance(article, dict):
                logger.logger.warning(f"Invalid article format at index {i}: {type(article)}")
                continue
                
            if not article.get("url"):
                logger.logger.warning(f"Article at index {i} missing URL")
                continue
                
            valid_articles.append(article)
        
        logger.logger.info(f"✅ Found {len(valid_articles)} valid articles out of {len(articles)} total")
        
        return {
            **state,
            "articles": valid_articles,
            "search_metrics": {
                "total_results": len(articles),
                "valid_results": len(valid_articles),
                "search_duration": search_duration,
                "query": query
            }
        }
        
    except Exception as e:
        # This will be caught by the decorator, but we can add additional logging here
        logger.logger.error(f"Unexpected error in search_articles: {str(e)}")
        raise

def search_articles_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when news search fails
    """
    logger.logger.warning("Using fallback for news search - returning empty results")
    
    return {
        **state,
        "articles": [],
        "search_status": "fallback",
        "search_error": "News search failed, using fallback"
    }