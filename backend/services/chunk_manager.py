import os
import shutil

import redis
import polars as pl

class ChunkStateError(Exception):
    pass

class ChunkStorageError(Exception):
    pass

class ChunkState:
    def __init__(self, user_id, ttl_seconds: int = 1800, rows_total: int = 1000000, max_chunk: int = 330):
        self.r = redis.Redis(host=os.environ['SERVER'], port=6379, db=1)
        self.user_id = user_id
        self.ttl_seconds = ttl_seconds
        self.rows_total = rows_total
        self.max_chunk = max_chunk

    def _key(self, name) -> str:
        return f"chunk:{self.user_id}:{name}"

    def _safe_redis_get(self, key: str) -> int:
        try:
            value = self.r.get(key)
            return int(value) if value is not None else 0
        except (redis.ConnectionError, ValueError) as e:
            raise ChunkStateError(f"Failed while reading from Redis:\n{e}")

    def _safe_redis_set(self, key: str, value: int) -> None:
        try:
            self.r.set(key, value, ex=self.ttl_seconds)
        except redis.ConnectionError as e:
            raise ChunkStateError(f"Failed while writing to Redis:\n{e}")

    def update_state_by_chunk(self):
        """
        Requests a payload for JS.
        """
        chunk_current = self._safe_redis_get(self._key("chunk_cur_value"))
        rows_len = self._safe_redis_get(self._key("data_total_rows"))
        if rows_len >= self.rows_total or chunk_current >= self.max_chunk:
            return {"done": True, "chunk_cur_value": None}
        next_chunk = chunk_current + 1
        self._safe_redis_set(self._key("chunk_cur_value"), next_chunk)
        return {"done": False, "data_total_rows": rows_len, "chunk_cur_value": next_chunk}


    def update_state_by_rows(self, chunk_rows_len:int):
        """
        Returns a request payload for JS.
        """
        chunk_num = self._safe_redis_get(self._key("chunk_cur_value"))
        if not chunk_rows_len or chunk_rows_len==0:
            return {"done": True, "chunk_cur_value": None}

        rows_len = self._safe_redis_get(self._key("data_total_rows"))
        update_rows_len = chunk_rows_len + rows_len
        self._safe_redis_set(self._key("data_total_rows"), update_rows_len)
        return {"done": False, "data_total_rows": update_rows_len, "chunk_cur_value": chunk_num }

    def update_state_reset(self):
        self.r.delete(
            self._key("chunk_cur_value"),
            self._key("data_total_rows")
        )


class ChunkStorage:
    def __init__(self, files_path, files_prefix: str = ""):
        self.files_path = files_path
        self.files_prefix = files_prefix
    def save_tmp_files(self, data, chunk_num: int):
        """
        Save data chunk to parquet file
        """
        file_name = f"{self.files_prefix}_{chunk_num}.parquet"
        full_path = os.path.join(self.files_path, file_name)
        try:
            df = pl.DataFrame(data)
            df.write_parquet(full_path)
        except Exception as e:
            raise ChunkStorageError(f"ChunkStorage failed while writing to temp_file:\n{e}")

    def delete_tmp_files(self):
        files_path = self.files_path
        if not os.path.exists(files_path):
            return
        try:
            shutil.rmtree(files_path)
        except Exception as e:
            raise ChunkStorageError(f"ChunkStorage failed. no such directory {e}\t{files_path}")
