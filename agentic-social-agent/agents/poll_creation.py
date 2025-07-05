from typing import Dict, Any, List
from utils.logger import with_error_handling, create_workflow_logger

# Global logger instance
logger = create_workflow_logger()

@with_error_handling(logger, "create_daily_poll")
def create_daily_poll(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a daily poll from articles with comprehensive error handling and logging
    """
    try:
        # Validate input state
        articles = state.get("articles", [])
        if not articles:
            logger.logger.warning("No articles provided for poll creation")
            return {
                **state,
                "poll": {
                    "question": "No articles available for poll creation",
                    "options": ["No options available"],
                    "status": "no_articles"
                },
                "poll_creation_metrics": {"articles_processed": 0, "options_created": 0}
            }
        
        logger.logger.info(f"📊 Creating daily poll from {len(articles)} articles")
        
        # Extract article titles for poll options
        options = []
        valid_articles = 0
        
        for i, article in enumerate(articles[:4]):  # Limit to 4 options
            try:
                if not isinstance(article, dict):
                    logger.logger.warning(f"Invalid article format at index {i}: {type(article)}")
                    continue
                
                title = article.get("title", "")
                if not title:
                    logger.logger.warning(f"Article at index {i} missing title")
                    continue
                
                # Clean and truncate title for poll option
                clean_title = title.strip()
                if len(clean_title) > 100:  # Limit title length for poll
                    clean_title = clean_title[:97] + "..."
                
                options.append(clean_title)
                valid_articles += 1
                
            except Exception as e:
                logger.logger.error(f"Error processing article {i} for poll: {e}")
        
        # Create poll structure
        if not options:
            logger.logger.warning("No valid options created for poll")
            poll = {
                "question": "Which of today's stories do you care most about?",
                "options": ["No articles available"],
                "status": "no_valid_options"
            }
        else:
            poll = {
                "question": "Which of today's stories do you care most about?",
                "options": options,
                "status": "success"
            }
        
        # Log poll creation metrics
        poll_creation_metrics = {
            "articles_processed": len(articles),
            "valid_articles": valid_articles,
            "options_created": len(options),
            "max_options": 4
        }
        
        logger.log_data_metrics("create_daily_poll", poll_creation_metrics)
        logger.logger.info(f"✅ Poll creation complete: {len(options)} options created from {valid_articles} valid articles")
        
        return {
            **state,
            "poll": poll,
            "poll_creation_metrics": poll_creation_metrics
        }
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in create_daily_poll: {str(e)}")
        raise

def create_daily_poll_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when poll creation fails
    """
    logger.logger.warning("Using fallback for poll creation - creating basic poll")
    
    fallback_poll = {
        "question": "Which of today's stories do you care most about?",
        "options": ["Local News", "Community Updates", "Stay Informed"],
        "status": "fallback"
    }
    
    return {
        **state,
        "poll": fallback_poll,
        "poll_creation_status": "fallback",
        "poll_creation_error": "Poll creation failed, using fallback",
        "poll_creation_metrics": {
            "articles_processed": 0,
            "valid_articles": 0,
            "options_created": 3,
            "max_options": 4
        }
    }