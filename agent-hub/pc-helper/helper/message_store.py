# helper/message_store.py
import json
import os
from typing import List, Dict, Any

MESSAGE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "messages")
os.makedirs(MESSAGE_DIR, exist_ok=True)

def _path_for(user_id: str, agent: str) -> str:
    safe_user = user_id.replace("/", "_")
    filename = f"{safe_user}_{agent}.json"
    return os.path.join(MESSAGE_DIR, filename)

def load_messages(user_id: str, agent: str) -> List[Dict]:
    p = _path_for(user_id, agent)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            os.rename(p, p + ".bak")
        except Exception:
            pass
        return []

def _to_jsonable(obj: Any):
    """递归把 pydantic / 自定义对象转成可 JSON 序列化的 dict/str"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    # pydantic model (OpenAI SDK tool_calls 就是这种)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # fallback: 转字符串
    return str(obj)

def append_message(user_id: str, agent: str, message: Dict):
    """
    保存完整的 message 对象，而不是只存 role/content。
    message 必须是符合 OpenAI Chat API/MCP 的消息结构。
    """
    p = _path_for(user_id, agent)
    data = []
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    # 附加时间戳，但保留完整消息
    message = _to_jsonable(message)
    print(message)
    message["ts"] = int(__import__("time").time())
    data.append(message)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
