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
from backend.models import Payload, ChunkRequest, ChunkSavePayload
from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.llm_orchestrator import LLMPlanner
from backend.utilities.logging_config import setup_logging
from backend.services.chunk_pipeline import ChunkState
from backend.services.pipeline_context import PipelineContext
from backend.security.code_validation import validate_code


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
        pipeline_states = PipelineContext(user_id)
        for state_type in ("planner_input", "chunking_input", "interpreter_input"):
            pipeline_states.save_pipeline_state(state_type, parsed_payload[state_type])
        # llm = ChatAI()
        # llm_planner_raw = LLMPlanner(
        #   system_prompt_planner = PLANNER,
        #   user_id = user_id,
        #   llm = llm.ask_openai,
        #   history = history
        # )
        # get_plan = llm_planner.get_llm_plan(pipeline_states.get_pipeline_state()["planner_input"])
        # history.add_message(user_id, "assistant", get_plan, message_dt_utc)
        # llm_planner.parse_llm_plan(get_plan)
        with open('backend/tmp_test_llm_resp.txt', 'r', encoding="utf-8") as f:
            test_resp = f.read()
        history.add_message(user_id, 'assistant', test_resp, message_dt_utc)
        llm_planner = LLMPlanner()
        parsed_llm_resp = llm_planner.parse_llm_plan(test_resp)
        validate_code(parsed_llm_resp.code)
        pipeline_states.save_pipeline_state('required_fields', parsed_llm_resp.required_fields)
        pipeline_states.save_pipeline_state('code', parsed_llm_resp.code)
        return {"user_id": user_id}
    except Exception as e:
        logger.error(f"Something went wrong:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


@app.post("/api/nextFilter")
def send_data_request(payload: ChunkRequest):
    user_id = payload.user_id
    pipeline_states = PipelineContext(user_id)
    chunking_input = pipeline_states.get_pipeline_state()["chunking_input"]
    required_fields = pipeline_states.get_pipeline_state()["required_fields"]
    chunk_stat = ChunkState(user_id).update_state_by_chunk()
    request_dict = {
      "worksheetName": chunking_input["worksheetName"],
      "chunkField": chunking_input["chunkFieldName"],
      "chunkValues": chunk_stat["chunk_cur_value"],
      "requiredFields": required_fields,
      "done": chunk_stat["done"],
    }
    return request_dict


@app.post("/api/saveChunk")
def save_chunk(payload: ChunkSavePayload):
    rows = payload.rows
    chunk_stat = ChunkState(payload.user_id)
    return chunk_stat.update_state_by_rows(len(rows), len(rows) == 0)
