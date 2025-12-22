"""FastMCP Server implementation for Dolibarr MCP."""

import sys
import re
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from pydantic import Field

from .config import Config
from .dolibarr_client import DolibarrClient, DolibarrAPIError
from .models import (
    ProjectSearchResult,
    CustomerResult,
    InvoiceResult,
    InvoiceLine,
    ProductResult,
    UserResult,
    ContactResult,
    OrderResult
)


# Global client instance
client: Optional[DolibarrClient] = None


def _require_client() -> DolibarrClient:
    """Ensure client is initialized and return it."""
    if not client:
        raise RuntimeError("Server not initialized")
    return client


def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection and other issues."""
    s = s.strip()
    # Allow alphanumeric, spaces, and common safe characters including +, &, ,, (), #
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]



@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Manage server lifecycle and API client session."""
    global client
    
    # Load configuration
    try:
        config = Config()
        
        # Check if environment variables are set properly
        if not config.dolibarr_url or "your-dolibarr-instance" in config.dolibarr_url:
            raise RuntimeError("DOLIBARR_URL not configured properly")
        
        if not config.api_key or "your_dolibarr_api_key" in config.api_key:
            raise RuntimeError("DOLIBARR_API_KEY not configured properly")
            
        # Initialize client
        client = DolibarrClient(config)
        await client.start_session()
        
        # Test connection
        try:
            status = await client.get_status()
            version = status.get("dolibarr_version", "Unknown")
            print(f"✅ Connected to Dolibarr API (Version: {version})", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Connection test failed: {e}", file=sys.stderr)
            
        yield
        
    finally:
        # Cleanup
        if client:
            try:
                await client.close_session()
                print("👋 Dolibarr client session closed", file=sys.stderr)
            finally:
                client = None


# Initialize FastMCP server
mcp = FastMCP(
    "dolibarr-mcp",
    dependencies=["aiohttp", "pydantic"],
    instructions="Professional Dolibarr ERP/CRM integration via Model Context Protocol",
    lifespan=server_lifespan
)


# ============================================================================
# PROJECT TOOLS
# ============================================================================

@mcp.tool()
async def search_projects(
    query: Optional[str] = Field(None, description="Search term for project ref or title"),
    filter_customer_id: Optional[int] = Field(None, description="Filter by customer ID (socid)"),
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
) -> List[ProjectSearchResult]:
    """Search projects by reference, title, or customer.
    
    Use filter_customer_id to find all projects of a specific customer.
    Can combine both query and filter_customer_id.
    """
    client = _require_client()

    filters = []
    
    if query:
        query_sanitized = _sanitize_search(query)
        filters.append(f"((t.ref:like:'%{query_sanitized}%') or (t.title:like:'%{query_sanitized}%'))")
    
    if filter_customer_id:
        filters.append(f"(t.socid:{filter_customer_id})")
    
    sqlfilters = " and ".join(filters) if filters else ""
    
    try:
        result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
        # Filter out items that don't match the model (e.g. missing required fields)
        # or let Pydantic handle validation errors
        return [ProjectSearchResult(**item) for item in result]
    except DolibarrAPIError as e:
        # FastMCP handles exceptions, but we can provide cleaner messages
        raise RuntimeError(f"Dolibarr API Error: {e.message}")




@mcp.tool()
async def get_projects(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of projects"),
    page: int = Field(0, ge=0, description="Page number (starts at 0)"),
    status: Optional[int] = Field(None, description="Project status filter")
) -> List[ProjectSearchResult]:
    """Get a paginated list of projects."""
    client = _require_client()
        
    result = await client.get_projects(limit=limit, page=page, status=status)
    return [ProjectSearchResult(**item) for item in result]


@mcp.tool()
async def get_project_by_id(
    project_id: int = Field(..., description="Exact numeric Dolibarr project ID")
) -> ProjectSearchResult:
    """Get details of a specific project."""
    client = _require_client()
        
    result = await client.get_project_by_id(project_id)
    return ProjectSearchResult(**result)


@mcp.tool()
async def create_project(
    title: str = Field(..., description="Project title"),
    ref: Optional[str] = Field(None, description="Project reference (auto-generated if empty)"),
    socid: Optional[int] = Field(None, description="Customer ID"),
    description: Optional[str] = Field(None, description="Project description"),
    status: int = Field(1, description="Initial status (0=Draft, 1=Open)")
) -> int:
    """Create a new project. Returns the new project ID."""
    client = _require_client()
        
    payload = {
        "title": title,
        "status": status
    }
    if ref:
        payload["ref"] = ref
    if socid:
        payload["socid"] = socid
    if description:
        payload["description"] = description
        
    return await client.create_project(payload)



# ============================================================================
# USER TOOLS
# ============================================================================

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



# ============================================================================
# CUSTOMER TOOLS
# ============================================================================

@mcp.tool()
async def get_customers(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of customers"),
    page: int = Field(0, ge=0, description="Page number (starts at 0)")
) -> List[CustomerResult]:
    """Get a paginated list of customers/third parties."""
    client = _require_client()
        
    result = await client.get_customers(limit=limit, page=page)
    return [CustomerResult(**item) for item in result]


@mcp.tool()
async def search_customers(
    query: str = Field(..., description="Search term for name or alias"),
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
) -> List[CustomerResult]:
    """Search customers by name or alias."""
    client = _require_client()
        
    query_sanitized = _sanitize_search(query)
    sqlfilters = f"((t.nom:like:'%{query_sanitized}%') or (t.name_alias:like:'%{query_sanitized}%'))"
    
    try:
        result = await client.search_customers(sqlfilters=sqlfilters, limit=limit)
        return [CustomerResult(**item) for item in result]
    except DolibarrAPIError as e:
        raise RuntimeError(f"Dolibarr API Error: {e.message}")


@mcp.tool()
async def get_customer_by_id(
    customer_id: int = Field(..., description="Customer ID")
) -> CustomerResult:
    """Get details of a specific customer."""
    client = _require_client()
        
    result = await client.get_customer_by_id(customer_id)
    return CustomerResult(**result)



@mcp.tool()
async def create_customer(
    name: str = Field(..., description="Customer name"),
    client_type: int = Field(1, description="Client type (1=Customer, 2=Prospect, 3=Both)"),
    email: Optional[str] = Field(None, description="Email address"),
    phone: Optional[str] = Field(None, description="Phone number"),
    address: Optional[str] = Field(None, description="Address"),
    town: Optional[str] = Field(None, description="City/Town"),
    zip_code: Optional[str] = Field(None, description="Postal code"),
    country_id: int = Field(1, description="Country ID (default: 1)")
) -> int:
    """Create a new customer/third party."""
    client = _require_client()
        
    payload = {
        "name": name,
        "client": client_type,
        "code_client": -1,  # Auto-generate code
        "country_id": country_id
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if address:
        payload["address"] = address
    if town:
        payload["town"] = town
    if zip_code:
        payload["zip"] = zip_code
        
    return await client.create_customer(payload)



@mcp.tool()
async def update_customer(
    customer_id: int = Field(..., description="Customer ID to update"),
    name: Optional[str] = Field(None, description="Customer name"),
    email: Optional[str] = Field(None, description="Email address"),
    phone: Optional[str] = Field(None, description="Phone number"),
    address: Optional[str] = Field(None, description="Address"),
    town: Optional[str] = Field(None, description="City/Town"),
    zip_code: Optional[str] = Field(None, description="Postal code")
) -> int:
    """Update an existing customer."""
    client = _require_client()
        
    payload = {}
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if address:
        payload["address"] = address
    if town:
        payload["town"] = town
    if zip_code:
        payload["zip"] = zip_code
        
    if not payload:
        return customer_id
        
    return await client.update_customer(customer_id, payload)



# ============================================================================
# CONTACT TOOLS
# ============================================================================

@mcp.tool()
async def get_contacts(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of contacts"),
    page: int = Field(0, ge=0, description="Page number (starts at 0)"),
    customer_id: Optional[int] = Field(None, description="Filter by customer ID (socid)")
) -> List[ContactResult]:
    """Get a paginated list of contacts."""
    client = _require_client()
        
    sqlfilters = None
    if customer_id:
        sqlfilters = f"(t.socid:eq:{customer_id})"
        
    result = await client.get_contacts(limit=limit, page=page, sqlfilters=sqlfilters)
    return [ContactResult(**item) for item in result]


@mcp.tool()
async def create_contact(
    lastname: str = Field(..., description="Last name"),
    firstname: str = Field(..., description="First name"),
    socid: int = Field(..., description="Associated customer ID"),
    email: Optional[str] = Field(None, description="Email address"),
    phone_pro: Optional[str] = Field(None, description="Professional phone"),
    poste: Optional[str] = Field(None, description="Job position")
) -> int:
    """Create a new contact."""
    client = _require_client()
        
    payload = {
        "lastname": lastname,
        "firstname": firstname,
        "socid": socid
    }
    if email:
        payload["email"] = email
    if phone_pro:
        payload["phone_pro"] = phone_pro
    if poste:
        payload["poste"] = poste
        
    return await client.create_contact(payload)



# ============================================================================
# INVOICE TOOLS
# ============================================================================

@mcp.tool()
async def create_invoice(
    customer_id: int = Field(..., description="Customer ID (socid)"),
    date: str = Field(..., description="Invoice date (YYYY-MM-DD)"),
    lines: List[InvoiceLine] = Field(..., description="Invoice lines"),
    project_id: Optional[int] = Field(None, description="Project ID"),
    payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
) -> int:
    """Create a new invoice (draft). Returns the new invoice ID."""
    client = _require_client()
        
    # Convert Pydantic models to dicts
    lines_data = [line.model_dump(exclude_none=True) for line in lines]
    
    payload = {
        "socid": customer_id,
        "date": date,
        "lines": lines_data,
        "type": 0,  # Standard invoice
        "statut": 0  # Draft
    }
    
    if project_id:
        payload["fk_project"] = project_id
    if payment_mode_id:
        payload["mode_reglement_id"] = payment_mode_id
        
    return await client.create_invoice(payload)


@mcp.tool()
async def get_invoices(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of invoices"),
    status: Optional[str] = Field(None, description="Filter by status (draft, unpaid, paid)")
) -> List[InvoiceResult]:
    """Get a list of invoices."""
    client = _require_client()
        
    result = await client.get_invoices(limit=limit, status=status)
    return [InvoiceResult(**item) for item in result]



@mcp.tool()
async def get_invoice_by_id(
    invoice_id: int = Field(..., description="Invoice ID")
) -> InvoiceResult:
    """Get details of a specific invoice."""
    client = _require_client()
        
    result = await client.get_invoice_by_id(invoice_id)
    return InvoiceResult(**result)


@mcp.tool()
async def update_invoice(
    invoice_id: int = Field(..., description="Invoice ID to update"),
    date: Optional[str] = Field(None, description="Invoice date (YYYY-MM-DD)"),
    payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
) -> int:
    """Update an existing invoice (draft only)."""
    client = _require_client()
        
    payload = {}
    if date:
        payload["date"] = date
    if payment_mode_id:
        payload["mode_reglement_id"] = payment_mode_id
        
    if not payload:
        return invoice_id
        
    return await client.update_invoice(invoice_id, payload)


@mcp.tool()
async def validate_invoice(
    invoice_id: int = Field(..., description="Invoice ID to validate")
) -> int:
    """Validate a draft invoice."""
    client = _require_client()
        
    return await client.validate_invoice(invoice_id)


@mcp.tool()
async def add_payment_to_invoice(
    invoice_id: int = Field(..., description="Invoice ID"),
    date: str = Field(..., description="Payment date (YYYY-MM-DD)"),
    payment_mode_id: int = Field(..., description="Payment mode ID (paymentid)"),
    account_id: int = Field(..., ge=1, description="Bank account ID (accountid)"),
    num_payment: Optional[str] = Field(None, description="Payment reference number"),
    close_paid: bool = Field(False, description="Close invoice as paid if fully paid")
) -> int:
    """Add a payment to an invoice (full remainder).
    
    This tool pays the remaining unpaid amount of the invoice.
    For partial payments, please use the Dolibarr UI or check API capabilities.
    """
    client = _require_client()
        
    payload = {
        "datepaye": date,
        "paymentid": payment_mode_id,
        "closepaidinvoices": "yes" if close_paid else "no",
        "accountid": account_id,
        "num_payment": num_payment or "",
    }
    
    return await client.add_payment_to_invoice(invoice_id, payload)




# ============================================================================
# ORDER TOOLS
# ============================================================================

@mcp.tool()
async def get_orders(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of orders"),
    page: int = Field(0, ge=0, description="Page number (starts at 0)"),
    status: Optional[int] = Field(None, description="Filter by status")
) -> List[OrderResult]:
    """Get a paginated list of orders."""
    client = _require_client()
        
    result = await client.get_orders(limit=limit, page=page, status=status)
    return [OrderResult(**item) for item in result]


@mcp.tool()
async def get_order_by_id(
    order_id: int = Field(..., description="Order ID")
) -> OrderResult:
    """Get details of a specific order."""
    client = _require_client()
        
    result = await client.get_order_by_id(order_id)
    return OrderResult(**result)


@mcp.tool()
async def create_order(
    customer_id: int = Field(..., description="Customer ID (socid)"),
    date: str = Field(..., description="Order date (YYYY-MM-DD)"),
    lines: List[InvoiceLine] = Field(..., description="Order lines"),
    project_id: Optional[int] = Field(None, description="Project ID"),
    delivery_date: Optional[str] = Field(None, description="Delivery date (YYYY-MM-DD)")
) -> int:
    """Create a new order (draft). Returns the new order ID."""
    client = _require_client()
        
    # Convert Pydantic models to dicts
    lines_data = [line.model_dump(exclude_none=True) for line in lines]
    
    payload = {
        "socid": customer_id,
        "date_commande": date,
        "lines": lines_data,
        "type": 0,
        "statut": 0  # Draft
    }
    
    if project_id:
        payload["fk_project"] = project_id
    if delivery_date:
        payload["date_livraison"] = delivery_date
        
    return await client.create_order(payload)



# ============================================================================
# SYSTEM TOOLS
# ============================================================================

@mcp.tool()
async def get_status() -> Dict[str, Any]:
    """Get Dolibarr system status and version information."""
    client = _require_client()
        
    return await client.get_status()


# ============================================================================
# PRODUCT TOOLS
# ============================================================================

@mcp.tool()
async def search_products_by_ref(
    ref_prefix: str = Field(..., min_length=1, max_length=40, description="Prefix of the product reference"),
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
) -> List[ProductResult]:
    """Search products by (partial) reference."""
    client = _require_client()
        
    ref_sanitized = _sanitize_search(ref_prefix)
    sqlfilters = f"(t.ref:like:'{ref_sanitized}%')"
    
    try:
        result = await client.search_products(sqlfilters=sqlfilters, limit=limit)
        return [ProductResult(**item) for item in result]
    except DolibarrAPIError as e:
        raise RuntimeError(f"Dolibarr API Error: {e.message}")


@mcp.tool()
async def search_products_by_label(
    label_search: str = Field(..., description="Search term in product label"),
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
) -> List[ProductResult]:
    """Search products by label/description text."""
    client = _require_client()
        
    label_sanitized = _sanitize_search(label_search)
    sqlfilters = f"(t.label:like:'%{label_sanitized}%')"
    
    try:
        result = await client.search_products(sqlfilters=sqlfilters, limit=limit)
        return [ProductResult(**item) for item in result]
    except DolibarrAPIError as e:
        raise RuntimeError(f"Dolibarr API Error: {e.message}")


@mcp.tool()
async def resolve_product_ref(
    ref: str = Field(..., description="Exact product reference")
) -> Dict[str, Any]:
    """Resolve an exact product reference to a product ID."""
    client = _require_client()
        
    ref_sanitized = _sanitize_search(ref)
    sqlfilters = f"(t.ref:eq:'{ref_sanitized}')"
    
    try:
        products = await client.search_products(sqlfilters=sqlfilters, limit=2)
    except DolibarrAPIError as e:
        raise RuntimeError(f"Dolibarr API Error: {e.message}") from e
    
    if not products:
        return {"status": "not_found", "ref": ref_sanitized}
    elif len(products) > 1:
        return {"status": "ambiguous", "ref": ref_sanitized, "count": len(products)}
    else:
        product = products[0]
        return {
            "status": "ok",
            "product_id": product.get("id"),
            "ref": product.get("ref"),
            "label": product.get("label"),
            "price": product.get("price")
        }



@mcp.tool()
async def get_products(
    limit: int = Field(100, ge=1, le=100, description="Maximum number of products"),
    page: int = Field(0, ge=0, description="Page number (starts at 0)"),
    category_id: Optional[int] = Field(None, description="Filter by category ID")
) -> List[ProductResult]:
    """Get a paginated list of products."""
    client = _require_client()
        
    result = await client.get_products(limit=limit, page=page, category_id=category_id)
    return [ProductResult(**item) for item in result]


@mcp.tool()
async def get_product_by_id(
    product_id: int = Field(..., description="Product ID")
) -> ProductResult:
    """Get details of a specific product."""
    client = _require_client()
        
    result = await client.get_product_by_id(product_id)
    return ProductResult(**result)


@mcp.tool()
async def create_product(
    ref: str = Field(..., description="Product reference"),
    label: str = Field(..., description="Product label"),
    price: float = Field(..., description="Selling price"),
    type: int = Field(0, description="Type (0=Product, 1=Service)"),
    description: Optional[str] = Field(None, description="Product description"),
    tva_tx: float = Field(20.0, description="VAT rate")
) -> int:
    """Create a new product. Returns the new product ID."""
    client = _require_client()
        
    payload = {
        "ref": ref,
        "label": label,
        "price": str(price),
        "type": type,
        "tva_tx": str(tva_tx)
    }
    if description:
        payload["description"] = description
        
    return await client.create_product(payload)




if __name__ == "__main__":
    mcp.run()
