import os
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi import Request, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from starlette.responses import JSONResponse

import backend.services.message_history as history
from backend.models import Payload, ChunkRequestsPayload, ChunkPayload
from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.llm_orchestrator import LLMPlanner
from backend.utilities.logging_config import setup_logging
from backend.services.chunk_pipeline import ChunkState

from backend.test import test_plan_resp


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
def parse_structure(payload: Payload):
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
        # llm = ChatAI()
        # llm_planner = LLMPlanner(
        #   system_prompt_planner = PLANNER,
        #   user_id = user_id,
        #   history = history,
        #   llm = llm.ask_openai
        # )
        # get_plan = llm_planner.get_llm_plan(message_dt_utc)
        # llm_planner.parse_llm_plan(get_plan)

        history.add_message(user_id, 'assistant', test_plan_resp, message_dt_utc)
        llm_planner = LLMPlanner()
        llm_planner.parse_llm_plan(test_plan_resp)
    except Exception as e:
        logger.error(f"Something went wrong:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


@app.post("/api/nextFilter")
def send_data_request(payload: ChunkRequestsPayload):
    user_id = payload.user_id
    chunk_hist = next(row for row in history.get_history(user_id) if row['role']=="chunking_input")
    chunk_stat = ChunkState(user_id)
    request_dict = {
      "user_id": user_id,
      "worksheetName": chunk_hist["worksheetName"],
      "chunkField": chunk_hist["chunkFieldName"]
    } | chunk_stat.update_state_by_chunk()
    return request_dict


@app.post("/api/saveChunk")
def save_chunk(payload: ChunkPayload):
    rows = payload.rows
    chunk_stat = ChunkState(payload.user_id)
    return chunk_stat.update_state_by_rows(len(rows), len(rows) == 0)
