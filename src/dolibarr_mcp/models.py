"""Pydantic models for Dolibarr MCP Server."""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler, field_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class ScientificDecimal(Decimal):
    """Decimal subclass that accepts scientific notation in JSON Schema.

    This is required because Dolibarr API sometimes returns very small
    numbers in scientific notation (e.g., '0E-8' for rounding differences),
    but Pydantic's default Decimal JSON schema rejects this format.

    Examples:
        - '0E-8' -> Decimal('0E-8')
        - '1.5E-10' -> Decimal('1.5E-10')
        - '123.45' -> Decimal('123.45')
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Define Pydantic validation schema."""
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Decimal),
                    core_schema.decimal_schema(),
                    core_schema.str_schema(),
                ]
            ),
        )

    @classmethod
    def _validate(cls, v):
        """Validate and convert input to Decimal."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (str, int, float)):
            return Decimal(str(v))
        raise ValueError(f"Cannot convert {type(v)} to Decimal")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Generate JSON Schema that accepts scientific notation.

        The pattern allows:
        - Standard decimals: 123.45, -5.67, +10
        - Scientific notation: 1.5E-10, 0E-8, 2.3e+5
        - Prevents invalid patterns: just signs/dots like '+.', '+-'
        """
        return {
            "anyOf": [
                {"type": "number"},
                {
                    "type": "string",
                    "pattern": r"^(?!^[-+.]*$)[+-]?0*\d*\.?\d*([eE][+-]?\d+)?$",
                },
            ]
        }


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
    fk_opp_status: Optional[int] = Field(None, description="Opportunity/lead status ID (set if project is a lead)")
    opp_amount: Optional[float] = Field(None, description="Opportunity amount")
    description: Optional[str] = Field(None, description="Project description")
    date_creation: Optional[int] = Field(None, description="Creation timestamp")
    date_modification: Optional[int] = Field(None, description="Modification timestamp")


class ProjectContactResult(DolibarrBaseModel):
    """A contact assigned to a project."""

    id: int = Field(..., description="Contact link ID")
    fk_socpeople: int = Field(..., description="Contact ID")
    type_contact: str = Field(..., description="Contact type code (e.g. PROJECTCONTRIBUTOR)")
    source: str = Field(..., description="'internal' or 'external'")
    lastname: Optional[str] = Field(None, description="Contact last name")
    firstname: Optional[str] = Field(None, description="Contact first name")


class CustomerResult(DolibarrBaseModel):
    """Structured customer/thirdparty result."""

    id: int = Field(..., description="Customer ID")
    name: str = Field(..., alias="nom", description="Customer name")
    name_alias: Optional[str] = Field(None, description="Alias name")
    code_client: Optional[str] = Field(None, description="Customer code")
    code_fournisseur: Optional[str] = Field(None, description="Supplier code")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    zip: Optional[str] = Field(None, description="Zip code")
    town: Optional[str] = Field(None, description="City/Town")
    status: int = Field(..., description="Status (1=Active, 0=Inactive)")
    client: int = Field(..., description="Is customer (1=Yes, 0=No)")
    fournisseur: int = Field(..., description="Is supplier (1=Yes, 0=No)")
    idprof1: Optional[str] = Field(None, description="Professional ID 1 (UID/SIREN etc.)")


class InvoiceLine(DolibarrBaseModel):
    """Invoice line item."""

    desc: str = Field(..., description="Description of the line item")
    subprice: ScientificDecimal = Field(..., description="Unit price (net)")
    qty: ScientificDecimal = Field(..., description="Quantity")
    tva_tx: ScientificDecimal = Field(..., description="VAT rate (e.g. 20.0)")
    product_id: Optional[int] = Field(None, description="Product ID (optional)")
    product_type: int = Field(0, description="Type (0=Product, 1=Service)")


class InvoiceLineResult(DolibarrBaseModel):
    """Invoice line item from API response."""

    id: int = Field(..., description="Line ID")
    desc: str = Field("", description="Description")
    qty: ScientificDecimal = Field(..., description="Quantity")
    subprice: ScientificDecimal = Field(..., description="Unit price (net)")
    total_ht: ScientificDecimal = Field(..., description="Total net amount")
    total_tva: ScientificDecimal = Field(..., description="Total VAT amount")
    total_ttc: ScientificDecimal = Field(..., description="Total gross amount")
    tva_tx: ScientificDecimal = Field(..., description="VAT rate (%)")
    product_type: int = Field(0, description="Type (0=Product, 1=Service)")
    product_ref: Optional[str] = Field(None, description="Product reference")
    product_label: Optional[str] = Field(None, description="Product label")
    fk_product: Optional[int] = Field(None, description="Product ID")


