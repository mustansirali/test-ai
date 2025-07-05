import time
from typing import Dict, Any
from langgraph.graph import StateGraph, START
from agents import news_search, article_storage, info_extraction, embed, summarize, post_generation, poll_creation
from utils.logger import create_workflow_logger

def build_workflow():
    """Build the daily news processing workflow with comprehensive logging"""
    
    # Create workflow logger
    workflow_logger = create_workflow_logger()
    
    def workflow_start(state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize workflow with logging"""
        workflow_logger.logger.info("🚀 Starting daily news processing workflow")
        workflow_logger.logger.info(f"📋 Input state keys: {list(state.keys())}")
        
        # Add workflow metadata
        workflow_state = {
            **state,
            "workflow_start_time": time.time(),
            "workflow_id": workflow_logger.workflow_id,
            "workflow_status": "started"
        }
        
        return workflow_state
    
    def workflow_end(state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize workflow with summary logging"""
        start_time = state.get("workflow_start_time", time.time())
        total_duration = time.time() - start_time
        
        # Count successful and failed steps
        steps_completed = 0
        steps_failed = 0
        
        step_statuses = [
            "search_articles_status",
            "extract_info_status", 
            "store_articles_status",
            "embed_articles_status",
            "summarize_articles_status",
            "generate_posts_status",
            "create_daily_poll_status"
        ]
        
        for status_key in step_statuses:
            if state.get(status_key) == "failed":
                steps_failed += 1
            elif status_key in state:
                steps_completed += 1
        
        # Log workflow completion
        workflow_logger.log_workflow_complete(total_duration, steps_completed, steps_failed)
        
        # Add final workflow metadata
        final_state = {
            **state,
            "workflow_end_time": time.time(),
            "workflow_total_duration": total_duration,
            "workflow_steps_completed": steps_completed,
            "workflow_steps_failed": steps_failed,
            "workflow_status": "completed"
        }
        
        workflow_logger.logger.info("🎉 Workflow completed successfully")
        return final_state
    
    # Build the graph
    builder = StateGraph(dict)

    # Define nodes with error handling
    builder.add_node("workflow_start", workflow_start)
    builder.add_node("search_articles", news_search.search_articles)
    builder.add_node("extract_info", info_extraction.extract_info)
    builder.add_node("store_articles", article_storage.store_articles)
    builder.add_node("embed_articles", embed.embed_articles)
    builder.add_node("summarize_articles", summarize.summarize_articles)
    builder.add_node("generate_posts", post_generation.generate_posts)
    builder.add_node("create_daily_poll", poll_creation.create_daily_poll)
    builder.add_node("workflow_end", workflow_end)

    # Define edges
    builder.add_edge(START, "workflow_start")
    builder.add_edge("workflow_start", "search_articles")
    builder.add_edge("search_articles", "extract_info")
    builder.add_edge("extract_info", "store_articles")
    builder.add_edge("store_articles", "embed_articles")
    builder.add_edge("embed_articles", "summarize_articles")
    builder.add_edge("summarize_articles", "generate_posts")
    builder.add_edge("generate_posts", "create_daily_poll")
    builder.add_edge("create_daily_poll", "workflow_end")

    return builder.compile()