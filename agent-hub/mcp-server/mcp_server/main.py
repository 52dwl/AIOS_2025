from mofa.agent_build.base.base_agent import MofaAgent, run_agent
import time, subprocess, shlex, os
from typing import Dict, Any

default_timeout = 30  # 默认超时秒数

def shell_tool(cmd: str, timeout: int = default_timeout) -> Dict[str, Any]:
    """
    执行系统命令，直接传 cmd 字符串。

    参数:
    - cmd: str，命令字符串，例如 "ls -la /tmp"
    - timeout: int，可选，超时时间（秒）

    返回:
    {
        "success": bool,
        "returncode": int|None,
        "stdout": str,
        "stderr": str,
        "elapsed": float,
        "error": str|None
    }
    """
    start_time = time.time()

    if not cmd or not isinstance(cmd, str):
        return {"success": False, "error": "missing or invalid 'cmd' parameter"}

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            shell=True,
            env=os.environ.copy()
        )
        elapsed = time.time() - start_time
        return {
            "success": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.decode(errors="ignore")[:20000],
            "stderr": completed.stderr.decode(errors="ignore")[:20000],
            "elapsed": elapsed,
            "error": None if completed.returncode == 0 else f"exit code {completed.returncode}"
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return {"success": False, "error": "timeout", "returncode": None, "stdout": "", "stderr": "", "elapsed": elapsed}

    except Exception as e:
        elapsed = time.time() - start_time
        return {"success": False, "error": str(e), "returncode": None, "stdout": "", "stderr": "", "elapsed": elapsed}




@run_agent
def run(agent):
    agent.register_mcp_tool(shell_tool)
    print('开始运行mcp服务')
    agent.run_mcp()

def main():
    agent_name = 'Mofa-Mcp'
    agent = MofaAgent(agent_name=agent_name)
    run(agent)

if __name__ == "__main__":
    main()
