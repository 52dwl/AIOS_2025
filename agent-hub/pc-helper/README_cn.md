# 电脑端文件数据助手

一个基于 MOFA 框架构建的综合性 PC 助手代理。该代理通过分析用户请求、利用内存功能以及通过 MCP 服务执行适当的工具来提供智能任务辅助。

## 功能特性

- **客户经理Agent（AM）**：分析用户意图，澄清需求，并管理任务执行流程
- **执行层Agent**：处理澄清后的用户意图并执行适当的工具
- **经验管理**：使用 mem0 进行持久化内存存储和用户交互检索
- **MCP 集成**：连接到 MCP（模型控制平面）服务以访问各种工具
- **消息持久化**：存储对话历史以保留上下文
- **摘要功能**：总结任务结果并将其存储为经验
- **MOFA 框架集成**：使用标准 MOFA 代理模式构建

## 安装

以开发模式安装包：

```bash
pip install -e .
```

## 配置

PC Helper 代理使用位于 `helper/config` 目录中的多个配置文件：

- `agent_am.yml`：代理管理器组件的配置
- `agent_executor.yml`：代理执行器组件的配置
- `memory_config.yml`：内存管理系统的配置

这些文件定义了每个组件的提示词、行为和设置。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| `user_input` | string | 是 | 由代理处理的用户请求或查询

### 输出参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| `am_result` | string | 用户请求的处理结果

## 使用示例

### 基本数据流配置

```yaml
# pc_helper_dataflow.yml
nodes:
  - id: terminal-input
    build: pip install -e ../../node-hub/terminal-input
    path: dynamic
    outputs:
      - data
    inputs:
      agent_response: pc-helper/am_result
  - id: pc-helper
    build: pip install -e .
    path: helper
    outputs:
      - am_result
    inputs:
      user_input: terminal-input/data
    env:
      IS_DATAFLOW_END: true
      WRITE_LOG: true
      LLM_API_KEY: your_api_key_here
      MCP_URL: http://127.0.0.1:8000/sse
      USER_ID: default_user
```

### 运行代理

1. **启动 MOFA 框架：**
   ```bash
   dora up
   ```

2. **确保 MCP 服务正在运行：**
   PC Helper 代理需要 MCP 服务在配置的 URL 上可用。

3. **构建并启动数据流：**
   ```bash
   dora build pc_helper_dataflow.yml
   dora start pc_helper_dataflow.yml
   ```

4. **发送输入数据：**
   使用 terminal-input 或任何 MOFA 输入方法向 `user_input` 参数发送用户请求。

## 代码示例

核心功能在 `helper/main.py` 中实现：

```python
import os
from mofa.agent_build.base.base_agent import run_agent, MofaAgent
from .utils import create_openai_client
from .mcp_client import PersistentMCPClient
from .mem0_client import Mem0Client
from .agent_executor import AgentExecutor
from .agent_am import AgentAM

@run_agent
def run(agent: MofaAgent):
    user_input = agent.receive_parameter("user_input") or ""
    if user_input.strip() == "":
        return
    user_id = os.getenv("USER_ID", "pc-helper")

    # 创建 OpenAI 客户端
    client = create_openai_client()
    
    # 初始化内存客户端
    mem_client = Mem0Client()
    # ... 内存初始化代码 ...

    # 初始化 MCP 客户端以访问工具
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/sse")
    p_mcp = PersistentMCPClient(url=mcp_url, agent=agent)
    # ... MCP 客户端初始化 ...

    # 初始化代理组件
    tools = p_mcp.list_tools()
    executor = AgentExecutor(client, mem_client, p_mcp, tools, agent=agent)
    am = AgentAM(client, mem_client, executor, None, agent=agent)

    # 处理用户输入并返回结果
    res = am.run(user_input, user_id=user_id)
    out = res.get("am_result") if isinstance(res, dict) else str(res)
    
    agent.send_output(agent_output_name="am_result", agent_result=out)

def main():
    agent = MofaAgent(agent_name="pc-helper")
    run(agent=agent)

if __name__ == "__main__":
    main()
```

## 依赖项

- **mofa**：MOFA 框架（代理开发的核心框架）
- **mem0**：用于持久化内存存储和检索
- **mcp**：模型控制平面客户端，用于访问工具
- **openai**：用于语言模型 API 访问
- **pyarrow**：用于数据序列化和 arrow 格式支持

## 使用场景

- **个人助手**：为各种 PC 相关任务提供智能辅助
- **工具集成**：作为用户和通过 MCP 可用的各种工具之间的桥梁
- **内存增强任务**：使用持久化内存执行具有上下文感知的任务
- **任务编排**：基于用户请求管理和执行多步骤任务
- **框架示例**：展示使用 MOFA 框架的高级代理架构

## 贡献

1. 确保您的代码遵循现有风格
2. 为新功能添加测试
3. 根据需要更新文档
4. 提交更改前运行测试

## 许可证

MIT 许可证 - 详见 LICENSE 文件。

## 链接

- [MOFA 框架](https://github.com/moxin-org/mofa)
- [MOFA 文档](https://github.com/moxin-org/mofa/blob/main/README.md)