def parse_frontend_payload(payload):
    worksheet = payload["worksheet"]
    chunk_field_name = worksheet.get("chunkField")
    chunk_field_context = [row for row in worksheet["schema"] if chunk_field_name and row.get("name")==chunk_field_name]
    chunk_field_type = None
    if chunk_field_context:
        chunk_field_type = chunk_field_context[0]["type"]

    return {
        "planner_input": {
            "question": payload["question"],
            "schema": worksheet["schema"]
        },
        "chunking_input": {
            "chunkFieldName": chunk_field_name,
            "chunkFieldType": chunk_field_type,
            "worksheetName": worksheet["worksheetName"]
        },
        "interpreter_input": {
            "filters": worksheet["filters"]
        }
    }