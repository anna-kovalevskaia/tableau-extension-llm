from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi import Request, FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from starlette.responses import JSONResponse

import backend.history as history
from backend.models import Payload
from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.llm_orchestrator import LLMPlanner
from backend.utilities.logging_config import setup_logging
from backend.utilities.prompt import GAMEDEV_PLANNER_SYSTEM_PROMPT
from backend.llm_adapter import ChatAI


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

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"tableau_data_structure": exc.errors()}
    )

@app.post("/api/worksheet_structure")
async def parse_structure(payload: Payload):
    user_id = str(uuid4())
    message_dt_utc = datetime.now(tz=ZoneInfo("UTC")).isoformat()
    try:
        parsed_payload = parse_frontend_payload(payload)
        fixed_schema = [
            row for row in parsed_payload["planner_input"]["schema"]
            if row["name"] not in ("Measure Values", "Measure Names")
        ]
        fixed_schema.extend([
            {"name": f, "type": "float", "isDiscrete": False}
            for row in parsed_payload["interpreter_input"]["filters"]
            for f in row["values"]
            if row["fieldName"] == "Measure Names"
        ])

        parsed_payload["planner_input"]["schema"] = fixed_schema

        for role in ("planner_input", "chunking_input", "interpreter_input"):
            history.add_message(user_id, role, parsed_payload[role], message_dt_utc)
        llm = ChatAI()
        llm_planner = LLMPlanner(GAMEDEV_PLANNER_SYSTEM_PROMPT, user_id, history, llm.ask_gemini)
        llm_planner.get_llm_plan(message_dt_utc)
        return {"user_id": user_id, "history": history.get_history(user_id)}
    except Exception as e:
        logger.error(f"Something went wrong:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)