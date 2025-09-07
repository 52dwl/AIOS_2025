# Hello World Node

A simple MOFA node that demonstrates the basic echo/passthrough functionality. This node receives input and returns it unchanged, serving as a template and testing utility for the MOFA framework.

## Features

- **Echo Functionality**: Returns input data unchanged
- **MOFA Framework Integration**: Built using the standard MOFA agent pattern
- **Simple Testing**: Ideal for verifying MOFA framework setup and dataflow connectivity
- **Minimal Dependencies**: Lightweight implementation with minimal external dependencies

## Installation

Install the package in development mode:

```bash
pip install -e .
```

## Configuration

This node requires no additional configuration files. It uses the standard MOFA agent configuration pattern.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The input data to be echoed back |

### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `hello_world_result` | string | The echoed input data unchanged |

## Usage Example

### Basic Dataflow Configuration

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

### Running the Node

1. **Start the MOFA framework:**
   ```bash
   dora up
   ```

2. **Build and start the dataflow:**
   ```bash
   dora build hello_world_dataflow.yml
   dora start hello_world_dataflow.yml
   ```

3. **Send input data:**
   Use terminal-input or any MOFA input method to send data to the `query` parameter.

## Code Example

The core functionality is implemented in `main.py`:

```python
from mofa.agent_build.base.base_agent import MofaAgent, run_agent

@run_agent
def run(agent: MofaAgent):
    # Receive input parameter
    user_query = agent.receive_parameter('query')
    
    # Send output (echo the input unchanged)
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


## Dependencies

- **pyarrow** (>= 5.0.0): For data serialization and arrow format support
- **mofa**: MOFA framework (automatically available in MOFA environment)

## Use Cases

- **Framework Testing**: Verify MOFA setup and dataflow connectivity
- **Template Reference**: Use as a starting point for new MOFA nodes
- **Debugging**: Test data flow and parameter passing in complex pipelines
- **Learning**: Understand basic MOFA node structure and patterns

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