import os
import redis
import json
from dotenv import load_dotenv
load_dotenv()

class PipelineStateError(Exception):
    pass

class PipelineContext:
    def __init__(self, user_id, ttl_seconds: int = 600):
        self.r = redis.Redis(host=os.environ['SERVER'], port=6379, db=2)
        self.user_id = user_id
        self.ttl_seconds = ttl_seconds

    def save_pipeline_state(self, state_type, content):
        state_key = f"pipeline_state:{self.user_id}"
        try:
            state_raw = self.r.get(state_key)
            state = json.loads(state_raw) if state_raw else {}
            state[state_type] = content
            self.r.set(state_key, json.dumps(state), ex=self.ttl_seconds)
        except Exception as e:
            raise PipelineStateError(f"Redis error while updating states: {e}")


    def get_pipeline_state(self):
        state_key = f"pipeline_state:{self.user_id}"
        try:
            return json.loads(self.r.get(state_key))
        except Exception as e:
            raise PipelineStateError(f"Redis error while getting pipeline state: {e}")

