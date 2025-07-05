import os
import time
from typing import Dict, Any, List
from openai import OpenAI
from tavily import TavilyClient
from tavily.errors import BadRequestError, ForbiddenError, InvalidAPIKeyError, MissingAPIKeyError, TimeoutError, UsageLimitExceededError
from dotenv import load_dotenv
from utils.logger import with_error_handling, create_workflow_logger

load_dotenv()

# Global logger instance
logger = create_workflow_logger()

@with_error_handling(logger, "extract_info")
def extract_info(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract information from articles using Tavily and OpenAI with comprehensive error handling
    """
    try:
        # Validate required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set")
        
        # Initialize clients
        openai = OpenAI(api_key=openai_api_key)
        tavily = TavilyClient(api_key=tavily_api_key)
        
        # Validate input state
        articles = state.get("articles", [])
        if not articles:
            logger.logger.warning("No articles provided for extraction")
            return {**state, "articles": [], "extraction_metrics": {"articles_processed": 0}}
        
        logger.logger.info(f"📄 Processing {len(articles)} articles for information extraction")
        
        # Extract URLs for Tavily extraction
        urls = [article.get("url") for article in articles if article.get("url")]
        if not urls:
            logger.logger.warning("No valid URLs found in articles")
            return {**state, "articles": articles, "extraction_metrics": {"articles_processed": 0}}
        
        # Extract raw content using Tavily
        extraction_start = time.time()
        try:
            results = tavily.extract(urls=urls)
            extraction_duration = time.time() - extraction_start
            
            logger.log_api_call(
                service="Tavily",
                endpoint="extract",
                status="success",
                duration=extraction_duration,
                urls_count=len(urls)
            )
            
        except (BadRequestError, ForbiddenError, InvalidAPIKeyError, MissingAPIKeyError, TimeoutError, UsageLimitExceededError) as e:
            extraction_duration = time.time() - extraction_start
            logger.log_api_call(
                service="Tavily",
                endpoint="extract",
                status="error",
                duration=extraction_duration,
                error=str(e)
            )
            raise
        
        # Process extracted content
        extracted_results = results.get("results", [])
        processed_articles = []
        successful_extractions = 0
        successful_ai_processing = 0
        
        for i, article in enumerate(articles):
            try:
                # Get raw content from Tavily results
                if i < len(extracted_results):
                    raw_content = extracted_results[i].get("raw_content", "")
                    article["raw_content"] = raw_content
                    article["extracted"] = True
                    successful_extractions += 1
                else:
                    article["raw_content"] = ""
                    article["extracted"] = False
                    logger.logger.warning(f"No extraction result for article {i}: {article.get('url', 'unknown')}")
                
                # Skip AI processing if no content
                if not article.get("raw_content"):
                    logger.logger.warning(f"Skipping AI processing for article {i} - no content")
                    processed_articles.append(article)
                    continue
                
                # Extract 5W1H using OpenAI
                ai_start = time.time()
                try:
                    prompt = f"Extract the 5W1H (Who, What, When, Where, Why, How) from this:\n\n{article['raw_content']}"
                    
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo-16k",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.1
                    )
                    
                    ai_duration = time.time() - ai_start
                    crucial_content = response.choices[0].message.content.strip()
                    article["crucial_content"] = crucial_content
                    successful_ai_processing += 1
                    
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="success",
                        duration=ai_duration,
                        model="gpt-3.5-turbo-16k",
                        tokens_used=response.usage.total_tokens if response.usage else 0
                    )
                    
                except Exception as e:
                    ai_duration = time.time() - ai_start
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="error",
                        duration=ai_duration,
                        error=str(e)
                    )
                    article["crucial_content"] = "AI processing failed"
                    logger.logger.error(f"OpenAI processing failed for article {i}: {e}")
                
                processed_articles.append(article)
                
            except Exception as e:
                logger.logger.error(f"Error processing article {i}: {e}")
                # Keep the article but mark it as failed
                article["extraction_error"] = str(e)
                processed_articles.append(article)
        
        # Log extraction metrics
        extraction_metrics = {
            "articles_processed": len(articles),
            "successful_extractions": successful_extractions,
            "successful_ai_processing": successful_ai_processing,
            "extraction_duration": extraction_duration,
            "urls_processed": len(urls)
        }
        
        logger.log_data_metrics("extract_info", extraction_metrics)
        logger.logger.info(f"✅ Extraction complete: {successful_extractions}/{len(articles)} articles extracted, {successful_ai_processing}/{len(articles)} AI processed")
        
        return {
            **state,
            "articles": processed_articles,
            "extraction_metrics": extraction_metrics
        }
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in extract_info: {str(e)}")
        raise

def extract_info_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when info extraction fails
    """
    logger.logger.warning("Using fallback for info extraction - returning original articles")
    
    articles = state.get("articles", [])
    for article in articles:
        article["extraction_status"] = "fallback"
        article["raw_content"] = ""
        article["crucial_content"] = ""
    
    return {
        **state,
        "articles": articles,
        "extraction_status": "fallback",
        "extraction_error": "Info extraction failed, using fallback"
    }