class InvoiceResult(DolibarrBaseModel):
    """Structured invoice result."""

    id: int = Field(..., description="Invoice ID")
    ref: str = Field(..., description="Invoice reference")
    socid: int = Field(..., description="Customer ID")
    date: int = Field(..., description="Invoice date timestamp")
    total_ht: ScientificDecimal = Field(..., description="Total net amount")
    total_tva: ScientificDecimal = Field(..., description="Total VAT amount")
    total_ttc: ScientificDecimal = Field(..., description="Total gross amount")
    paye: int = Field(..., description="Paid amount (1=Paid, 0=Not paid)")
    status: int = Field(
        ..., description="Status (0=Draft, 1=Unpaid, 2=Paid, 3=Abandoned)"
    )
    note_public: Optional[str] = Field(None, description="Public note (visible on PDF)")
    note_private: Optional[str] = Field(None, description="Private note (internal only)")
    lines: Optional[list[InvoiceLineResult]] = Field(None, description="Invoice line items")


class ProductResult(DolibarrBaseModel):
    """Structured product result."""

    id: int = Field(..., description="Product ID")
    ref: str = Field(..., description="Product reference")
    label: str = Field(..., description="Product label")
    description: Optional[str] = Field(None, description="Product description")
    type: Literal[0, 1] = Field(..., description="Type (0=Product, 1=Service)")
    price: ScientificDecimal = Field(..., description="Selling price")
    price_ttc: ScientificDecimal = Field(..., description="Selling price including tax")
    tva_tx: ScientificDecimal = Field(..., description="VAT rate")
    stock_reel: Optional[float] = Field(None, description="Current stock")
    cost_price: Optional[ScientificDecimal] = Field(None, description="Cost/purchase price")
    barcode: Optional[str] = Field(None, description="Barcode value")
    barcode_type_code: Optional[str] = Field(None, description="Barcode type (e.g. EAN13)")
    status: Optional[int] = Field(None, description="Selling status (0=Not for sale, 1=For sale)")
    status_buy: Optional[int] = Field(None, description="Buying status (0=Not for purchase, 1=For purchase)")
    note_public: Optional[str] = Field(None, description="Public note")
    note_private: Optional[str] = Field(None, description="Private note")

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, v: Any) -> int:
        if isinstance(v, str):
            return int(v)
        return v


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
    unit_price: ScientificDecimal = Field(
        ..., alias="subprice", description="Unit price (net)"
    )
    qty: ScientificDecimal = Field(..., description="Quantity")
    vat_rate: ScientificDecimal = Field(..., alias="tva_tx", description="VAT rate (%)")
    total_ht: ScientificDecimal = Field(..., description="Total net amount")
    total_ttc: ScientificDecimal = Field(..., description="Total gross amount")
    product_id: Optional[int] = Field(
        None, alias="fk_product", description="Product ID"
    )


class ProposalResult(DolibarrBaseModel):
    """Structured proposal result."""

    id: int = Field(..., description="Proposal ID")
    ref: str = Field(..., description="Proposal reference")
    socid: int = Field(..., description="Customer ID")
    date: int = Field(..., description="Proposal date timestamp")
    total_ht: ScientificDecimal = Field(..., description="Total net amount")
    total_tva: ScientificDecimal = Field(..., description="Total VAT amount")
    total_ttc: ScientificDecimal = Field(..., description="Total gross amount")
    status: int = Field(
        ..., description="Status (0=Draft, 1=Open, 2=Signed, 3=Declined, 4=Billed)"
    )
    project_id: Optional[int] = Field(None, description="Linked project ID")
    lines: Optional[list[ProposalLine]] = Field(None, description="Proposal line items")


class OrderResult(DolibarrBaseModel):
    """Structured order result."""

    id: int = Field(..., description="Order ID")
    ref: str = Field(..., description="Order reference")
    socid: int = Field(..., description="Customer ID")
    date_commande: int = Field(..., description="Order date timestamp")
    total_ht: float = Field(..., description="Total net amount")

    total_ttc: float = Field(..., description="Total gross amount")
    statut: int = Field(..., description="Status")
