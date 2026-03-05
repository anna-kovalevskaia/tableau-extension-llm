import glob
import polars as pl
from backend.security.code_execution import SaveExecution

def execute_llm_code(files_path, code, extra_globals=None):
    files = glob.glob(f"{files_path}/*.parquet")
    data_df = pl.read_parquet(files)

    save_execut = SaveExecution()
    sandbox_globals = save_execut.build_sandbox_globals(extra_globals)

    sandbox_globals['data_df'] = data_df
    sandbox_locals = {}

    try:
        save_execut.limit_resources() # doesnt work for windows
        exec(code, sandbox_globals, sandbox_locals)
    except Exception as e:
        raise RuntimeError(f"Error during code execution: {e}") from e
    finally:
        save_execut.restore_originals()

    return sandbox_locals.get("result")