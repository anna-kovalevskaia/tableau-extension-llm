import os
import redis

class ChunkStateError(Exception):
    pass

class ChunkState:
    def __init__(self, user_id, ttl_seconds: int = 3600, rows_total: int = 1000000):
        self.r = redis.Redis(host=os.environ['SERVER'], port=6379, db=1)
        self.user_id = user_id
        self.ttl_seconds = ttl_seconds
        self.rows_total = rows_total

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
        For requests a payload for JS.
        """
        chunk_current = self._safe_redis_get(self._key("chunk_cur_value"))

        rows_len = self._safe_redis_get(self._key("data_total_rows"))
        if rows_len >= self.rows_total:
            return {"done": True}
        next_chunk = chunk_current + 1
        self._safe_redis_set(self._key("chunk_cur_value"), next_chunk)
        return {"done": False, "chunk_cur_value": int(next_chunk)}


    def update_state_by_rows(self, chunk_rows_len:int, if_last_chunk: bool = False):
        """
        For returns a request payload for JS.
        """
        if if_last_chunk:
            return {"done": True}

        if chunk_rows_len < 0:
            raise ChunkStateError("chunk_rows_len is less then 0")

        rows_len = self._safe_redis_get(self._key("data_total_rows"))
        update_rows_len = chunk_rows_len + rows_len
        self._safe_redis_set(self._key("data_total_rows"), update_rows_len)
        return {"done": False, "data_total_rows": update_rows_len}