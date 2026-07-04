"""Tests for Document MCP Tools (from tools/documents.py)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import DocumentDownloadResult
from dolibarr_mcp.tools.documents import register_document_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def document_tools_fns():
    """Register document tools and capture the inner functions."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_document_tools(mcp)
    return registered


@pytest.mark.asyncio
async def test_download_document(mock_client, document_tools_fns):
    """download_document passes modulepart/original_file straight through."""
    mock_client.download_document.return_value = {
        "filename": "PR2601-0001.odt",
        "content-type": "application/vnd.oasis.opendocument.text",
        "filesize": 12345,
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    result = await document_tools_fns["download_document"](
        modulepart="propal", original_file="PR2601-0001/PR2601-0001.odt",
    )

    assert isinstance(result, DocumentDownloadResult)
    assert result.filename == "PR2601-0001.odt"
    assert result.content_type == "application/vnd.oasis.opendocument.text"
    assert result.filesize == 12345
    assert result.content == "YmFzZTY0Y29udGVudA=="
    mock_client.download_document.assert_awaited_once_with("propal", "PR2601-0001/PR2601-0001.odt")


@pytest.mark.asyncio
async def test_download_proposal_document_uses_last_main_doc(mock_client, document_tools_fns):
    """download_proposal_document reads last_main_doc from the proposal and downloads it."""
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PR2601-0001",
        "last_main_doc": "PR2601-0001/PR2601-0001.odt",
    }
    mock_client.download_document.return_value = {
        "filename": "PR2601-0001.odt",
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    result = await document_tools_fns["download_proposal_document"](proposal_id=123)

    assert isinstance(result, DocumentDownloadResult)
    mock_client.get_proposal_by_id.assert_awaited_once_with(123)
    mock_client.download_document.assert_awaited_once_with("propal", "PR2601-0001/PR2601-0001.odt")


@pytest.mark.asyncio
async def test_download_proposal_document_without_generated_doc_raises(mock_client, document_tools_fns):
    """download_proposal_document raises a clear error if last_main_doc is empty."""
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PR2601-0001",
        "last_main_doc": "",
    }

    with pytest.raises(ValueError, match="no generated document yet"):
        await document_tools_fns["download_proposal_document"](proposal_id=123)

    mock_client.download_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_proposal_document_uses_last_main_doc_when_present(mock_client, document_tools_fns):
    """build_proposal_document reuses last_main_doc as the reference path when set."""
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PR2601-0001",
        "last_main_doc": "PR2601-0001/PR2601-0001.odt",
    }
    mock_client.build_document.return_value = {
        "filename": "PR2601-0001.odt",
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    result = await document_tools_fns["build_proposal_document"](
        proposal_id=123, doctemplate="", langcode="",
    )

    assert isinstance(result, DocumentDownloadResult)
    mock_client.build_document.assert_awaited_once_with(
        "propal", "PR2601-0001/PR2601-0001.odt", doctemplate="", langcode="",
    )


@pytest.mark.asyncio
async def test_build_proposal_document_falls_back_to_ref_when_no_doc_yet(mock_client, document_tools_fns):
    """build_proposal_document derives a reference path from ref if no document exists yet."""
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PR2601-0001",
        "last_main_doc": "",
    }
    mock_client.build_document.return_value = {
        "filename": "PR2601-0001.odt",
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    await document_tools_fns["build_proposal_document"](
        proposal_id=123, doctemplate="mycustomodt", langcode="de_DE",
    )

    mock_client.build_document.assert_awaited_once_with(
        "propal", "PR2601-0001/PR2601-0001.pdf", doctemplate="mycustomodt", langcode="de_DE",
    )


@pytest.mark.asyncio
async def test_build_proposal_document_without_ref_raises(mock_client, document_tools_fns):
    """build_proposal_document raises if the proposal has no ref (shouldn't normally happen)."""
    mock_client.get_proposal_by_id.return_value = {"id": 123, "ref": "", "last_main_doc": ""}

    with pytest.raises(ValueError, match="no ref"):
        await document_tools_fns["build_proposal_document"](proposal_id=123, doctemplate="", langcode="")

    mock_client.build_document.assert_not_awaited()
