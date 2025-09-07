# helper/agent_executor.py
import os
import json
from typing import List, Dict, Any
from mofa.utils.files.read import read_yaml
from .utils import agent_config_dir_path, extract_json
from .message_store import load_messages, append_message

class AgentExecutor:
    def __init__(self, client, memory_client, mcp_client, tools: List[Dict[str, Any]], agent=None):
        self.client = client
        self.memory = memory_client
        self.mcp = mcp_client
        self.tools = tools or []
        self.mofa_agent = agent
        self.model = os.getenv("LLM_MODEL_EXECUTOR", "deepseek-chat")
        cfg = read_yaml(os.path.join(agent_config_dir_path, "agent_executor.yml"))
        self.prompt = cfg.get("agent", {}).get("prompt", "")

    def _log(self, msg: str, level: str = "INFO"):
        if self.mofa_agent:
            try:
                self.mofa_agent.write_log(msg, level=level)
            except Exception:
                pass

    def _make_messages(self, user_id: str, clarified_intent: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self.prompt}]
        persisted = load_messages(user_id, "exec")
        messages.extend(persisted)
        # mem0 execution experience hints
        try:
            mem_res = self.memory.search(query=clarified_intent, user_id=user_id, limit=5)
            if isinstance(mem_res, dict) and "results" in mem_res:
                for r in mem_res["results"]:
                    mem_text = r.get("memory") or r.get("memory_text") or r.get("text") or json.dumps(r, ensure_ascii=False)
                    messages.append({"role": "system", "content": f"[mem0_execution_experience]\n{mem_text}"})
                self._log(f"Executor 从 mem0 检索到 {len(mem_res.get('results', []))} 条执行经验", "DEBUG")
        except Exception as e:
            self._log(f"Executor mem0 检索失败: {e}", "WARN")
        messages.append({"role": "user", "content": clarified_intent})
        return messages

    def run(self, clarified_intent: str, user_id: str = "default") -> str:
        self._log(f"Executor.run 开始，clarified_intent={clarified_intent}", "INFO")
        messages = self._make_messages(user_id, clarified_intent)
        append_message(user_id, "exec", {"role": "user", "content": clarified_intent})

        # Call planner LLM with tools
        try:
            if self.tools:
                plan_resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )
            else:
                plan_resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
        except Exception as e:
            self._log(f"Executor LLM 调用失败: {e}", "ERROR")
            return f"错误：执行层 LLM 调用失败: {e}"

        llm_message = plan_resp.choices[0].message
        content = getattr(llm_message, "content", None) or (llm_message.get("content") if isinstance(llm_message, dict) else "")
        # append_message(user_id, "exec", "assistant", content)
        self._log("Executor LLM 返回并已持久化 assistant 消息", "DEBUG")

        # detect tool_calls
        tool_calls = None
        if hasattr(llm_message, "tool_calls"):
            tool_calls = getattr(llm_message, "tool_calls")
        else:
            try:
                tool_calls = llm_message.get("tool_calls")
            except Exception:
                tool_calls = None

        if tool_calls:
            self._log(f"LLM 要调用工具，count={len(tool_calls)}", "INFO")
            for func_call in tool_calls:
                # parse func_call ...
                if hasattr(func_call, "function"):
                    func = func_call.function
                    tool_name = getattr(func, "name", None) or getattr(func_call, "name", None)
                    args_text = getattr(func, "arguments", None)
                    call_id = getattr(func_call, "id", None) or getattr(func_call, "tool_call_id", None)
                else:
                    fdict = func_call.get("function", {})
                    tool_name = fdict.get("name") or func_call.get("name")
                    args_text = fdict.get("arguments") or func_call.get("arguments")
                    call_id = func_call.get("id") or func_call.get("tool_call_id")

                if not tool_name:
                    self._log(f"无法识别工具名 func_call={func_call}", "ERROR")
                    return f"错误：无法识别工具名 (func_call={func_call})"

                try:
                    args = json.loads(args_text) if args_text else {}
                except Exception:
                    args = {"raw_args": args_text}

                self._log(f"调用 MCP 工具 {tool_name}，args={args}", "INFO")
                try:
                    tool_result = self.mcp.call_tool(tool_name, args).content[0].text
                    self._log(f"工具 {tool_name} 返回: {str(tool_result)[:1000]}", "DEBUG")
                except Exception as e:
                    self._log(f"MCP 工具调用失败: {e}", "ERROR")
                    return f"错误：MCP 工具 {tool_name} 调用失败: {e}"

                tool_message = {"role": "user", "content": f"工具 {tool_name} 返回: {tool_result}"}

                append_message(user_id, "exec", tool_message)
                messages.append(tool_message)

            # final LLM call
            try:
                final_resp = self.client.chat.completions.create(model=self.model, messages=messages)
                final_message = final_resp.choices[0].message
                final_content = getattr(final_message, "content", None) or (final_message.get("content") if isinstance(final_message, dict) else "")
                append_message(user_id, "exec", {"role": "assistant", "content": final_content})
                self._log("Executor 最终回复生成并持久化", "INFO")
                return final_content
            except Exception as e:
                self._log(f"Executor 最终 LLM 调用失败: {e}", "ERROR")
                return f"错误：生成最终回复失败: {e}"
        else:
            self._log("Executor: LLM 决定不调用工具，直接返回内容", "DEBUG")
            return content
