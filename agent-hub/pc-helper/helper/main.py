# helper/main.py
import os
from mofa.agent_build.base.base_agent import run_agent, MofaAgent
from mofa.utils.files.read import read_yaml
from .utils import create_openai_client
from .mcp_client import PersistentMCPClient
from .mem0_client import Mem0Client
from .agent_executor import AgentExecutor
from .agent_am import AgentAM
from .summarizer import SummarizerAgent
from .message_store import append_message

@run_agent
def run(agent: MofaAgent):
    user_input = agent.receive_parameter("user_input") or ""
    if user_input.strip() == "":
        return
    user_id = os.getenv("USER_ID", "pc-helper")

    agent.write_log(f"启动会话，user_id={user_id}, user_input={user_input}", level="INFO")

    # 1) OpenAI client
    client = create_openai_client()
    agent.write_log("OpenAI client 已创建", level="INFO")

    # 2) mem0 init (sync)
    mem_config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config", "memory_config.yml")
    mem_conf = {}
    try:
        mem_conf = read_yaml(mem_config_path).get('agent',{})
        mem_conf['llm']['config']['api_key'] = os.getenv("LLM_API_KEY")
        agent.write_log(f"读取 mem0 config: {mem_config_path}", level="INFO")
    except Exception as e:
        agent.write_log(f"读取 mem0 配置失败: {e}", level="WARN")

    mem_client = Mem0Client()
    try:
        mem_client.init_from_config(mem_conf)
        agent.write_log("mem0 初始化成功", level="INFO")
    except Exception as e:
        agent.write_log(f"mem0 初始化失败: {e}", level="ERROR")
        # 继续运行，但 mem0 功能将不可用

    # 3) persistent mcp client
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/sse")
    p_mcp = PersistentMCPClient(url=mcp_url, agent=agent)
    try:
        p_mcp.start()
        agent.write_log("PersistentMCPClient started", level="INFO")
    except Exception as e:
        agent.write_log(f"PersistentMCPClient start failed: {e}", level="ERROR")

    try:
        tools = p_mcp.list_tools()
        agent.write_log(f"MCP tools 列表获取成功: {len(tools)} 个工具", level="INFO")
    except Exception as e:
        tools = []
        agent.write_log(f"获取 MCP tools 失败: {e}", level="WARN")

    # 4) agents and summarizer
    # summarizer = SummarizerAgent(client, mem_client, agent=agent)
    summarizer = None
    executor = AgentExecutor(client, mem_client, p_mcp, tools, agent=agent)
    am = AgentAM(client, mem_client, executor, summarizer, agent=agent)

    # 6) normal flow
    agent.write_log("将 user_input 发送给 AgentAM", level="INFO")
    res = am.run(user_input, user_id=user_id)
    out = res.get("am_result") if isinstance(res, dict) else str(res)

    # append_message(user_id, "am", "user", user_input)
    # agent.write_log("user_input 已持久化到 messages", level="DEBUG")

    agent.send_output(agent_output_name="am_result", agent_result=out)
    agent.write_log("会话完成并将 am_result 发送回 caller", level="INFO")

def main():
    agent = MofaAgent(agent_name="pc-helper")
    run(agent=agent)

if __name__ == "__main__":
    main()
