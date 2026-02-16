from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.history import add_message
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
    user_id = str(uuid4())
    payload = await  request.json()
    parsed_payload = parse_frontend_payload(payload)
    add_message(user_id=user_id, role="planner_input", content=parsed_payload["planner_input"])
    add_message(user_id=user_id, role="chunking_input", content=parsed_payload["chunking_input"])
    add_message(user_id=user_id, role="interpreter_input", content=parsed_payload["interpreter_input"])

    return {"user_id": user_id}


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)