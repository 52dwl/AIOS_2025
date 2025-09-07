# helper/utils.py
import os
import datetime
import json
from dotenv import load_dotenv
from openai import OpenAI

agent_config_dir_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config")

def create_openai_client(file_path: str = ".env"):
    env_file = os.getenv("ENV_FILE", file_path)
    if not os.path.exists(env_file):
        raise FileNotFoundError(f"未找到环境配置文件: {env_file}, 请创建并设置 LLM_API_KEY / OPENAI_API_KEY")
    load_dotenv(env_file)
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not LLM_API_KEY:
        raise ValueError("未找到有效的 API 密钥，请在 .env 中设置 LLM_API_KEY 或 OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", None)
    return OpenAI(api_key=LLM_API_KEY, base_url=base_url)

def generate_system_prompt(system_prompt_raw: str, **kwargs) -> str:
    return system_prompt_raw.format(
        date=datetime.datetime.now().strftime("%Y-%m-%d"),
        system=os.name,
        username=os.getlogin(),
        workdir=os.getcwd(),
        abilities=kwargs.get("abilities", ""),
        tools=kwargs.get("tools", ""),
        language="zh-CN",
    )

def extract_json(text: str):
    """
    尝试从 text 中提取第一个 JSON 对象或数组并返回 (obj, json_text).
    返回 (None, None) 表示解析失败。
    更鲁棒：允许周围有前导说明文字。
    """
    if not text or not isinstance(text, str):
        return None, None

    # 直接尝试全部解析
    try:
        obj = json.loads(text)
        return obj, text
    except Exception:
        pass

    # 搜索第一个 {...} 或 [...]
    stack = []
    start = None
    for i, ch in enumerate(text):
        if ch == '{' or ch == '[':
            if start is None:
                start = i
            stack.append(ch)
        elif ch == '}' or ch == ']':
            if stack:
                stack.pop()
                if not stack and start is not None:
                    candidate = text[start:i+1]
                    # 修正一些常见非标准引号问题
                    cleaned = candidate.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
                    try:
                        obj = json.loads(cleaned)
                        return obj, cleaned
                    except Exception:
                        # 继续向后寻找下一个可能片段
                        start = None
                        stack = []
                        continue
    return None, None
