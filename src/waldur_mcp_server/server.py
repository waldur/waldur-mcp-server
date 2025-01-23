import os
from typing import Literal

from mcp.server.fastmcp import FastMCP
import httpx


class WaldurClient:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token

    async def _request(
        self, path: str, method: str = "GET", data: dict = None, params: dict = None
    ) -> dict:
        """Make HTTP request to Waldur API"""
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            url = f"{self.api_url.rstrip('/')}/api/{path.strip('/')}/"
            response = await client.request(method, url, json=data, params=params)
            if response.status_code == 400:
                raise ValueError(response.json())
            response.raise_for_status()
            return response.json()

    async def sql_query(self, query: str) -> dict:
        """Execute SQL query against Waldur API"""
        return await self._request(
            "query",
            "POST",
            {"query": query},
        )

    async def send_invitation(
        self, scope_url: str, role: str, email: str, extra_invitation_text: str | None
    ) -> dict:
        """Send invitation to user via Waldur API."""
        return await self._request(
            "user-invitations",
            "POST",
            {
                "email": email,
                "scope": scope_url,
                "role": role,
                "extra_invitation_text": extra_invitation_text,
            },
        )

    async def list_roles(self, filters: dict = None) -> list[dict]:
        """List roles with optional filters."""
        return await self._request("roles", params=filters)

    async def list_customers(self, filters: dict = None) -> list[dict]:
        """List customers with optional filters."""
        return await self._request("customers", params=filters)

    async def list_projects(self, filters: dict = None) -> list[dict]:
        """List projects with optional filters."""
        return await self._request("projects", params=filters)

    async def list_invoices(self, filters: dict = None) -> list[dict]:
        """List invoices with optional filters."""
        return await self._request("invoices", params=filters)

    async def list_resources(self, filters: dict = None) -> list[dict]:
        """List resources with optional filters."""
        return await self._request("marketplace-resources", params=filters)

    async def list_offerings(self, filters: dict = None) -> list[dict]:
        """List offerings with optional filters."""
        return await self._request("marketplace-offerings", params=filters)


# Get credentials from environment variables
api_url = os.getenv("WALDUR_API_URL")
token = os.getenv("WALDUR_TOKEN")

if not api_url or not token:
    raise ValueError(
        "WALDUR_API_URL and WALDUR_TOKEN environment variables must be set"
    )

client = WaldurClient(api_url, token)

# Create an MCP server
mcp = FastMCP("Waldur", dependencies=["httpx"])


@mcp.resource("schema://main")
async def get_schema() -> list[str]:
    """Provide the database schema as a resource"""
    result = await client.sql_query(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    return [row[0] for row in result]


@mcp.tool()
async def query(sql: str) -> dict:
    """Run a read-only SQL query"""
    return await client.sql_query(sql)


@mcp.tool()
async def list_customers() -> list[dict]:
    """List all customers"""
    return await client.list_customers()


@mcp.tool()
async def list_projects() -> list[dict]:
    """List all projects"""
    return await client.list_projects()


@mcp.tool()
async def list_resources() -> list[dict]:
    """List all resources"""
    return await client.list_resources()


@mcp.tool()
async def list_invoices() -> list[dict]:
    """List all invoices"""
    return await client.list_invoices()


@mcp.tool()
async def list_offerings() -> list[dict]:
    """List all offerings"""
    return await client.list_offerings()


@mcp.tool()
async def create_invitation(
    scope_type: Literal["customer", "project"],
    scope_name: str,
    role: str,
    emails: list[str],
    extra_invitation_text: str = "",
) -> list[dict]:
    """Invite users to project or organization by email

    Args:
        scope_type: Whether to invite users to organization or project
        scope_name: Name of the organization or project to invite users to
        role: Role to assign to invited users
        emails: List of email addresses to invite
        extra_invitation_text: Custom message to include in the invitation
    """

    matching_roles = await client.list_roles({"description": role})
    if not matching_roles:
        raise ValueError(f"Role '{role}' not found")
    role = matching_roles[0]["uuid"]

    if scope_type == "customer":
        matching_customers = await client.list_customers({"name": scope_name})
        if not matching_customers:
            raise ValueError(f"Customer '{scope_name}' not found")
        scope_url = matching_customers[0]["url"]
    elif scope_type == "project":
        matching_projects = await client.list_projects({"name": scope_name})
        if not matching_projects:
            raise ValueError(f"Project '{scope_name}' not found")
        scope_url = matching_projects[0]["url"]

    if not scope_url:
        raise ValueError(f"Invalid scope type: {scope_type}")

    results = []
    for email in emails:
        result = await client.send_invitation(
            scope_url, role, email, extra_invitation_text
        )
        results.append(result)

    return results


def main():
    mcp.run()


if __name__ == "__main__":
    main()
