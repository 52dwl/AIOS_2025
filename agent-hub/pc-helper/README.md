# PC Helper Agent

A comprehensive PC Helper Agent built on the MOFA framework. This agent provides intelligent task assistance by analyzing user requests, leveraging memory capabilities, and executing appropriate tools through the MCP service.

## Features

- **Agent Manager (AM)**: Analyzes user intentions, clarifies requirements, and manages task execution flow
- **Agent Executor**: Processes clarified user intentions and executes appropriate tools
- **Memory Management**: Uses mem0 for persistent memory storage and retrieval of user interactions
- **MCP Integration**: Connects to the MCP (Model Control Plane) service to access various tools
- **Message Persistence**: Stores conversation history for context preservation
- **Summarization**: Summarizes task outcomes and stores them as experiences
- **MOFA Framework Integration**: Built using the standard MOFA agent pattern

## Installation

Install the package in development mode:

```bash
pip install -e .
```

## Configuration

The PC Helper Agent uses multiple configuration files located in the `helper/config` directory:

- `agent_am.yml`: Configuration for the Agent Manager component
- `agent_executor.yml`: Configuration for the Agent Executor component
- `memory_config.yml`: Configuration for the memory management system

These files define prompts, behaviors, and settings for each component.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_input` | string | Yes | The user's request or query to be processed by the agent

### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `am_result` | string | The processed result of the user's request

## Usage Example

### Basic Dataflow Configuration

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

### Running the Agent

1. **Start the MOFA framework:**
   ```bash
   dora up
   ```

2. **Ensure MCP service is running:**
   The PC Helper Agent requires the MCP service to be available at the configured URL.

3. **Build and start the dataflow:**
   ```bash
   dora build pc_helper_dataflow.yml
   dora start pc_helper_dataflow.yml
   ```

4. **Send input data:**
   Use terminal-input or any MOFA input method to send user requests to the `user_input` parameter.

## Code Example

The core functionality is implemented in `helper/main.py`:

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

    # Create OpenAI client
    client = create_openai_client()
    
    # Initialize memory client
    mem_client = Mem0Client()
    # ... memory initialization code ...

    # Initialize MCP client for tool access
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/sse")
    p_mcp = PersistentMCPClient(url=mcp_url, agent=agent)
    # ... MCP client initialization ...

    # Initialize agent components
    tools = p_mcp.list_tools()
    executor = AgentExecutor(client, mem_client, p_mcp, tools, agent=agent)
    am = AgentAM(client, mem_client, executor, None, agent=agent)

    # Process user input and return result
    res = am.run(user_input, user_id=user_id)
    out = res.get("am_result") if isinstance(res, dict) else str(res)
    
    agent.send_output(agent_output_name="am_result", agent_result=out)

def main():
    agent = MofaAgent(agent_name="pc-helper")
    run(agent=agent)

if __name__ == "__main__":
    main()
```


## Dependencies

- **mofa**: MOFA framework (core framework for agent development)
- **mem0**: For persistent memory storage and retrieval
- **mcp**: Model Control Plane client for accessing tools
- **openai**: For language model API access
- **pyarrow**: For data serialization and arrow format support

## Use Cases

- **Personal Assistant**: Provide intelligent assistance for various PC-related tasks
- **Tool Integration**: Serve as a bridge between users and various tools available through MCP
- **Memory-Enabled Tasks**: Perform tasks with context awareness using persistent memory
- **Task Orchestration**: Manage and execute multi-step tasks based on user requests
- **Framework Example**: Demonstrate advanced agent architecture using MOFA framework

## Contributing

1. Ensure your code follows the existing style
2. Add tests for new functionality
3. Update documentation as needed
4. Run tests before submitting changes

## License

MIT License - see LICENSE file for details.

## Links

- [MOFA Framework](https://github.com/moxin-org/mofa)
- [MOFA Documentation](https://github.com/moxin-org/mofa/blob/main/README.md)