# helper/agent_am.py
import os
import json
from mofa.utils.files.read import read_yaml
from .utils import agent_config_dir_path, extract_json
from .message_store import load_messages, append_message
from .summarizer import SummarizerAgent

class AgentAM:
    def __init__(self, client, memory_client, executor, summarizer: SummarizerAgent = None, agent=None):
        """
        :param agent: MofaAgent 实例，用于写日志 (agent.write_log)
        """
        self.client = client
        self.memory = memory_client
        self.executor = executor
        self.summarizer = summarizer
        self.mofa_agent = agent
        self.model = os.getenv("LLM_MODEL_AM", "deepseek-chat")
        cfg = read_yaml(os.path.join(agent_config_dir_path, "agent_am.yml"))
        self.prompt = cfg.get("agent", {}).get("prompt", "")

    def _log(self, msg: str, level: str = "INFO"):
        if self.mofa_agent:
            try:
                self.mofa_agent.write_log(msg, level=level)
            except Exception:
                pass

    def _present_mem0_candidates(self, user_id: str, user_input: str, topk: int = 3):
        """从 mem0 搜索历史, 返回候选文本列表"""
        try:
            mem_res = self.memory.search(query=user_input, user_id=user_id, limit=topk)
            if isinstance(mem_res, dict) and "results" in mem_res:
                candidates = []
                for r in mem_res["results"]:
                    mem_text = r.get("memory") or r.get("memory_text") or r.get("text") or json.dumps(r, ensure_ascii=False)
                    candidates.append(mem_text)
                self._log(f"mem0 search 返回 {len(candidates)} 条候选", "DEBUG")
                return candidates
        except Exception as e:
            self._log(f"mem0 search 出错: {e}", "WARN")
        return []

    def run(self, user_input: str, user_id: str = "default", input_role: str = "user") -> dict:
        """
        input_role: 指定传入 user_input 的角色，默认 'user'。当回喂 executor 结果时使用 'agent_executor'。
        """
        # 尝试解析 JSON
        parsed, js_text = extract_json(user_input)
        if parsed is not None and isinstance(parsed, dict):
            next_step = (parsed.get("next_step") or "").upper()
            if next_step == "CLARIFY":
                clar = parsed.get("clarify") or ""
                self._log("AM 返回 CLARIFY", "DEBUG")
                return {"am_result": clar}
            elif next_step == "ABORT":
                self._log("AM 返回 ABORT", "INFO")
                return {"am_result": parsed.get("abort") or "用户取消"}
            elif next_step == "FINISH":
                finish_text = parsed.get("finish") or ""
                self._log("AM 返回 FINISH，触发 Summarizer 存储经验", "INFO")
                # 触发总结器写 mem0
                if self.summarizer:
                    try:
                        self.summarizer.summarize_and_store(user_id, user_input)
                        self._log("Summarizer 运行完成并尝试写入 mem0", "INFO")
                    except Exception as e:
                        self._log(f"Summarizer 写入 mem0 失败: {e}", "WARN")
                return {"am_result": finish_text}
            elif next_step == "CONTINUE":
                clarified_intent = parsed.get("continue") or ""
                self._log(f"Executor 返回 CONTINUE， continue={clarified_intent}", "DEBUG")
                exec_out = self.executor.run(clarified_intent, user_id=user_id)
                append_message(user_id, "am", {"role": "assistant", "content": exec_out})
                self._log("执行层结果已回喂 AM 并持久化", "DEBUG")
                return self.run(exec_out, user_id)
        # 1) 检索 mem0 经验
        self._log(f"AgentAM.run 开始，user_input={user_input}", "INFO")
        candidates = self._present_mem0_candidates(user_id, user_input)
        memory = "\n".join(candidates)
        # 2) 若无候选，按原有流程直接调用 AM LLM
        persisted = load_messages(user_id, "am")
        messages = [{"role": "system", "content": self.prompt}]
        if memory:
            messages.append({"role": "system", "content": f"当前有以下经验：{memory}"})
        messages.extend(persisted)
        messages.append({"role": "user", "content": user_input})

        self._log(f"向 AM LLM 发送消息（role={input_role}）", "DEBUG")
        try:
            resp = self.client.chat.completions.create(model=self.model, messages=messages)
            llm_message = resp.choices[0].message
            content = getattr(llm_message, "content", None) or (llm_message.get("content") if isinstance(llm_message, dict) else "")
        except Exception as e:
            self._log(f"客户经理 LLM 调用失败: {e}", "ERROR")
            return {"am_result": f"错误：客户经理 LLM 调用失败: {e}"}

        append_message(user_id, "am", {"role": "user", "content": user_input})
        append_message(user_id, "am", {"role": llm_message.role, "content": content})
        self._log("AM LLM 返回并已持久化", "DEBUG")

        # 尝试解析 JSON
        parsed, js_text = extract_json(content)
        if parsed is None:
            self._log("AM 返回非 JSON 内容，直接返回文本", "DEBUG")
            return {"am_result": content}

        next_step = (parsed.get("next_step") or "").upper()
        if next_step == "CLARIFY":
            clar = parsed.get("clarify") or ""
            self._log("AM 返回 CLARIFY", "DEBUG")
            return {"am_result": clar}
        elif next_step == "ABORT":
            self._log("AM 返回 ABORT", "INFO")
            return {"am_result": parsed.get("abort") or "用户取消"}
        elif next_step == "FINISH":
            finish_text = parsed.get("finish") or ""
            self._log("AM 返回 FINISH，触发 Summarizer 存储经验", "INFO")
            # 触发总结器写 mem0
            if self.summarizer:
                try:
                    self.summarizer.summarize_and_store(user_id, user_input)
                    self._log("Summarizer 运行完成并尝试写入 mem0", "INFO")
                except Exception as e:
                    self._log(f"Summarizer 写入 mem0 失败: {e}", "WARN")
            return {"am_result": finish_text}
        elif next_step == "CONTINUE":
            clarified_intent = parsed.get("clarified_intent") or parsed.get("continue") or ""
            self._log(f"AM 返回 CONTINUE，clarified_intent={clarified_intent}", "INFO")
            exec_out = self.executor.run(clarified_intent, user_id=user_id)
            append_message(user_id, "am", {"role": "assistant", "content": exec_out})
            self._log("执行层结果已回喂 AM 并持久化", "DEBUG")
            return self.run(exec_out, user_id)
        else:
            self._log(f"AM 返回未知 next_step: {next_step}", "WARN")
            return {"am_result": content}
