# helper/mcp_client.py
# Persistent MCP client: runs an asyncio loop in background thread and keeps ClientSession open.
import asyncio
import threading
from typing import Any, Dict, List, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

def convert_tool_format(tool):
    converted_tool = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema["properties"],
                "required": tool.inputSchema["required"]
            }
        }
    }
    return converted_tool

class PersistentMCPClient:
    def __init__(self, url: str = "http://127.0.0.1:8000/sse", agent=None):
        self.url = url
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self._started = threading.Event()
        self._stop = threading.Event()
        self._session = None
        self._streams = None
        self.mofa_agent = agent

    def _log(self, msg: str, level: str = "INFO"):
        if self.mofa_agent:
            try:
                self.mofa_agent.write_log(msg, level=level)
            except Exception:
                pass

    def start(self, timeout: float = 10.0):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._thread_main, daemon=True)
        self.thread.start()
        started = self._started.wait(timeout=timeout)
        if not started:
            self._log("PersistentMCPClient 启动超时", "ERROR")
            raise TimeoutError("启动 PersistentMCPClient 超时")
        self._log("PersistentMCPClient 已启动", "INFO")

    def _thread_main(self):
        async def _init_and_wait():
            async with sse_client(url=self.url) as streams:
                async with ClientSession(*streams) as session:
                    self._streams = streams
                    self._session = session
                    await session.initialize()
                    self._started.set()
                    while not self._stop.is_set():
                        await asyncio.sleep(0.5)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(_init_and_wait())
        finally:
            try:
                self.loop.close()
            except Exception:
                pass

    def stop(self):
        if not self.thread:
            return
        self._stop.set()
        self.thread.join(timeout=5)
        self.thread = None
        self.loop = None
        self._session = None
        self._streams = None
        self._started.clear()
        self._stop.clear()
        self._log("PersistentMCPClient 已停止", "INFO")

    def _run_coroutine(self, coro):
        if not self.loop or not self.thread:
            raise RuntimeError("PersistentMCPClient 未启动，请先调用 start()")
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return fut.result()

    def list_tools(self) -> List[Dict[str, Any]]:
        async def _list():
            if self._session is None:
                await asyncio.sleep(0.1)
            return await self._session.list_tools()
        self._log("列出 MCP tools", "DEBUG")
        tools_Tool = self._run_coroutine(_list())
        tools = [ convert_tool_format(v) for v in tools_Tool.tools]
        return tools

    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        async def _call():
            if self._session is None:
                await asyncio.sleep(0.1)
            return await self._session.call_tool(tool_name, args)
        self._log(f"call_tool: {tool_name}, args={args}", "DEBUG")
        return self._run_coroutine(_call())
