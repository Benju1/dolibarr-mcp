"""Connection handling: no keep-alive reuse, GET retried once, writes never."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from dolibarr_mcp.dolibarr_client import DolibarrAPIError, DolibarrClient


def _disconnected(method: str) -> DolibarrAPIError:
    cause = aiohttp.ServerDisconnectedError()
    err = DolibarrAPIError(f"HTTP client error on {method} x: ServerDisconnectedError")
    err.__cause__ = cause
    return err


def _client() -> DolibarrClient:
    config = MagicMock()
    config.dolibarr_url = "https://erp.example.com/api/index.php"
    config.api_key = "k"
    return DolibarrClient(config)


@pytest.mark.asyncio
async def test_session_does_not_reuse_connections():
    client = _client()
    await client.start_session()
    try:
        assert client.session.connector.force_close is True
    finally:
        await client.close_session()


@pytest.mark.asyncio
async def test_get_is_retried_once_after_connection_loss():
    client = _client()
    client._make_request = AsyncMock(side_effect=[_disconnected("GET"), [{"ok": 1}]])

    assert await client.request("GET", "products/1/purchase_prices") == [{"ok": 1}]
    assert client._make_request.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
async def test_writes_are_never_retried(method):
    client = _client()
    client._make_request = AsyncMock(side_effect=[_disconnected(method), {"id": 1}])

    with pytest.raises(DolibarrAPIError):
        await client.request(method, "proposals", data={})
    assert client._make_request.await_count == 1


@pytest.mark.asyncio
async def test_get_http_error_is_not_retried():
    client = _client()
    client._make_request = AsyncMock(side_effect=[DolibarrAPIError("Not Found", status_code=404), []])

    with pytest.raises(DolibarrAPIError):
        await client.request("GET", "products/999")
    assert client._make_request.await_count == 1
