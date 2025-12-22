"""User tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import UserResult


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def register_user_tools(mcp: FastMCP) -> None:
    """Register all user-related tools."""
    
    @mcp.tool()
    async def get_users(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of users"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)")
    ) -> List[UserResult]:
        """Get a paginated list of users."""
        client = _require_client()
            
        result = await client.get_users(limit=limit, page=page)
        return [UserResult(**item) for item in result]

    @mcp.tool()
    async def get_user_by_id(
        user_id: int = Field(..., description="User ID")
    ) -> UserResult:
        """Get details of a specific user."""
        client = _require_client()
            
        result = await client.get_user_by_id(user_id)
        return UserResult(**result)

    @mcp.tool()
    async def create_user(
        login: str = Field(..., description="User login"),
        lastname: str = Field(..., description="Last name"),
        firstname: Optional[str] = Field(None, description="First name"),
        email: Optional[str] = Field(None, description="Email address"),
        password: Optional[str] = Field(None, description="Password"),
        admin: int = Field(0, description="Admin level (0=No, 1=Yes)")
    ) -> int:
        """Create a new user. Returns the new user ID."""
        client = _require_client()
            
        payload = {
            "login": login,
            "lastname": lastname,
            "admin": admin,
            "statut": 1  # Active by default
        }
        if firstname:
            payload["firstname"] = firstname
        if email:
            payload["email"] = email
        if password:
            payload["password"] = password
                
        return await client.create_user(payload)

    @mcp.tool()
    async def update_user(
        user_id: int = Field(..., description="User ID to update"),
        login: Optional[str] = Field(None, description="User login"),
        lastname: Optional[str] = Field(None, description="Last name"),
        firstname: Optional[str] = Field(None, description="First name"),
        email: Optional[str] = Field(None, description="Email address"),
        admin: Optional[int] = Field(None, description="Admin level (0=No, 1=Yes)")
    ) -> int:
        """Update an existing user."""
        client = _require_client()
            
        payload = {}
        if login:
            payload["login"] = login
        if lastname:
            payload["lastname"] = lastname
        if firstname:
            payload["firstname"] = firstname
        if email:
            payload["email"] = email
        if admin is not None:
            payload["admin"] = admin
                
        if not payload:
            return user_id
                
        return await client.update_user(user_id, payload)

    @mcp.tool()
    async def delete_user(
        user_id: int = Field(..., description="User ID to delete")
    ) -> int:
        """Delete a user."""
        client = _require_client()
            
        return await client.delete_user(user_id)
