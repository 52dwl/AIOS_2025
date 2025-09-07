# Hello World 节点

一个简单的 MOFA 节点，演示基本的回声/透传功能。该节点接收输入数据并原样返回，作为 MOFA 框架的模板和测试工具。

## 功能特性

- **回声功能**：原样返回输入数据
- **MOFA 框架集成**：使用标准 MOFA 代理模式构建
- **简单测试**：非常适合验证 MOFA 框架设置和数据流连接
- **最小依赖**：轻量级实现，外部依赖最少

## 安装

以开发模式安装包：

```bash
pip install -e .
```

## 配置

该节点不需要额外的配置文件。它使用标准的 MOFA 代理配置模式。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| `query` | string | 是 | 要回传的输入数据 |

### 输出参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| `hello_world_result` | string | 原样返回的输入数据 |

## 使用示例

### 基本数据流配置

```yaml
# hello_world_dataflow.yml
nodes:
  - id: terminal-input
    build: pip install -e ../../node-hub/terminal-input
    path: dynamic
    outputs:
      - data
    inputs:
      agent_response: life-helper-am-agent/hello_world_result
  - id: life-helper-am-agent
    build: pip install -e ../../agent-hub/life-helper-am
    path: life-helper-am
    outputs:
      - hello_world_result
    inputs:
      query: terminal-input/data
    env:
      IS_DATAFLOW_END: true
      WRITE_LOG: true
```

### 运行节点

1. **启动 MOFA 框架：**
   ```bash
   dora up
   ```

2. **构建并启动数据流：**
   ```bash
   dora build hello_world_dataflow.yml
   dora start hello_world_dataflow.yml
   ```

3. **发送输入数据：**
   使用 terminal-input 或任何 MOFA 输入方法向 `query` 参数发送数据。

## 代码示例

核心功能在 `main.py` 中实现：

```python
from mofa.agent_build.base.base_agent import MofaAgent, run_agent

@run_agent
def run(agent: MofaAgent):
    # 接收输入参数
    user_query = agent.receive_parameter('query')
    
    # 发送输出（原样回传输入）
    agent.send_output(
        agent_output_name='hello_world_result', 
        agent_result=user_query
    )

def main():
    agent = MofaAgent(agent_name='life-helper-am')
    run(agent=agent)

if __name__ == "__main__":
    main()
```

## 依赖项

- **pyarrow** (>= 5.0.0)：用于数据序列化和 arrow 格式支持
- **mofa**：MOFA 框架（在 MOFA 环境中自动可用）

## 使用场景

- **框架测试**：验证 MOFA 设置和数据流连接
- **模板参考**：作为新 MOFA 节点的起点
- **调试工具**：在复杂管道中测试数据流和参数传递
- **学习工具**：理解基本的 MOFA 节点结构和模式

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