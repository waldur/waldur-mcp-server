import os
import json
from typing import Any, Sequence, Dict, Optional, List
import httpx

import mcp.types as types
from mcp.server import Server


class WaldurClient:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        response = await self.client.request(method, url, params=params, json=json_data)
        response.raise_for_status()
        return response.json()

    async def list_projects(self, params: Optional[Dict] = None) -> List[Dict]:
        return await self._make_request("GET", "/projects/", params=params)

    async def list_customers(self, params: Optional[Dict] = None) -> List[Dict]:
        return await self._make_request("GET", "/customers/", params=params)

    async def list_marketplace_public_offerings(
        self, params: Optional[Dict] = None
    ) -> List[Dict]:
        return await self._make_request(
            "GET", "/marketplace-public-offerings/", params=params
        )

    async def list_marketplace_resources(self, params) -> List[Dict]:
        return await self._make_request(
            "GET", "/marketplace-resources/", params=params
        )


# Get credentials from environment variables
api_url = os.getenv("WALDUR_API_URL")
token = os.getenv("WALDUR_TOKEN")

if not api_url or not token:
    raise ValueError(
        "WALDUR_API_URL and WALDUR_TOKEN environment variables must be set"
    )

# Initialize Waldur client
client = WaldurClient(api_url, token)

server = Server("waldur_mcp_server")

PAGINATION_SCHEMA = {
    "page": {
        "type": "integer",
        "description": "Page number for pagination",
        "minimum": 1,
    },
    "page_size": {
        "type": "integer",
        "description": "Number of items per page",
        "minimum": 1,
        "maximum": 100,
    },
}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Waldur tools."""
    return [
        types.Tool(
            name="list_projects",
            description="List available Waldur projects with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    **PAGINATION_SCHEMA,
                    "name": {
                        "type": "string",
                        "description": "Filter projects by name",
                    },
                    "customer": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter projects by customer UUIDs",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Filter projects by customer name (case-insensitive, partial match)",
                    },
                    "customer_native_name": {
                        "type": "string",
                        "description": "Filter projects by customer native name (case-insensitive, partial match)",
                    },
                    "customer_abbreviation": {
                        "type": "string",
                        "description": "Filter projects by customer abbreviation (case-insensitive, partial match)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Filter projects by description (case-insensitive, partial match)",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query across multiple fields",
                    },
                },
            },
        ),
        types.Tool(
            name="list_customers",
            description="List available Waldur organizations (customers)",
            inputSchema={
                "type": "object",
                "properties": {
                    **PAGINATION_SCHEMA,
                    "query": {
                        "type": "string",
                        "description": "Search query across multiple fields",
                    },
                    "name": {
                        "type": "string",
                        "description": "Filter by organization name (case-insensitive, partial match)",
                    },
                    "native_name": {
                        "type": "string",
                        "description": "Filter by organization native name (case-insensitive, partial match)",
                    },
                    "abbreviation": {
                        "type": "string",
                        "description": "Filter by organization abbreviation (case-insensitive, partial match)",
                    },
                    "contact_details": {
                        "type": "string",
                        "description": "Filter by contact details (case-insensitive, partial match)",
                    },
                    "organization_group_uuid": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by organization group UUIDs",
                    },
                    "organization_group_name": {
                        "type": "string",
                        "description": "Filter by organization group name (case-insensitive, partial match)",
                    },
                    "organization_group_type_uuid": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by organization group type UUIDs",
                    },
                    "organization_group_type_name": {
                        "type": "string",
                        "description": "Filter by organization group type name (case-insensitive, partial match)",
                    },
                    "registration_code": {
                        "type": "string",
                        "description": "Filter by registration code",
                    },
                    "agreement_number": {
                        "type": "string",
                        "description": "Filter by agreement number",
                    },
                    "backend_id": {
                        "type": "string",
                        "description": "Filter by backend ID",
                    },
                    "archived": {
                        "type": "boolean",
                        "description": "Filter by archived status",
                    },
                },
            },
        ),
        types.Tool(
            name="list_marketplace_offerings",
            description="List available Waldur marketplace offerings",
            inputSchema={
                "type": "object",
                "properties": {
                    **PAGINATION_SCHEMA,
                },
            },
        ),
        types.Tool(
            name="list_marketplace_resources",
            description="List available Waldur marketplace resources",
            inputSchema={
                "type": "object",
                "properties": {
                    **PAGINATION_SCHEMA,
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[types.TextContent]:
    """Handle tool calls for Waldur operations."""
    # Convert the arguments to filter parameters
    filters = {}
    if arguments:
        for key, value in arguments.items():
            if value is not None:  # Only add non-empty values
                filters[key] = value

    if name == "list_projects":
        projects = await client.list_projects(filters)
        formatted_projects = [
            {
                "id": project["uuid"],
                "name": project["name"],
                "type": "project",
                "organization": project["customer_name"],
                "description": project.get("description", ""),
                "created": project.get("created", ""),
                "customer_native_name": project.get("customer_native_name", ""),
                "customer_abbreviation": project.get("customer_abbreviation", ""),
            }
            for project in projects
        ]
        return [types.TextContent(type="text", text=json.dumps(formatted_projects, indent=2))]

    elif name == "list_customers":
        customers = await client.list_customers(filters)
        formatted_customers = [
            {
                "id": customer["uuid"],
                "name": customer["name"],
                "type": "customer",
                "abbreviation": customer.get("abbreviation", "N/A"),
                "native_name": customer.get("native_name", ""),
                "contact_details": customer.get("contact_details", ""),
                "organization_group": customer.get("organization_group_name", ""),
                "organization_group_type": customer.get(
                    "organization_group_type_name", ""
                ),
                "registration_code": customer.get("registration_code", ""),
                "agreement_number": customer.get("agreement_number", ""),
                "backend_id": customer.get("backend_id", ""),
                "archived": customer.get("archived", False),
            }
            for customer in customers
        ]
        return [types.TextContent(type="text", text=json.dumps(formatted_customers, indent=2))]

    elif name == "list_marketplace_offerings":
        offerings = await client.list_marketplace_public_offerings(filters)
        formatted_offerings = [
            {
                "id": offering["uuid"],
                "name": offering["name"],
                "type": "marketplace-offering",
                "category": offering["category_title"],
                "customer": offering["customer_name"],
                "state": offering["state"],
                "offering_type": offering["type"],
            }
            for offering in offerings
        ]
        return [types.TextContent(type="text", text=json.dumps(formatted_offerings, indent=2))]

    elif name == "list_marketplace_resources":
        resources_list = await client.list_marketplace_resources(**filters)
        formatted_resources = [
            {
                "id": resource["uuid"],
                "name": resource["name"],
                "type": "marketplace-resource",
                "offering": resource["offering_name"],
                "project": resource["project_name"],
                "state": resource["state"],
                "plan": resource.get("plan_name", "N/A"),
            }
            for resource in resources_list
        ]
        return [types.TextContent(type="text", text=json.dumps(formatted_resources, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )
