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
        filters = [ # without server fields
            f.model_dump() for f in worksheet.filters if f.fieldName!="Measure Names" and f.fieldName!=chunk_field_name
        ] if worksheet.filters else None

        measure_filters = next(f.values for f in worksheet.filters if f.fieldName=="Measure Names") if worksheet.filters else None

        filtered_schema = [
            row for row in ws_schema
            if row["name"] not in ("Measure Values", "Measure Names")
        ]
        if measure_filters:
            filtered_schema.extend([
                {"name": f_value, "type": "float", "isDiscrete": False}
                for f_value in measure_filters
            ])

        return {
            "planner_input": {
                "question": payload.question,
                "schema": filtered_schema,
            },
            "chunking_input": {
                "chunkFieldName": chunk_field_name,
                "chunkFieldType": chunk_field_type,
                "worksheetName": worksheet.worksheetName
            },
            "interpreter_input": {
                "filters": filters
            },
            "service_fields": {
                "Measure Names": measure_filters
            }
        }
    except Exception as e:
        raise JSPayloadError(f"Json is invalid:\n{e}")