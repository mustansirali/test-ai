import os
import sys
import time
import traceback
from typing import Dict, Any
from dotenv import load_dotenv
from workflows.daily_workflow import build_workflow
from utils.logger import create_workflow_logger

# Load environment variables
load_dotenv()

def validate_environment() -> bool:
    """Validate that all required environment variables are set"""
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    # Optional MongoDB validation
    if not os.getenv("MONGODB_URI"):
        print("⚠️  MONGODB_URI not set - some features may be limited")
    
    return True

def validate_input_data(input_data: Dict[str, Any]) -> bool:
    """Validate input data structure"""
    required_keys = ["place"]
    missing_keys = []
    
    for key in required_keys:
        if key not in input_data:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing required input keys: {', '.join(missing_keys)}")
        return False
    
    # Validate place is not empty
    if not input_data.get("place", "").strip():
        print("❌ 'place' cannot be empty")
        return False
    
    return True

def main():
    """Main function with comprehensive error handling and logging"""
    
    # Create main logger
    logger = create_workflow_logger()
    
    try:
        logger.logger.info("🚀 Starting Agentic Social Agent")
        
        # Validate environment
        if not validate_environment():
            logger.logger.error("Environment validation failed")
            sys.exit(1)
        
        # Define input data
        input_data = {
            "place": "Austin Texas",
            "domains": [
                "fox7austin.com", "texastribune.org", "austintexas.gov",
                "kxan.com", "ksat.com", "cbsaustin.com"
            ],
            "persona": "a concerned citizen",
            "tone": "Neutral",
            "user_perspective": ""
        }
        
        # Validate input data
        if not validate_input_data(input_data):
            logger.logger.error("Input data validation failed")
            sys.exit(1)
        
        logger.logger.info(f"📋 Processing news for: {input_data['place']}")
        logger.logger.info(f"📰 Domains: {input_data['domains']}")
        logger.logger.info(f"👤 Persona: {input_data['persona']}")
        logger.logger.info(f"🎭 Tone: {input_data['tone']}")
        
        # Build workflow
        logger.logger.info("🔧 Building workflow...")
        workflow = build_workflow()
        
        # Configure workflow
        config = {"configurable": {"thread_id": "daily-run"}}
        
        # Execute workflow with streaming
        logger.logger.info("⚡ Executing workflow...")
        workflow_start_time = time.time()
        
        step_count = 0
        for step in workflow.stream(input_data, config, stream_mode="values"):
            step_count += 1
            step_name = list(step.keys())[0] if step else "unknown"
            logger.logger.info(f"📊 Step {step_count}: {step_name}")
            
            # Log step-specific information
            if "articles" in step:
                article_count = len(step["articles"]) if isinstance(step["articles"], list) else 0
                logger.logger.info(f"   📄 Articles found: {article_count}")
            
            if "summaries" in step:
                summary_count = len(step["summaries"]) if isinstance(step["summaries"], dict) else 0
                logger.logger.info(f"   📝 Summaries created: {summary_count}")
            
            if "posts" in step or any(key.startswith("post_") for key in step.keys()):
                post_count = sum(1 for key in step.keys() if key.startswith("post_"))
                logger.logger.info(f"   📱 Posts generated: {post_count}")
            
            if "poll" in step:
                poll = step.get("poll", {})
                options_count = len(poll.get("options", [])) if isinstance(poll, dict) else 0
                logger.logger.info(f"   📊 Poll created with {options_count} options")
        
        workflow_duration = time.time() - workflow_start_time
        logger.logger.info(f"✅ Workflow completed in {workflow_duration:.2f} seconds")
        
        # Log final summary
        logger.logger.info("📈 Workflow Summary:")
        logger.logger.info(f"   ⏱️  Total duration: {workflow_duration:.2f}s")
        logger.logger.info(f"   🔄 Steps executed: {step_count}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.logger.warning("⚠️  Workflow interrupted by user")
        return 1
        
    except Exception as e:
        logger.logger.error(f"❌ Unexpected error in main: {str(e)}")
        logger.logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


# TODO: 
# - Implement caching for repeated queries
# - Consider using a more sophisticated state management system
# - Image more complex agent instructions to research and find supportive material to generative comprehensive understanding of the current events as it pertains to politics
