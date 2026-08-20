import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from dolibarr_mcp.config import Config
from dolibarr_mcp.dolibarr_client import DolibarrClient
from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import InvoiceLine
from dolibarr_mcp.tools.invoices import register_invoice_tools

@pytest.mark.asyncio
class TestInvoiceAtomic:
    
    @pytest.fixture
    def client(self):
        config = Config(
            dolibarr_url="https://test.dolibarr.com/api/index.php",
            api_key="test_key"
        )
        return DolibarrClient(config)

    @patch('aiohttp.ClientSession.request')
    async def test_add_invoice_line(self, mock_request, client):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '123' # Returns line ID usually
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.add_invoice_line(
                invoice_id=1,
                desc="Test Line",
                qty=1,
                subprice=100,
                product_id=99
            )

        # Verify call
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "https://test.dolibarr.com/api/index.php/invoices/1/lines"
        assert kwargs['json'] == {
            "desc": "Test Line",
            "qty": 1,
            "subprice": 100,
            "fk_product": 99
        }

    @patch('aiohttp.ClientSession.request')
    async def test_update_invoice_line(self, mock_request, client):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '{"success": 1}'
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.update_invoice_line(
                invoice_id=1,
                line_id=10,
                qty=5
            )

        args, kwargs = mock_request.call_args
        assert args[0] == "PUT"
        assert args[1] == "https://test.dolibarr.com/api/index.php/invoices/1/lines/10"
        assert kwargs['json'] == {"qty": 5}

    @patch('aiohttp.ClientSession.request')
    async def test_delete_invoice_line(self, mock_request, client):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '{"success": 1}'
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.delete_invoice_line(invoice_id=1, line_id=10)

        args, kwargs = mock_request.call_args
        assert args[0] == "DELETE"
        assert args[1] == "https://test.dolibarr.com/api/index.php/invoices/1/lines/10"

    @patch('aiohttp.ClientSession.request')
    async def test_validate_invoice(self, mock_request, client):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = '{"success": 1}'
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.validate_invoice(invoice_id=1, warehouse_id=5)

        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "https://test.dolibarr.com/api/index.php/invoices/1/validate"
        assert kwargs['json'] == {"idwarehouse": 5, "not_trigger": 0}


@pytest.mark.asyncio
async def test_create_invoice_passes_line_values():
    """Test that create_invoice passes qty, subprice, desc, tva_tx correctly to add_invoice_line."""
    mock_client = AsyncMock()
    mock_client.create_invoice.return_value = 42
    mock_client.add_invoice_line.return_value = 100

    # Capture the tool function via a fake MCP
    tools = {}

    class FakeMCP:
        def tool(self):
            def decorator(f):
                tools[f.__name__] = f
                return f
            return decorator

    register_invoice_tools(FakeMCP())
    create_invoice = tools["create_invoice"]

    state_module.set_client(mock_client)
    try:
        result = await create_invoice(
            customer_id=10,
            date="2026-02-11",
            cond_reglement_code=None,
            lines=[
                InvoiceLine(
                    desc="Test item",
                    subprice=Decimal("91.28"),
                    qty=Decimal("5"),
                    tva_tx=Decimal("19.0"),
                    product_id=58,
                    product_type=0,
                )
            ],
        )

        assert result == 42
        mock_client.add_invoice_line.assert_called_once()
        call_args = mock_client.add_invoice_line.call_args
        assert call_args[0][0] == 42  # invoice_id
        line_data = call_args[0][1]
        assert line_data["desc"] == "Test item"
        assert line_data["subprice"] == "91.28"
        assert line_data["qty"] == "5"
        assert line_data["tva_tx"] == "19.0"
        assert line_data["product_id"] == 58
        assert line_data["product_type"] == 0
    finally:
        state_module.set_client(None)
