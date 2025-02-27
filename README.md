# Waldur MCP server

## Quickstart

1. Install Claude Desktop for your platform from the [Claude Desktop releases page](https://claude.ai/download)

2. Install Python 3.10 or higher.

3. Install uv package manager.

### Installation

To install the package:

```bash
pip install waldur-mcp-server
```

Or with uv:

```bash
uv pip install waldur-mcp-server
```

### Claude Desktop MCP Server Configuration

On Windows: `\AppData\Roaming\Claude\claude_desktop_config.json`

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>

```json
{
  "mcpServers": {
    "waldur-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\waldur_service",
        "run",
        "waldur-mcp-server"
      ],
      "env": {
        "WALDUR_API_URL": "https://your-waldur-instance/api",
        "WALDUR_TOKEN": "your-token"
      }
    }
  }
}
```

</details>

<details>
  <summary>Published Servers Configuration</summary>

```json
{
  "mcpServers": {
    "waldur-mcp-server": {
      "command": "uvx",
      "args": [
        "waldur-mcp-server"
      ],
      "env": {
        "WALDUR_API_URL": "https://your-waldur-instance/api",
        "WALDUR_TOKEN": "your-token"
      }
    }
  }
}
```

</details>

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory C:\\waldur_service run waldur-mcp-server
```

When debugging, you'll need to set the required environment variables. Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Development

For information about development and releasing new versions, see [RELEASING.md](RELEASING.md).
