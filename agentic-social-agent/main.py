import os
from dotenv import load_dotenv
from workflows.daily_workflow import build_workflow

load_dotenv()

def main():
    workflow = build_workflow()
    config = {"configurable": {"thread_id": "daily-run"}}
    input_data = {
        "query": "Austin Texas latest news",
        "domains": [
            "fox7austin.com", "texastribune.org", "austintexas.gov",
            "kxan.com", "ksat.com", "cbsaustin.com"
        ],
        "persona": "a concerned citizen",
        "tone": "Neutral"
    }
    for step in workflow.stream(input_data, config, stream_mode="values"):
        print(step)

if __name__ == "__main__":
    main()