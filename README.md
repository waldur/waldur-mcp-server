# Waldur MCP server

## Quickstart

1. Install Claude Desktop for your platform from the [Claude Desktop releases page](https://claude.ai/download)

2. Install Python 3.10 or higher.

3. Install uv package manager.

### Claude Desktop MCP Server Configuration

On Windows: `\AppData\Roaming\Claude\claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
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
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
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
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory C:\\waldur_service run waldur-mcp-server
```

When debugging, you'll need to set the required environment variables. Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
