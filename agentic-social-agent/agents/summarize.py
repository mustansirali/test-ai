import os
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, WriteError
from dotenv import load_dotenv
from utils.logger import with_error_handling, create_workflow_logger

load_dotenv()

# Global logger instance
logger = create_workflow_logger()

def get_mongodb_client() -> Optional[MongoClient]:
    """Get MongoDB client with error handling"""
    try:
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            logger.logger.warning("MONGODB_URI not set. Using localhost:27017")
            mongodb_uri = "mongodb://localhost:27017"
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        logger.logger.info("✅ MongoDB connection successful for summaries")
        return client
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.logger.error(f"MongoDB connection failed for summaries: {e}")
        return None
    except Exception as e:
        logger.logger.error(f"Unexpected MongoDB connection error for summaries: {e}")
        return None

@with_error_handling(logger, "summarize_articles")
def summarize_articles(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize articles using OpenAI with comprehensive error handling and logging
    """
    try:
        # Validate required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        openai = OpenAI(api_key=openai_api_key)
        
        # Validate input state
        articles = state.get("articles", [])
        if not articles:
            logger.logger.warning("No articles provided for summarization")
            return {**state, "summaries": {}, "summarization_metrics": {"articles_processed": 0}}
        
        logger.logger.info(f"📝 Processing {len(articles)} articles for summarization")
        
        # Get MongoDB client
        client = get_mongodb_client()
        if client is None:
            logger.logger.warning("MongoDB not available, summaries will not be stored")
        
        summaries = {}
        successful_summaries = 0
        failed_summaries = 0
        skipped_summaries = 0
        total_tokens = 0
        
        for article_idx, article in enumerate(articles):
            try:
                content = article.get("raw_content", "")
                if not content:
                    logger.logger.warning(f"No content for article {article_idx}: {article.get('url', 'unknown')}")
                    skipped_summaries += 1
                    continue
                
                # Create summary using OpenAI
                summary_start = time.time()
                try:
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo-16k",
                        messages=[
                            {"role": "system", "content": "Summarize the following article in plain English for a civic-minded audience."},
                            {"role": "user", "content": content}
                        ],
                        max_tokens=300,
                        temperature=0.3
                    )
                    
                    summary_duration = time.time() - summary_start
                    summary = response.choices[0].message.content.strip()
                    tokens_used = response.usage.total_tokens if response.usage else 0
                    total_tokens += tokens_used
                    
                    successful_summaries += 1
                    summaries[article["url"]] = summary
                    
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="success",
                        duration=summary_duration,
                        model="gpt-3.5-turbo-16k",
                        tokens_used=tokens_used
                    )
                    
                except Exception as e:
                    summary_duration = time.time() - summary_start
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="error",
                        duration=summary_duration,
                        error=str(e)
                    )
                    failed_summaries += 1
                    logger.logger.error(f"OpenAI summarization failed for article {article_idx}: {e}")
                    continue
                
                # Store summary in MongoDB if available
                if client:
                    try:
                        db = client['articles']
                        articles_collection = db["raw_articles"]
                        
                        articles_collection.update_one(
                            {"url": article["url"]},
                            {"$set": {
                                "summary": summary,
                                "place": state.get("place", "unknown"),
                                "title": article.get("title", ""),
                                "summarization_timestamp": time.time(),
                                "tokens_used": tokens_used
                            }},
                            upsert=True
                        )
                        
                    except WriteError as e:
                        logger.logger.error(f"Failed to store summary for article {article_idx}: {e}")
                    except Exception as e:
                        logger.logger.error(f"Unexpected error storing summary for article {article_idx}: {e}")
                
            except Exception as e:
                failed_summaries += 1
                logger.logger.error(f"Error processing article {article_idx}: {e}")
        
        # Log summarization metrics
        summarization_metrics = {
            "articles_processed": len(articles),
            "successful_summaries": successful_summaries,
            "failed_summaries": failed_summaries,
            "skipped_summaries": skipped_summaries,
            "total_tokens": total_tokens,
            "success_rate": (successful_summaries / len(articles)) * 100 if articles else 0
        }
        
        logger.log_data_metrics("summarize_articles", summarization_metrics)
        logger.logger.info(f"✅ Summarization complete: {successful_summaries}/{len(articles)} articles summarized, {total_tokens} tokens used")
        
        # Close MongoDB connection
        if client:
            client.close()
            logger.logger.debug("MongoDB connection closed for summaries")
        
        return {
            **state,
            "summaries": summaries,
            "summarization_metrics": summarization_metrics
        }
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in summarize_articles: {str(e)}")
        raise

def summarize_articles_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when summarization fails
    """
    logger.logger.warning("Using fallback for summarization - no summaries created")
    
    articles = state.get("articles", [])
    return {
        **state,
        "summaries": {},
        "summarization_status": "fallback",
        "summarization_error": "Summarization failed, using fallback",
        "summarization_metrics": {
            "articles_processed": len(articles),
            "successful_summaries": 0,
            "failed_summaries": len(articles),
            "skipped_summaries": 0,
            "total_tokens": 0,
            "success_rate": 0
        }
    }