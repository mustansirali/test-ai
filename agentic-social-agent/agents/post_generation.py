import os
import time
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import with_error_handling, create_workflow_logger

load_dotenv()

# Global logger instance
logger = create_workflow_logger()

@with_error_handling(logger, "generate_posts")
def generate_posts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate social media posts using OpenAI with comprehensive error handling and logging
    """
    try:
        # Validate required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        openai = OpenAI(api_key=openai_api_key)
        
        # Extract input parameters with defaults
        summary = state.get("summary") or state.get("extracted_info") or ""
        persona = state.get("persona", "a concerned citizen")
        tone = state.get("tone", "Neutral")
        user_perspective = state.get("user_perspective", "")
        
        logger.logger.info(f"📱 Generating social media posts for persona: {persona}, tone: {tone}")
        
        # Validate input
        if not summary:
            logger.logger.warning("No summary or extracted_info provided for post generation")
            return {
                **state,
                "posts": {},
                "post_generation_metrics": {"posts_generated": 0, "errors": 1}
            }
        
        posts = {}
        successful_posts = 0
        failed_posts = 0
        total_tokens = 0
        
        # Generate posts for different character limits
        character_limits = [50, 100, 500]
        
        for cap in character_limits:
            try:
                # Construct prompt
                prompt = (
                    f"Write a {tone} social media post in under {cap} characters from the perspective of "
                    f"{persona}.\n\nSummary: {summary}\n\nAdditional thoughts: {user_perspective}"
                )
                
                # Generate post with timing
                post_start = time.time()
                try:
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=cap + 50,  # Allow some buffer
                        temperature=0.7
                    )
                    
                    post_duration = time.time() - post_start
                    post_content = response.choices[0].message.content.strip()
                    tokens_used = response.usage.total_tokens if response.usage else 0
                    total_tokens += tokens_used
                    
                    # Validate post length
                    if len(post_content) > cap:
                        logger.logger.warning(f"Generated post exceeds {cap} character limit: {len(post_content)} chars")
                        # Truncate if necessary
                        post_content = post_content[:cap-3] + "..."
                    
                    posts[f"post_{cap}"] = post_content
                    successful_posts += 1
                    
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="success",
                        duration=post_duration,
                        model="gpt-4",
                        tokens_used=tokens_used,
                        character_limit=cap,
                        actual_length=len(post_content)
                    )
                    
                except Exception as e:
                    post_duration = time.time() - post_start
                    logger.log_api_call(
                        service="OpenAI",
                        endpoint="chat/completions",
                        status="error",
                        duration=post_duration,
                        error=str(e),
                        character_limit=cap
                    )
                    failed_posts += 1
                    posts[f"post_{cap}"] = f"Post generation failed for {cap} characters"
                    logger.logger.error(f"OpenAI post generation failed for {cap} characters: {e}")
                
            except Exception as e:
                failed_posts += 1
                posts[f"post_{cap}"] = f"Post generation failed for {cap} characters"
                logger.logger.error(f"Error generating post for {cap} characters: {e}")
        
        # Log post generation metrics
        post_generation_metrics = {
            "posts_generated": successful_posts,
            "posts_failed": failed_posts,
            "total_tokens": total_tokens,
            "character_limits": character_limits,
            "success_rate": (successful_posts / len(character_limits)) * 100
        }
        
        logger.log_data_metrics("generate_posts", post_generation_metrics)
        logger.logger.info(f"✅ Post generation complete: {successful_posts}/{len(character_limits)} posts generated, {total_tokens} tokens used")
        
        return {
            **state,
            **posts,
            "post_generation_metrics": post_generation_metrics
        }
        
    except Exception as e:
        logger.logger.error(f"Unexpected error in generate_posts: {str(e)}")
        raise

def generate_posts_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback function for when post generation fails
    """
    logger.logger.warning("Using fallback for post generation - creating basic posts")
    
    # Create simple fallback posts
    fallback_posts = {
        "post_50": "Stay informed about local news.",
        "post_100": "Important developments happening in our community. Stay tuned for updates.",
        "post_500": "Local news update: There have been recent developments in our area that may affect our community. We're monitoring the situation and will share more information as it becomes available. Stay informed and stay safe."
    }
    
    return {
        **state,
        **fallback_posts,
        "post_generation_status": "fallback",
        "post_generation_error": "Post generation failed, using fallback",
        "post_generation_metrics": {
            "posts_generated": 3,
            "posts_failed": 0,
            "total_tokens": 0,
            "character_limits": [50, 100, 500],
            "success_rate": 100
        }
    }