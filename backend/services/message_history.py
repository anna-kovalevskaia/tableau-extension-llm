import os
import redis
import json
from dotenv import load_dotenv
load_dotenv()

class HistoryError(Exception):
    pass

r = redis.Redis(host=os.environ['SERVER'], port=6379, db=0)

MAX_HISTORY = 20 # max messages in history
TTL_SECONDS = 600

def add_message(user_id, role, content, message_dt):
    history_key = f"history:{user_id}"
    try:
        chat_history = json.dumps({
            "role": role,
            "content": content,
            "message_time": message_dt
        })
        r.rpush(history_key, chat_history)
        r.ltrim(history_key, -MAX_HISTORY, -1)
        r.expire(history_key, TTL_SECONDS)
    except Exception as e:
        raise HistoryError(f"Redis error while adding message: {e}")


def get_history(user_id):
    history_key = f"history:{user_id}"
    try:
        user_message_history = r.lrange(history_key, 0, -1)
        return [json.loads(m) for m in user_message_history]
    except Exception as e:
        raise HistoryError(f"Redis error while getting message: {e}")

