# helper/mem0_client.py
# 使用 mem0 提供的同步接口（Memory.from_config 等）
from typing import Any, Dict, List, Optional
import os

try:
    # 根据 mem0 docs，使用 Memory（同步接口）
    from mem0 import Memory
except Exception:
    Memory = None

class Mem0Client:
    """
    简单同步封装 mem0 Memory。只初始化一次（from_config / from_env 等）。
    请确保你的 memory_config.yml 与 docs 格式一致。
    """

    def __init__(self, config: Optional[Dict] = None):
        if Memory is None:
            raise ImportError("未安装 mem0，请参考 https://docs.mem0.ai 安装")
        self.memory = None
        self.config = config

    def init_from_config(self, config: Dict):
        """
        使用 Memory.from_config(config) 初始化（docs 示例）
        """
        if not config:
            raise ValueError("请提供 mem0 配置")
        # Memory.from_config 一般返回一个 Memory 实例
        self.memory = Memory.from_config(config)
        return self.memory

    def search(self, query: str, user_id: str = "default", limit: int = 5):
        if self.memory is None:
            raise RuntimeError("mem0 未初始化")
        # 使用 memory.search 或 memory.get 类似方法，按 docs 微调
        # docs quickstart shows memory.search(query, user_id=..., limit=...)
        try:
            return self.memory.search(query=query, user_id=user_id, limit=limit)
        except Exception:
            raise

    def add(self, messages: List[Dict[str, str]], user_id: str = "default"):
        if self.memory is None:
            raise RuntimeError("mem0 未初始化")
        # messages is a list of {"role":..., "content":...}
        return self.memory.add(messages, user_id=user_id)
