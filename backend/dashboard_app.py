from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.utilities.logging_config import setup_logging
logger = setup_logging("app.log")


from dotenv import load_dotenv
load_dotenv()

from backend.ops.frontend_payload_parse import parse_frontend_payload

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
    payload = await  request.json()
    parsed_payload = parse_frontend_payload(payload)
    return parsed_payload



# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)