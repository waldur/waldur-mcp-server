import os
import json
from typing import Any, Sequence, Dict, List
import httpx

import mcp.types as types
from mcp.server import Server
from pydantic import AnyUrl


async def execute_waldur_query(api_url: str, token: str, query: str) -> Dict:
    """Execute SQL query against Waldur API"""
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    url = f"{api_url.rstrip('/')}/query/"
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        response = await client.request("POST", url, json={"query": query})
        response.raise_for_status()
        return response.json()


# Get credentials from environment variables
api_url = os.getenv("WALDUR_API_URL")
token = os.getenv("WALDUR_TOKEN")

if not api_url or not token:
    raise ValueError(
        "WALDUR_API_URL and WALDUR_TOKEN environment variables must be set"
    )

server = Server("waldur_mcp_server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Waldur tools."""
    return [
        types.Tool(
            name="query",
            description="Run a read-only SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute (read-only queries only)",
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="project-list",
            description="List all Waldur projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="customer-list",
            description="List all Waldur customers",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="resource-list",
            description="List resources such as instances, volumes, and networks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[types.TextContent]:
    """Handle tool calls for Waldur operations."""
    queries = {
        "query": lambda args: args["sql"] if "sql" in args else None,
        "project-list": lambda _: "SELECT uuid, name, description FROM structure_project",
        "customer-list": lambda _: "SELECT uuid, name, abbreviation FROM structure_customer",
        "resource-list": lambda _: "SELECT uuid, name FROM marketplace_resource",
    }

    if name not in queries:
        raise ValueError(f"Unknown tool: {name}")

    query = queries[name](arguments)
    if query is None:
        raise ValueError("SQL query is required")

    result = await execute_waldur_query(api_url, token, query)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


@server.list_resources()
async def list_resources() -> List[types.Resource]:
    """List available Waldur resources that can be used with Claude."""
    result = await execute_waldur_query(
        api_url,
        token,
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
    )
    return [
        types.Resource(
            uri=f"waldur://{row[0]}",
            name=f"{row[0]} database schema",
            description=f"{row[0]} database schema",
            mimeType="application/json",
        )
        for row in result
    ]


@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    if uri.scheme != "waldur":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    path = str(uri).replace("waldur://", "")
    if not path:
        raise ValueError(f"Unsupported path: {path}")

    result = await execute_waldur_query(
        api_url,
        token,
        f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{path}'",
    )
    return json.dumps(result, indent=2)


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )
