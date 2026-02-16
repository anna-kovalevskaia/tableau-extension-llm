from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

_chat_history: Dict[str, List[Dict[str, Any]]] = {}

MAX_HISTORY = 20 # max messages in history
TTL_SECONDS = 600

def add_message(user_id, role, content, message_dt):
    if user_id not in _chat_history:
        _chat_history[user_id]=[]

    _chat_history[user_id].append({
        "role": role,
        "content": content,
        "message_time": message_dt
    })

    if len(_chat_history[user_id]) > MAX_HISTORY:
        _chat_history[user_id] = _chat_history[user_id][-MAX_HISTORY:]


def get_history(user_id):
    return _chat_history.get(user_id,[])


def clean_message_history():
    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    expired_users = [
        user
        for user, message in _chat_history.items()
        if int((now_utc - message[-1]["message_time"]).total_seconds()) > TTL_SECONDS
    ]

    for expired_user in expired_users:
            _chat_history.pop(expired_user, None)

