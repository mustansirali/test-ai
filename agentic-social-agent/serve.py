import os
import sys
import time
import traceback
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from workflows.daily_workflow import build_workflow
from utils.logger import create_workflow_logger

# Load env
load_dotenv()

app = FastAPI()
logger = create_workflow_logger()

class WorkflowInput(BaseModel):
    place: str
    domains: List[str]
    persona: str = "a concerned citizen"
    tone: str = "Neutral"
    user_perspective: str = ""

def validate_environment() -> bool:
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    return True

def validate_input_data(data: Dict[str, Any]) -> bool:
    if not data.get("place", "").strip():
        logger.logger.error("❌ 'place' is required and cannot be empty.")
        return False
    return True

@app.get("/")
def root():
    return {"status": "Agentic Social Agent is running."}

@app.post("/run")
async def run_workflow(input: WorkflowInput):
    try:
        logger.logger.info("🚀 Received request to run workflow.")

        if not validate_environment():
            raise HTTPException(status_code=500, detail="Missing required environment variables.")

        input_data = input.dict()

        if not validate_input_data(input_data):
            raise HTTPException(status_code=400, detail="Invalid input data: 'place' is required.")

        logger.logger.info(f"📍 Location: {input_data['place']}")
        logger.logger.info(f"📰 Domains: {input_data['domains']}")
        logger.logger.info(f"👤 Persona: {input_data['persona']}")
        logger.logger.info(f"🎭 Tone: {input_data['tone']}")

        workflow = build_workflow()
        config = {"configurable": {"thread_id": f"{input_data['place']}-run"}}

        logger.logger.info("🔧 Executing workflow...")
        start = time.time()
        step_count = 0

        for step in workflow.stream(input_data, config, stream_mode="values"):
            step_count += 1
            step_name = list(step.keys())[0] if step else "unknown"
            logger.logger.info(f"📊 Step {step_count}: {step_name}")

            if "articles" in step:
                logger.logger.info(f"   📄 Articles: {len(step['articles'])}")
            if "summaries" in step:
                logger.logger.info(f"   📝 Summaries: {len(step['summaries'])}")
            if "poll" in step:
                logger.logger.info(f"   📊 Poll: {len(step['poll'].get('options', []))} options")

        duration = time.time() - start
        logger.logger.info(f"✅ Workflow completed in {duration:.2f}s ({step_count} steps)")
        return {"status": "success", "duration": duration, "steps": step_count}

    except Exception as e:
        logger.logger.error(f"❌ Error: {str(e)}")
        logger.logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Workflow failed due to unexpected error.")