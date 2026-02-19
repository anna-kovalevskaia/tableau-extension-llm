from backend.utilities.logging_config import setup_logging
from backend.models import Payload
logger = setup_logging(filename='frontend_payload_parse.log')

class JSPayloadError(Exception):
    pass

def parse_frontend_payload(payload: Payload):
    try:
        worksheet = payload.worksheet
        chunk_field_name = worksheet.chunkField
        chunk_field_context = [
            row.model_dump() for row in worksheet.schema if chunk_field_name and row.name==chunk_field_name
        ]
        chunk_field_type = chunk_field_context[0]["type"] if chunk_field_context else None

        return {
            "planner_input": {
                "question": payload.question,
                "schema": worksheet.schema
            },
            "chunking_input": {
                "chunkFieldName": chunk_field_name,
                "chunkFieldType": chunk_field_type,
                "worksheetName": worksheet.worksheetName
            },
            "interpreter_input": {
                "filters": worksheet.filters
            }
        }
    except Exception as e:
        logger.error(f"Json is invalid {payload.model_dump()}:\n{e}")
        raise JSPayloadError(f"Json is invalid:\n{e}")