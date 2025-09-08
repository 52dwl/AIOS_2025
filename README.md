# 本项目为第三届MoFA超级智能体Campathon参赛项目

## 项目介绍

本项目为第三届MoFA超级智能体Campathon参赛项目，项目名称为“电脑端文件数据助手”。

当前为MVP实现，已实现功能：
1. 接收用户模糊指令，向用户澄清指令详情
2. 将澄清后的指令交付给执行层，执行层调用mcp工具完成任务
3. mcp工具已实现：执行系统命令

## 项目架构

本项目有两个Agent，分别是：
- 客户经理Agent：负责接收用户指令，向用户澄清指令详情，将澄清后的指令交付给执行层
- 执行层Agent：负责接收客户经理Agent交付的指令，调用mcp工具完成任务

上下文管理：当前采用简单的上下文管理，每个Agent都有自己的上下文，上下文包含用户指令和Agent的回复。使用json文件保存Agent上下文。

记忆功能：当前采用mem0管理记忆，但是由于速度原因，当前版本未启用记忆功能。

## 项目运行

1. 安装mofa

2. 安装依赖
   ```bash
   pip install ollama
   ```

3. `env`配置

   路径：`AIOS_2025/examples/pc-helper/.env`
   内容：
   ```
   LLM_API_KEY=sk-xxx
   OPENAI_API_KEY=sk-xxx   # 若你更习惯这个变量名
   LLM_BASE_URL=https://api.deepseek.com
   MCP_URL=http://127.0.0.1:8000/sse
   ENV_FILE=.env
   USER_ID=pc-helper
   LLM_MODEL_AM=deepseek-chat
   LLM_MODEL_EXECUTOR=deepseek-chat
   LLM_MODEL_SUM=deepseek-chat
   MEMORY_LIMIT=5
   ```

4. 运行项目
   ```bash
   dora up
   cd AIOS_2025/examples/pc-helper
   dora build pc_helper_dataflow.yml
   dora start pc_helper_dataflow.yml
   ```

   建议关闭mem功能，因为当前版本mem0无效，且首次启动会拉取ollama的向量模型，耗时很久。
   关闭方式：将 `AIOS_2025/agent-hub/pc-helper/helper/main.py` 中的以下代码注释掉：
   ```python
   mem_client.init_from_config(mem_conf)
   ```

   运行mcp服务器
   ```bash
   cd AIOS_2025/examples/mcp-server
   dora build mcp_server.yml
   dora start mcp_server.yml
   ```

   启动terminal-input节点
   ```bash
   terminal-input
   ```

5. 日志查看
   路径：
    - `AIOS_2025/examples/pc-helper/logs/`

## TODO
1. 优化上下文管理
3. 前端界面
   - 使用moly替代terminal-input，将运行细节展示出来，而不是放到日志里
4. MCP工具开发
    - 文件内容读写
    - 数据处理Agent（作为MCP工具供执行层调用）
    - 代码编写Agent（作为MCP工具供执行层调用，简易版）
5. 数据流打断（中断）
   - 为数据流提供中断处理
6. 预制解决方案
   - 为客户经理Agent提供预制的解决方案，减少用户等待时间