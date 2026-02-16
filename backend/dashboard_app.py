from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.history import add_message, clean_message_history
from backend.utilities.logging_config import setup_logging

load_dotenv()

logger = setup_logging("app.log")

app = FastAPI(
    title="Tableau LLM Chat",
    description="Simple LLM chat interface for Tableau data"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/configure.html")
def static_config():
    return FileResponse('static/configure.html')

@app.get("/index.html")
def static_index():
    return FileResponse('static/index.html')

@app.post("/api/llm-query")
async def llm_query(request: Request):
    clean_message_history()
    user_id = str(uuid4())
    payload = await  request.json()
    parsed_payload = parse_frontend_payload(payload)
    message_dt_utc = datetime.now(tz=ZoneInfo("UTC"))
    for role in ("planner_input", "chunking_input", "interpreter_input"):
        add_message(user_id, role, parsed_payload[role], message_dt_utc)

    return {"user_id": user_id}


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)