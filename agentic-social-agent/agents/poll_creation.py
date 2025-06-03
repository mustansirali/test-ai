def create_daily_poll(events: list):
    # Simplified example: create a poll question based on event titles
    poll_question = "Which of today's events interests you the most?"
    options = [event["title"] for event in events[:4]]  # Limit to 4 options
    return {"question": poll_question, "options": options}