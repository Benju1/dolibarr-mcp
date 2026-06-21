"""Proposal/Quote tools for Dolibarr MCP Server."""

from typing import List, Optional
from decimal import Decimal

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import ProposalResult, ProposalLine, InvoiceLine


def _require_client() -> DolibarrClient:
    """Ensure client is initialized and return it."""
    from ..state import get_client
    return get_client()


def register_proposal_tools(mcp: FastMCP) -> None:
    """Register all proposal-related tools with the MCP server."""
    
    @mcp.tool()
    async def get_proposals(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of proposals"),
        status: Optional[str] = Field(None, description="Filter by status"),
        project_id: Optional[int] = Field(None, description="Filter by project ID"),
        customer_id: Optional[int] = Field(None, description="Filter by customer ID")
    ) -> List[ProposalResult]:
        """Get a list of proposals (quotes) with optional filtering.
        
        Status values: draft, open, signed, declined, billed.
        Can combine multiple filters.
        """
        client = _require_client()
        
        thirdparty_ids = str(customer_id) if customer_id else None
        
        filters = []
        if project_id:
            filters.append(f"(t.fk_projet:=:{project_id})")
        
        sqlfilters = " AND ".join(filters) if filters else None
        
        result = await client.get_proposals(limit=limit, status=status, sqlfilters=sqlfilters, thirdparty_ids=thirdparty_ids)
        return [ProposalResult(**item) for item in result]

    @mcp.tool()
    async def get_proposal_by_id(
        proposal_id: int = Field(..., description="Proposal ID")
    ) -> ProposalResult:
        """Get details of a specific proposal."""
        client = _require_client()
        
        result = await client.get_proposal_by_id(proposal_id)
        return ProposalResult(**result)

    @mcp.tool()
    async def create_proposal(
        customer_id: int = Field(..., description="Customer ID (socid)"),
        date: str = Field(..., description="Proposal date (YYYY-MM-DD)"),
        lines: Optional[List[InvoiceLine]] = Field(None, description="Proposal lines"),
        project_id: Optional[int] = Field(None, description="Project ID"),
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
    ) -> ProposalResult:
        """Create a new proposal (draft). Returns full proposal details."""
        client = _require_client()
        
        # 1. Create proposal header
        payload = {
            "socid": customer_id,
            "date": date,
            "statut": 0  # Draft status
        }
        
        if project_id:
            payload["fk_projet"] = project_id
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
        
        result = await client.create_proposal(payload)
        proposal_id = result.get("id") if isinstance(result, dict) else result
        
        # 2. Add lines individually
        if lines:
            try:
                for line in lines:
                    line_data = line.model_dump(exclude_none=True)
                    # Decimal → str for JSON serialization
                    for key in ("subprice", "qty", "tva_tx"):
                        if key in line_data:
                            line_data[key] = str(line_data[key])
                    await client.add_proposal_line(proposal_id, line_data)
            except Exception:
                # Rollback: delete the proposal if line addition fails
                await client.delete_proposal(proposal_id)
                raise
        
        # Return full state
        full = await client.get_proposal_by_id(proposal_id)
        return ProposalResult(**full)

    @mcp.tool()
    async def update_proposal(
        proposal_id: int = Field(..., description="Proposal ID"),
        date: Optional[str] = Field(None, description="Proposal date (YYYY-MM-DD)"),
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
    ) -> ProposalResult:
        """Update an existing proposal (draft only). Returns updated proposal."""
        client = _require_client()
        
        payload = {}
        if date:
            payload["date"] = date
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
        
        if not payload:
            raise ValueError("At least one field (date, payment_mode_id) must be provided")
        
        await client.update_proposal(proposal_id, payload)

        # Return updated state
        full = await client.get_proposal_by_id(proposal_id)
        return ProposalResult(**full)

    @mcp.tool()
    async def delete_proposal(
        proposal_id: int = Field(..., description="Proposal ID to delete")
    ) -> int:
        """Delete a proposal (draft only). Returns the deleted proposal ID."""
        client = _require_client()
        
        await client.delete_proposal(proposal_id)
        return proposal_id

    @mcp.tool()
    async def validate_proposal(
        proposal_id: int = Field(..., description="Proposal ID to validate")
    ) -> ProposalResult:
        """Validate a draft proposal (transition to open/signed state).
        
        Returns the updated proposal details after validation.
        """
        client = _require_client()
        
        await client.validate_proposal(proposal_id)

        # Return updated state
        full = await client.get_proposal_by_id(proposal_id)
        return ProposalResult(**full)

    @mcp.tool()
    async def convert_proposal_to_order(
        proposal_id: int = Field(..., description="Proposal ID to convert")
    ) -> int:
        """Convert a validated proposal to a sales order.
        
        Returns the new order ID.
        Raises error if conversion fails or order ID is not available.
        """
        client = _require_client()
        
        result = await client.convert_proposal_to_order(proposal_id)
        
        # Safely extract order ID from response
        if isinstance(result, dict):
            order_id = result.get("id")
            if order_id:
                return int(order_id)
            # If no ID in response, it's a failure (API returned empty/null)
            raise ValueError(f"Conversion failed: no order ID returned from API")
        elif isinstance(result, (int, str)):
            return int(result)
        else:
            # Unexpected response format
            raise ValueError(f"Conversion failed: unexpected API response type {type(result)}")

    @mcp.tool()
    async def add_proposal_line(
        proposal_id: int = Field(..., description="Proposal ID"),
        description: str = Field(..., description="Line description"),
        unit_price: Decimal = Field(..., description="Unit price (net)"),
        quantity: Decimal = Field(..., description="Quantity"),
        vat_rate: Decimal = Field(20.0, description="VAT rate (%)"),
        product_id: Optional[int] = Field(None, description="Product ID (optional)")
    ) -> int:
        """Add a line to a proposal.
        
        Returns the created line ID.
        Note: Dolibarr API returns only the line ID, not full line details.
        """
        client = _require_client()
        
        line_data = {
            "desc": description,
            "subprice": str(unit_price),
            "qty": str(quantity),
            "tva_tx": str(vat_rate),
            "product_type": 0
        }

        if product_id:
            line_data["fk_product"] = product_id

        result = await client.add_proposal_line(proposal_id, line_data)
        if result == 0 or result == "0":
            raise ValueError(f"Dolibarr addline returned 0 — line was not created. Payload: {line_data}")
        return int(result) if isinstance(result, (int, str)) else result.get("id", result)

    @mcp.tool()
    async def update_proposal_line(
        proposal_id: int = Field(..., description="Proposal ID"),
        line_id: int = Field(..., description="Line ID"),
        description: Optional[str] = Field(None, description="Line description"),
        unit_price: Optional[Decimal] = Field(None, description="Unit price (net)"),
        quantity: Optional[Decimal] = Field(None, description="Quantity"),
        vat_rate: Optional[Decimal] = Field(None, description="VAT rate (%)")
    ) -> int:
        """Update a line in a proposal.

        Provide only the fields you want to update.
        Returns the updated line ID.
        """
        client = _require_client()

        if all(v is None for v in (description, unit_price, quantity, vat_rate)):
            raise ValueError("At least one field must be provided for update")

        # Fetch current line data to preserve unprovided fields
        proposal_data = await client.get_proposal_by_id(proposal_id)
        current_line = None
        for line in proposal_data.get("lines", []):
            if int(line.get("id", 0)) == line_id:
                current_line = line
                break
        if current_line is None:
            raise ValueError(f"Line {line_id} not found in proposal {proposal_id}")

        # Build payload from current values, override with provided values
        payload = {
            "desc": current_line.get("desc", ""),
            "subprice": str(current_line.get("subprice", 0)),
            "qty": str(current_line.get("qty", 0)),
            "tva_tx": str(current_line.get("tva_tx", 0)),
            "product_type": current_line.get("product_type", 0),
        }
        if current_line.get("fk_product"):
            payload["fk_product"] = current_line["fk_product"]

        if description is not None:
            payload["desc"] = description
        if unit_price is not None:
            payload["subprice"] = str(unit_price)
        if quantity is not None:
            payload["qty"] = str(quantity)
        if vat_rate is not None:
            payload["tva_tx"] = str(vat_rate)

        result = await client.update_proposal_line(proposal_id, line_id, payload)
        return line_id

    @mcp.tool()
    async def delete_proposal_line(
        proposal_id: int = Field(..., description="Proposal ID"),
        line_id: int = Field(..., description="Line ID to delete")
    ) -> int:
        """Delete a line from a proposal.
        
        Returns the deleted line ID.
        """
        client = _require_client()
        
        await client.delete_proposal_line(proposal_id, line_id)
        return line_id
