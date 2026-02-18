import json
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import backend.ops.history as history
from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.llm_orchestrator import LLMPlanner
from backend.utilities.logging_config import setup_logging
from backend.utilities.prompt import GAMEDEV_PLANNER_SYSTEM_PROMPT
from backend.adapter import ChatAI


load_dotenv()

logger = setup_logging("app.log")

app = FastAPI(
    title="Tableau LLM Chat",
    description="Simple LLM chat interface for Tableau dashboard data"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/configure.html")
def static_config():
    return FileResponse('static/configure.html')

@app.get("/index.html")
def static_index():
    return FileResponse('static/index.html')

@app.post("/api/worksheet_structure")
async def parse_structure(request: Request):
    user_id = str(uuid4())
    payload = await  request.json()
    parsed_payload = parse_frontend_payload(payload)
    message_dt_utc = datetime.now(tz=ZoneInfo("UTC"))
    for role in ("planner_input", "chunking_input", "interpreter_input"):
        history.add_message(user_id, role, parsed_payload[role], message_dt_utc)
    llm = ChatAI()
    llm_planner = LLMPlanner(GAMEDEV_PLANNER_SYSTEM_PROMPT, user_id, history, llm.ask_ollama)

    return {"user_id": user_id}


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)