"""Pydantic models for Dolibarr MCP Server."""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class DolibarrBaseModel(BaseModel):
    """Base model with extra fields ignored."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ProjectSearchResult(DolibarrBaseModel):
    """Structured project search result."""
    id: int = Field(..., description="Dolibarr project ID")
    ref: str = Field(..., description="Project reference")
    title: str = Field(..., description="Project title")
    socid: Optional[int] = Field(None, description="Associated customer ID (socid)")
    status: int = Field(..., description="Project status")
    description: Optional[str] = Field(None, description="Project description")
    date_creation: Optional[int] = Field(None, description="Creation timestamp")
    date_modification: Optional[int] = Field(None, description="Modification timestamp")


class CustomerResult(DolibarrBaseModel):
    """Structured customer/thirdparty result."""
    id: int = Field(..., description="Customer ID")
    name: str = Field(..., alias="nom", description="Customer name")
    name_alias: Optional[str] = Field(None, description="Alias name")
    code_client: Optional[str] = Field(None, description="Customer code")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    zip: Optional[str] = Field(None, description="Zip code")
    town: Optional[str] = Field(None, description="City/Town")
    status: int = Field(..., description="Status (1=Active, 0=Inactive)")
    client: int = Field(..., description="Is customer (1=Yes, 0=No)")
    fournisseur: int = Field(..., description="Is supplier (1=Yes, 0=No)")


class InvoiceLine(DolibarrBaseModel):
    """Invoice line item."""
    desc: str = Field(..., description="Description of the line item")
    subprice: Decimal = Field(..., description="Unit price (net)")
    qty: Decimal = Field(..., description="Quantity")
    tva_tx: Decimal = Field(..., description="VAT rate (e.g. 20.0)")
    product_id: Optional[int] = Field(None, description="Product ID (optional)")
    product_type: int = Field(0, description="Type (0=Product, 1=Service)")


class InvoiceResult(DolibarrBaseModel):
    """Structured invoice result."""
    id: int = Field(..., description="Invoice ID")
    ref: str = Field(..., description="Invoice reference")
    socid: int = Field(..., description="Customer ID")
    date: int = Field(..., description="Invoice date timestamp")
    total_ht: Decimal = Field(..., description="Total net amount")
    total_tva: Decimal = Field(..., description="Total VAT amount")
    total_ttc: Decimal = Field(..., description="Total gross amount")
    paye: int = Field(..., description="Paid amount (1=Paid, 0=Not paid)")
    status: int = Field(..., description="Status (0=Draft, 1=Unpaid, 2=Paid, 3=Abandoned)")


class ProductResult(DolibarrBaseModel):
    """Structured product result."""
    id: int = Field(..., description="Product ID")
    ref: str = Field(..., description="Product reference")
    label: str = Field(..., description="Product label")
    description: Optional[str] = Field(None, description="Product description")
    type: Literal[0, 1] = Field(..., description="Type (0=Product, 1=Service)")
    price: Decimal = Field(..., description="Selling price")
    price_ttc: Decimal = Field(..., description="Selling price including tax")
    tva_tx: Decimal = Field(..., description="VAT rate")
    stock_reel: Optional[float] = Field(None, description="Current stock")



class UserResult(DolibarrBaseModel):
    """Structured user result."""
    id: int = Field(..., description="User ID")
    login: str = Field(..., description="Login username")
    lastname: Optional[str] = Field(None, description="Last name")
    firstname: Optional[str] = Field(None, description="First name")
    email: Optional[str] = Field(None, description="Email address")
    admin: int = Field(..., description="Is admin (1=Yes, 0=No)")
    statut: int = Field(..., description="Status (1=Active, 0=Inactive)")


class ContactResult(DolibarrBaseModel):
    """Structured contact result."""
    id: int = Field(..., description="Contact ID")
    lastname: str = Field(..., description="Last name")
    firstname: str = Field(..., description="First name")
    email: Optional[str] = Field(None, description="Email address")
    socid: int = Field(..., description="Associated thirdparty ID")
    poste: Optional[str] = Field(None, description="Job position")
    phone_pro: Optional[str] = Field(None, description="Professional phone")


class ProposalLine(DolibarrBaseModel):
    """A line item in a proposal."""
    id: int = Field(..., description="Line ID")
    description: str = Field(..., alias="desc", description="Line description")
    unit_price: Decimal = Field(..., alias="subprice", description="Unit price (net)")
    qty: Decimal = Field(..., description="Quantity")
    vat_rate: Decimal = Field(..., alias="tva_tx", description="VAT rate (%)")
    total_ht: Decimal = Field(..., description="Total net amount")
    total_ttc: Decimal = Field(..., description="Total gross amount")
    product_id: Optional[int] = Field(None, alias="fk_product", description="Product ID")


class ProposalResult(DolibarrBaseModel):
    """Structured proposal result."""
    id: int = Field(..., description="Proposal ID")
    ref: str = Field(..., description="Proposal reference")
    socid: int = Field(..., description="Customer ID")
    date: int = Field(..., description="Proposal date timestamp")
    total_ht: Decimal = Field(..., description="Total net amount")
    total_tva: Decimal = Field(..., description="Total VAT amount")
    total_ttc: Decimal = Field(..., description="Total gross amount")
    status: int = Field(..., description="Status (0=Draft, 1=Open, 2=Signed, 3=Declined, 4=Billed)")
    project_id: Optional[int] = Field(None, description="Linked project ID")


class OrderResult(DolibarrBaseModel):
    """Structured order result."""
    id: int = Field(..., description="Order ID")
    ref: str = Field(..., description="Order reference")
    socid: int = Field(..., description="Customer ID")
    date_commande: int = Field(..., description="Order date timestamp")
    total_ht: float = Field(..., description="Total net amount")

    total_ttc: float = Field(..., description="Total gross amount")
    statut: int = Field(..., description="Status")
