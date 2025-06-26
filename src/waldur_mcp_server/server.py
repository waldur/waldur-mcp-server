import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from waldur_api_client.api.customers import customers_list
from waldur_api_client.api.invoices import invoices_list
from waldur_api_client.api.marketplace_public_offerings import (
    marketplace_public_offerings_list,
)
from waldur_api_client.api.marketplace_resources import marketplace_resources_list
from waldur_api_client.api.projects import projects_list
from waldur_api_client.api.query import query as api_query
from waldur_api_client.api.roles import roles_list
from waldur_api_client.api.user_invitations import user_invitations_create
from waldur_api_client.client import AuthenticatedClient
from waldur_api_client.models.invitation import Invitation
from waldur_api_client.models.public_offering_details import PublicOfferingDetails
from waldur_api_client.models.invitation_request import InvitationRequest
from waldur_api_client.models.customer import Customer
from waldur_api_client.models.invoice import Invoice
from waldur_api_client.models.resource import Resource
from waldur_api_client.models.project import Project
from waldur_api_client.models.query_request import QueryRequest

# Get credentials from environment variables
api_url = os.getenv("WALDUR_API_URL")
token = os.getenv("WALDUR_TOKEN")

if not api_url or not token:
    raise ValueError(
        "WALDUR_API_URL and WALDUR_TOKEN environment variables must be set"
    )

client = AuthenticatedClient(base_url=api_url, token=token)

# Create an MCP server
mcp = FastMCP("Waldur", dependencies=["httpx"])


@mcp.resource("schema://main")
async def get_schema() -> list[str]:
    """Provide the database schema as a resource"""
    result = await api_query.asyncio(
        client=client,
        body=QueryRequest(
            query="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ),
    )
    if isinstance(result, list):
        return [row[0] for row in result]
    return []


@mcp.tool()
async def query(sql: str) -> list[Any]:
    """Run a read-only SQL query"""
    return await api_query.asyncio(client=client, body=QueryRequest(query=sql))


@mcp.prompt()
async def schema_aware_query() -> str:
    with open(os.path.join(os.path.dirname(__file__), "meta.yaml")) as f:
        schema = f.read()
        return f"Given the following PostgreSQL database structure:\n {schema}\n compose SQL query for the following analytical query:\n"


@mcp.tool()
async def list_customers() -> list[Customer]:
    """List all customers"""
    return await customers_list.asyncio(client=client)


@mcp.tool()
async def list_projects() -> list[Project]:
    """List all projects"""
    return await projects_list.asyncio(client=client)


@mcp.tool()
async def list_resources() -> list[Resource]:
    """List all resources"""
    return await marketplace_resources_list.asyncio(client=client)


@mcp.tool()
async def list_invoices() -> list[Invoice]:
    """List all invoices"""
    return await invoices_list.asyncio(client=client)


@mcp.tool()
async def list_offerings() -> list[PublicOfferingDetails]:
    """List all offerings"""
    return await marketplace_public_offerings_list.asyncio(client=client)


@mcp.tool()
async def create_invitation(
    scope_type: Literal["customer", "project"],
    scope_name: str,
    role: str,
    emails: list[str],
    extra_invitation_text: str = "",
) -> list[Invitation]:
    """Invite users to project or organization by email

    Args:
        scope_type: Whether to invite users to organization or project
        scope_name: Name of the organization or project to invite users to
        role: Role to assign to invited users
        emails: List of email addresses to invite
        extra_invitation_text: Custom message to include in the invitation
    """

    matching_roles = await roles_list.asyncio(client=client, description=role)
    if not matching_roles:
        raise ValueError(f"Role '{role}' not found")
    role_uuid = matching_roles[0]["uuid"]

    if scope_type == "customer":
        matching_customers = await customers_list.asyncio(
            client=client, name=scope_name
        )
        if not matching_customers:
            raise ValueError(f"Customer '{scope_name}' not found")
        scope_url = matching_customers[0]["url"]
    elif scope_type == "project":
        matching_projects = await projects_list.asyncio(client=client, name=scope_name)
        if not matching_projects:
            raise ValueError(f"Project '{scope_name}' not found")
        scope_url = matching_projects[0]["url"]

    if not scope_url:
        raise ValueError(f"Invalid scope type: {scope_type}")

    results = []
    for email in emails:
        result = await user_invitations_create.asyncio(
            client=client,
            body=InvitationRequest(
                scope=scope_url,
                role=role_uuid,
                email=email,
                extra_invitation_text=extra_invitation_text,
            ),
        )
        results.append(result)

    return results


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
