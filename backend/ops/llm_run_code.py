import datetime
import glob
import polars as pl
from backend.security.code_execution import SaveExecution
from backend.services.pipeline_context import PipelineContext

def convert_dates(obj):
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_dates(v) for v in obj]
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    return obj

def execute_llm_code(user_id, files_path, code, extra_globals=None):
    files = glob.glob(f"{files_path}/*.parquet")
    fields_type = PipelineContext(user_id).get_pipeline_state()["required_fields_with_types"]
    df = pl.read_parquet(files)

    for col, t in fields_type.items():
        if t == "date":
            df = df.with_columns([
                pl.col(col)
                .cast(pl.Utf8, strict=False)
                .str.replace("%null%", None)
                .str.replace(r"^\s*$", None, literal=False)
                .str.strptime(pl.Date, strict=False)
            ])

    cast_map = {}
    for col, t in fields_type.items():
        if t == "date":
            cast_map[col] = pl.Date
        elif t == "float":
            cast_map[col] = pl.Float64
        elif t == "integer":
            cast_map[col] = pl.Int64
        elif t == "string":
            cast_map[col] = pl.Utf8

    data_df = df.with_columns([
        pl.col(col).cast(dtype)
        for col, dtype in cast_map.items()
    ])
    save_execut = SaveExecution()
    sandbox_globals = save_execut.build_sandbox_globals(extra_globals)

    sandbox_globals['data_df'] = data_df
    sandbox_locals = {}
    try:
        # save_execut.limit_resources() # doesnt work for windows
        exec(code, sandbox_globals, sandbox_locals)
    except Exception as e:
        raise RuntimeError(f"Error during code execution: {e}") from e
    finally:
        save_execut.restore_originals()

    return convert_dates(sandbox_locals.get("result"))
