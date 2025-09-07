# helper/summarizer.py
import json
from .message_store import load_messages
from .utils import extract_json
from typing import Dict
from mofa.utils.files.read import read_yaml
from .utils import agent_config_dir_path
import os

class SummarizerAgent:
    def __init__(self, client, memory_client, agent=None):
        self.client = client
        self.memory = memory_client
        self.mofa_agent = agent
        self.model = os.getenv("LLM_MODEL_SUM", os.getenv("LLM_MODEL_AM", "deepseek-chat"))
        self.prompt = (
            "你是经验总结器。输入中包含用户原始模糊输入、客户经理和执行层的对话历史、以及相关历史记忆。"
            "请输出一个 JSON，包含两个字段："
            "1) intent_summary: 对用户模糊输入的结构化意图（字段名和值）"
            "2) plan_summary: 针对该意图的可复用执行方案要点（必要参数、调用的工具/脚本、注意事项）"
            "要求输出纯 JSON。"
        )

    def _log(self, msg: str, level: str = "INFO"):
        if self.mofa_agent:
            try:
                self.mofa_agent.write_log(msg, level=level)
            except Exception:
                pass

    def _collect_context(self, user_id: str):
        am_msgs = load_messages(user_id, "am")
        exec_msgs = load_messages(user_id, "exec")
        return {"am_messages": am_msgs, "exec_messages": exec_msgs}

    def summarize_and_store(self, user_id: str, user_input: str) -> bool:
        self._log(f"Summarizer 触发，user_input={user_input}", "INFO")
        ctx = self._collect_context(user_id)
        prompt_text = f"用户原始输入:\n{user_input}\n\n上下文:\n{json.dumps(ctx, ensure_ascii=False)}\n\n请生成 JSON：{{'intent_summary':..., 'plan_summary':...}}"
        try:
            resp = self.client.chat.completions.create(model=self.model, messages=[{"role":"system","content":self.prompt}, {"role":"user","content":prompt_text}])
            out = resp.choices[0].message.content
        except Exception as e:
            self._log(f"Summarizer LLM 调用失败: {e}", "ERROR")
            out = f"错误：Summary LLM 调用失败: {e}"

        parsed = None
        try:
            parsed = json.loads(out)
        except Exception:
            import re
            m = re.search(r'(\{.*\})', out, re.S)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                except Exception:
                    parsed = None

        if not parsed:
            mem_text = f"UserInput: {user_input}\nSummarizerRaw: {out}"
            try:
                self.memory.add([{"role":"system","content":mem_text}], user_id=user_id)
                self._log("Summarizer 未能解析 JSON，存储 raw summary 到 mem0", "WARN")
            except Exception:
                self._log("Summarizer 写入 mem0 失败", "ERROR")
            return False

        try:
            intent_entry = {"role":"system", "content": f"INTENT:{json.dumps(parsed.get('intent_summary'), ensure_ascii=False)}"}
            plan_entry = {"role":"system", "content": f"PLAN:{json.dumps(parsed.get('plan_summary'), ensure_ascii=False)}"}
            self.memory.add([intent_entry], user_id=user_id)
            self.memory.add([plan_entry], user_id=user_id)
            self._log("Summarizer 将意图和方案写入 mem0 成功", "INFO")
            return True
        except Exception as e:
            self._log(f"Summarizer 写入 mem0 失败: {e}", "ERROR")
            return False
