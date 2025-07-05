import os
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure, WriteError
from dotenv import load_dotenv
import tiktoken
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
        logger.logger.info("✅ MongoDB connection successful for embeddings")
        return client
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        logger.logger.error(f"MongoDB connection failed for embeddings: {e}")
        return None
    except Exception as e:
        logger.logger.error(f"Unexpected MongoDB connection error for embeddings: {e}")
        return None

def chunk_text(text: str, max_tokens: int = 800, model: str = "text-embedding-3-small") -> List[str]:
    """
    Chunk text based on token limits with error handling
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        chunks = [tokens[i:i+max_tokens] for i in range(0, len(tokens), max_tokens)]
        return [encoding.decode(chunk) for chunk in chunks]
    except Exception as e:
        logger.logger.error(f"Error chunking text: {e}")
        # Fallback: simple character-based chunking
        chunk_size = max_tokens * 4  # Rough estimate
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@with_error_handling(logger, "embed_articles")
def embed_articles(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Embed articles using OpenAI with comprehensive error handling and logging
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
            logger.logger.warning("No articles provided for embedding")
            return {**state, "embedding_metrics": {"articles_processed": 0, "chunks_embedded": 0}}
        
        logger.logger.info(f"🔤 Processing {len(articles)} articles for embedding")
        
        # Get MongoDB client
        client = get_mongodb_client()
        if client is None:
            logger.logger.warning("MongoDB not available, skipping embedding storage")
            return {
                **state,
                "embedding_status": "skipped",
                "embedding_error": "MongoDB connection failed",
                "embedding_metrics": {"articles_processed": len(articles), "chunks_embedded": 0}
            }
        
        try:
            db = client['articles']
            chunks_collection = db["article_chunks"]
            
            # Create indexes for better performance
            try:
                chunks_collection.create_index([("url", 1), ("chunk_index", 1)], unique=True)
                logger.logger.info("✅ Created unique index on 'url' and 'chunk_index' fields")
            except Exception as e:
                logger.logger.warning(f"Index creation failed (may already exist): {e}")
            
            total_chunks = 0
            successful_embeddings = 0
            failed_embeddings = 0
            total_tokens = 0
            
            for article_idx, article in enumerate(articles):
                try:
                    content = article.get("raw_content", "")
                    if not content:
                        logger.logger.warning(f"No content for article {article_idx}: {article.get('url', 'unknown')}")
                        continue
                    
                    # Chunk the content
                    chunks = chunk_text(content)
                    total_chunks += len(chunks)
                    
                    logger.logger.debug(f"📄 Article {article_idx}: {len(chunks)} chunks created")
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        try:
                            # Create embedding
                            embedding_start = time.time()
                            try:
                                response = openai.embeddings.create(
                                    input=chunk,
                                    model="text-embedding-3-small"
                                )
                                embedding_duration = time.time() - embedding_start
                                
                                embedding = response.data[0].embedding
                                tokens_used = response.usage.total_tokens if response.usage else 0
                                total_tokens += tokens_used
                                
                                successful_embeddings += 1
                                
                                logger.log_api_call(
                                    service="OpenAI",
                                    endpoint="embeddings",
                                    status="success",
                                    duration=embedding_duration,
                                    model="text-embedding-3-small",
                                    tokens_used=tokens_used
                                )
                                
                            except Exception as e:
                                embedding_duration = time.time() - embedding_start
                                logger.log_api_call(
                                    service="OpenAI",
                                    endpoint="embeddings",
                                    status="error",
                                    duration=embedding_duration,
                                    error=str(e)
                                )
                                failed_embeddings += 1
                                logger.logger.error(f"OpenAI embedding failed for chunk {chunk_idx} of article {article_idx}: {e}")
                                continue
                            
                            # Store in MongoDB
                            try:
                                chunks_collection.update_one(
                                    {"url": article["url"], "chunk_index": chunk_idx},
                                    {
                                        "$set": {
                                            "url": article["url"],
                                            "title": article.get("title", ""),
                                            "place": state.get("place", "unknown"),
                                            "chunk_index": chunk_idx,
                                            "content_chunk": chunk,
                                            "embedding": embedding,
                                            "tokens_used": tokens_used,
                                            "embedding_model": "text-embedding-3-small"
                                        }
                                    },
                                    upsert=True
                                )
                                
                            except WriteError as e:
                                logger.logger.error(f"Failed to store embedding for chunk {chunk_idx} of article {article_idx}: {e}")
                                failed_embeddings += 1
                            except Exception as e:
                                logger.logger.error(f"Unexpected error storing embedding for chunk {chunk_idx} of article {article_idx}: {e}")
                                failed_embeddings += 1
                            
                        except Exception as e:
                            failed_embeddings += 1
                            logger.logger.error(f"Error processing chunk {chunk_idx} of article {article_idx}: {e}")
                    
                except Exception as e:
                    logger.logger.error(f"Error processing article {article_idx}: {e}")
                    failed_embeddings += 1
            
            # Log embedding metrics
            embedding_metrics = {
                "articles_processed": len(articles),
                "total_chunks": total_chunks,
                "successful_embeddings": successful_embeddings,
                "failed_embeddings": failed_embeddings,
                "total_tokens": total_tokens,
                "success_rate": (successful_embeddings / total_chunks) * 100 if total_chunks > 0 else 0
            }
            
            logger.log_data_metrics("embed_articles", embedding_metrics)
            logger.logger.info(f"✅ Embedding complete: {successful_embeddings}/{total_chunks} chunks embedded, {total_tokens} tokens used")
            
            return {
                **state,
                "embedding_status": "success",
                "embedding_metrics": embedding_metrics
            }
            
        except Exception as e:
            logger.logger.error(f"Database operation error in embedding: {e}")
            raise
            
        finally:
            if client:
                client.close()
                logger.logger.debug("MongoDB connection closed for embeddings")
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in embed_articles: {str(e)}")
        raise

def embed_articles_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when embedding fails
    """
    logger.logger.warning("Using fallback for embedding - no embeddings created")
    
    articles = state.get("articles", [])
    return {
        **state,
        "embedding_status": "fallback",
        "embedding_error": "Embedding failed, using fallback",
        "embedding_metrics": {
            "articles_processed": len(articles),
            "total_chunks": 0,
            "successful_embeddings": 0,
            "failed_embeddings": 0,
            "total_tokens": 0,
            "success_rate": 0
        }
    }