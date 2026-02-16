from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

_chat_history: Dict[str, List[Dict[str,str]]] = {}

MAX_HISTORY = 20 # max messages in history

def add_message(user_id, role, content, message_dt):
    message_dt_utc = message_dt(tz=ZoneInfo("UTC"))

    if user_id not in _chat_history:
        _chat_history[user_id]=[]

    _chat_history[user_id].append({
        "role": role,
        "content": content,
        "message_time": message_dt_utc
    })

    if len(_chat_history[user_id]) > MAX_HISTORY:
        _chat_history[user_id] = _chat_history[user_id][-MAX_HISTORY:]


def get_history(user_id):
    return _chat_history.get(user_id,[])


def clean_message_history(_chat_history):
    now_utc = datetime.now(tz=ZoneInfo("UTC"))


