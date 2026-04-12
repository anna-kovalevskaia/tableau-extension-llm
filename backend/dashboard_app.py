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
from backend.services.chunk_manager import ChunkState, ChunkStorage
from backend.services.pipeline_context import PipelineContext
from backend.services.llm_adapter import ChatAI

from backend.models import Payload, ChunkRequest, ChunkSavePayload, RunAnalysis

from backend.ops.frontend_payload_parse import parse_frontend_payload
from backend.ops.llm_orchestrator import LLMPlanner, LLMInterpreter
from backend.ops.llm_run_code import execute_llm_code

from backend.utilities.logging_config import setup_logging
from backend.utilities.prompt import PLANNER_STEP1, PLANNER_STEP2,INTERPRETER

from backend.security.code_validation import validate_code


load_dotenv()

logger = setup_logging("app.log")

app = FastAPI(
    title="Tableau LLM Chat",
    description="Simple LLM chat interface for Tableau dashboard data"
)
temp_dir = os.environ['TEMP_FILES_DIR']
os.makedirs(temp_dir, exist_ok=True)

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
        pipeline_states = PipelineContext(user_id)

        for state_type in ("planner_input", "chunking_input", "interpreter_input", "service_fields"):
            pipeline_states.save_pipeline_state(state_type, parsed_payload[state_type])

        llm = ChatAI()
        llm_planner = LLMPlanner(
          system_prompt_planner = PLANNER_STEP1,
          user_id = user_id,
          llm = llm.ask_ollama,
          history = history
        )
        planner_input = pipeline_states.get_pipeline_state()["planner_input"]
        get_plan_step1 = llm_planner.get_llm_plan(planner_input)

        llm_planner = LLMPlanner(
          system_prompt_planner = PLANNER_STEP2,
          user_id = user_id,
          llm = llm.ask_openai,
          history = history
        )
        get_plan_step2 = llm_planner.get_llm_plan(payload.question+'\n'+get_plan_step1)
        parsed_llm_resp = llm_planner.parse_llm_plan(get_plan_step2)

        history.add_message(user_id, 'user', payload.question, message_dt_utc)
        history.add_message(user_id, "assistant", get_plan_step2, message_dt_utc)

        required_fields_with_types = {
            required_field: sh["type"]
            for required_field in parsed_llm_resp.required_fields
            for sh in planner_input["schema"]
            if sh["name"] == required_field
        }
        pipeline_states.save_pipeline_state("required_fields_with_types", required_fields_with_types)
        validate_code(parsed_llm_resp.code)

        measure_names = pipeline_states.get_pipeline_state()["service_fields"]["Measure Names"]
        required_fields= [{"otherRequiredFieldNames": parsed_llm_resp.required_fields}]
        if measure_names:
            required_fields.append({
                "measureNames": list(set(measure_names) & set(parsed_llm_resp.required_fields))
            })

        pipeline_states.save_pipeline_state('required_fields', required_fields)
        pipeline_states.save_pipeline_state('code', parsed_llm_resp.code)

        str_date_tm = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_prefix = f"_temp_{user_id}_{str_date_tm}"

        files_path = os.path.join(temp_dir, files_prefix)
        os.makedirs(files_path, exist_ok=True)

        pipeline_states.save_pipeline_state('files_path', files_path)
        pipeline_states.save_pipeline_state('files_prefix', files_prefix)

        return {"user_id": user_id }
    except Exception as e:
        logger.error(f"Something went wrong:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


@app.post("/api/nextFilter")
def send_data_request(payload: ChunkRequest):
    user_id = payload.user_id
    pipeline_states = PipelineContext(user_id).get_pipeline_state()
    chunking_input = pipeline_states["chunking_input"]
    required_fields = pipeline_states["required_fields"]
    files_path = pipeline_states["files_path"]
    try:
        chunk_stat = ChunkState(user_id).update_state_by_chunk()
        request_dict = {
          "worksheetName": chunking_input["worksheetName"],
          "chunkField": chunking_input["chunkFieldName"],
          "chunkValues": chunk_stat["chunk_cur_value"],
          "requiredFields": required_fields,
          "done": chunk_stat["done"],
        }
        return request_dict
    except Exception as e:
        ChunkStorage(files_path).delete_tmp_files()
        logger.error(f"Something went wrong while sending next chunk structure:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


@app.post("/api/saveChunk")
def save_chunk(payload: ChunkSavePayload):
    user_id = payload.user_id
    files_path = PipelineContext(payload.user_id).get_pipeline_state()["files_path"]
    files_pref = PipelineContext(payload.user_id).get_pipeline_state()["files_prefix"]
    try:
        rows = payload.rows
        chunk_stat = ChunkState(user_id)
        state_by_rows = chunk_stat.update_state_by_rows(len(rows))
        chunk_storage = ChunkStorage(files_path, files_pref)
        chunk_storage.save_tmp_files(rows, state_by_rows["chunk_cur_value"])
        return state_by_rows
    except Exception as e:
        ChunkStorage(files_path).delete_tmp_files()
        logger.error(f"Something went wrong while saving chunk data:\n{e}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})


@app.post("/api/runAnalysis")
def run_data_analysis(payload: RunAnalysis):
    user_id = payload.user_id
    pipeline_states = PipelineContext(user_id).get_pipeline_state()

    files_path = pipeline_states["files_path"]
    code = pipeline_states["code"]
    interpreter_input = pipeline_states["interpreter_input"]
    try:
        result = execute_llm_code(user_id, files_path, code)
        ChunkStorage(files_path).delete_tmp_files()

        llm = ChatAI()
        llm_inter = LLMInterpreter(
          system_prompt_interpreter = INTERPRETER,
          user_id = user_id,
          llm = llm.ask_openai,
          history=history
        )

        final_answer = llm_inter.llm_interpretation(result, interpreter_input)
        return final_answer
    except Exception as e:
        ChunkStorage(files_path).delete_tmp_files()
        logger.error(f"Something went wrong while analysing data:\n{e}\n{code}")
        raise HTTPException(status_code=500, detail={"detail": str(e)})
