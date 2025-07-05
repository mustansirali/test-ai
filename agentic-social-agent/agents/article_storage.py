import os
import time
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, DuplicateKeyError, WriteError
from utils.logger import with_error_handling, create_workflow_logger

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
        logger.logger.info("✅ MongoDB connection successful")
        return client
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.logger.error(f"MongoDB connection failed: {e}")
        logger.logger.info("Continuing without MongoDB storage...")
        return None
    except Exception as e:
        logger.logger.error(f"Unexpected MongoDB connection error: {e}")
        return None

@with_error_handling(logger, "store_articles")
def store_articles(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store articles in MongoDB with comprehensive error handling and logging
    """
    try:
        # Validate input state
        articles = state.get("articles", [])
        if not articles:
            logger.logger.warning("No articles provided for storage")
            return {**state, "storage_metrics": {"articles_processed": 0, "articles_stored": 0}}
        
        logger.logger.info(f"💾 Storing {len(articles)} articles in MongoDB")
        
        # Get MongoDB client
        client = get_mongodb_client()
        if client is None:
            logger.logger.warning("MongoDB not available, skipping storage")
            return {
                **state,
                "storage_status": "skipped",
                "storage_error": "MongoDB connection failed",
                "storage_metrics": {"articles_processed": len(articles), "articles_stored": 0}
            }
        
        try:
            db = client['articles']
            articles_collection = db["raw_articles"]
            
            # Create indexes for better performance
            try:
                articles_collection.create_index("url", unique=True)
                logger.logger.info("✅ Created unique index on 'url' field")
            except Exception as e:
                logger.logger.warning(f"Index creation failed (may already exist): {e}")
            
            stored_count = 0
            duplicate_count = 0
            error_count = 0
            
            for i, article in enumerate(articles):
                try:
                    # Validate article structure
                    if not isinstance(article, dict):
                        logger.logger.warning(f"Invalid article format at index {i}: {type(article)}")
                        error_count += 1
                        continue
                    
                    if not article.get("url"):
                        logger.logger.warning(f"Article at index {i} missing URL")
                        error_count += 1
                        continue
                    
                    # Use upsert to avoid duplicates
                    try:
                        result = articles_collection.update_one(
                            {"url": article["url"]},
                            {"$setOnInsert": article},
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            stored_count += 1
                            logger.logger.debug(f"✅ Stored new article: {article['url']}")
                        else:
                            duplicate_count += 1
                            logger.logger.debug(f"⏭️ Skipped duplicate article: {article['url']}")
                            
                    except DuplicateKeyError:
                        duplicate_count += 1
                        logger.logger.debug(f"⏭️ Duplicate key error for: {article['url']}")
                    except WriteError as e:
                        error_count += 1
                        logger.logger.error(f"Write error for article {i}: {e}")
                    except Exception as e:
                        error_count += 1
                        logger.logger.error(f"Unexpected error storing article {i}: {e}")
                
                except Exception as e:
                    error_count += 1
                    logger.logger.error(f"Error processing article {i}: {e}")
            
            # Log storage metrics
            storage_metrics = {
                "articles_processed": len(articles),
                "articles_stored": stored_count,
                "duplicates_skipped": duplicate_count,
                "errors": error_count,
                "success_rate": (stored_count / len(articles)) * 100 if articles else 0
            }
            
            logger.log_data_metrics("store_articles", storage_metrics)
            logger.logger.info(f"✅ Storage complete: {stored_count} stored, {duplicate_count} duplicates, {error_count} errors")
            
            return {
                **state,
                "storage_status": "success",
                "storage_metrics": storage_metrics
            }
            
        except Exception as e:
            logger.logger.error(f"Database operation error: {e}")
            raise
            
        finally:
            if client:
                client.close()
                logger.logger.debug("MongoDB connection closed")
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in store_articles: {str(e)}")
        raise

def store_articles_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when article storage fails
    """
    logger.logger.warning("Using fallback for article storage - articles not persisted")
    
    articles = state.get("articles", [])
    return {
        **state,
        "storage_status": "fallback",
        "storage_error": "Article storage failed, using fallback",
        "storage_metrics": {
            "articles_processed": len(articles),
            "articles_stored": 0,
            "duplicates_skipped": 0,
            "errors": len(articles),
            "success_rate": 0
        }
    }