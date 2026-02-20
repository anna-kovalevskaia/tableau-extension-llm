from backend.models import Payload

class JSPayloadError(Exception):
    pass

def parse_frontend_payload(payload: Payload):
    try:
        worksheet = payload.worksheet
        chunk_field_name = worksheet.chunkField
        ws_schema = [row.model_dump() for row in worksheet.schema]
        chunk_field_context = [
            row for row in ws_schema if chunk_field_name and row["name"]==chunk_field_name
        ]
        chunk_field_type = chunk_field_context[0]["type"] if chunk_field_context else None

        return {
            "planner_input": {
                "question": payload.question,
                "schema": ws_schema,
            },
            "chunking_input": {
                "chunkFieldName": chunk_field_name,
                "chunkFieldType": chunk_field_type,
                "worksheetName": worksheet.worksheetName
            },
            "interpreter_input": {
                "filters": [f.model_dump() for f in worksheet.filters] if worksheet.filters else None
            }
        }
    except Exception as e:
        raise JSPayloadError(f"Json is invalid:\n{e}")