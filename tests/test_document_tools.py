"""Tests for Document MCP Tools (from tools/documents.py)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.dolibarr_client import DolibarrAPIError
from dolibarr_mcp.models import DocumentDownloadResult
from dolibarr_mcp.tools.documents import register_document_tools

ODT_TEMPLATE = "generic_invoice_odt:/srv/dolibarr/documents/doctemplates/invoices/J-Rechnung.odt"


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    client.config = SimpleNamespace(dolibarr_odt_template_dir="/srv/dolibarr/documents/doctemplates")
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

    result = await document_tools_fns["download_proposal_document"](proposal_id=123, filename="")

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
        await document_tools_fns["download_proposal_document"](proposal_id=123, filename="")

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
        proposal_id=123, template="", langcode="",
    )

    assert isinstance(result, DocumentDownloadResult)
    mock_client.build_document.assert_awaited_once_with(
        "propal", "PR2601-0001/PR2601-0001.pdf", doctemplate="", langcode="",
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
        proposal_id=123, template="mycustomodt", langcode="de_DE",
    )

    mock_client.build_document.assert_awaited_once_with(
        "propal", "PR2601-0001/PR2601-0001.pdf", doctemplate="mycustomodt", langcode="de_DE",
    )


@pytest.mark.asyncio
async def test_build_proposal_document_without_ref_raises(mock_client, document_tools_fns):
    """build_proposal_document raises if the proposal has no ref (shouldn't normally happen)."""
    mock_client.get_proposal_by_id.return_value = {"id": 123, "ref": "", "last_main_doc": ""}

    with pytest.raises(ValueError, match="no final ref"):
        await document_tools_fns["build_proposal_document"](proposal_id=123, template="", langcode="")

    mock_client.build_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_invoice_document_pdf_template_returns_builddoc_result(mock_client, document_tools_fns):
    """build_invoice_document with a PDF model returns the builddoc payload directly."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.build_document.return_value = {
        "filename": "000438.pdf",
        "content-type": "application/pdf",
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    result = await document_tools_fns["build_invoice_document"](invoice_id=283, template="sponge", langcode="")

    assert isinstance(result, DocumentDownloadResult)
    assert result.filename == "000438.pdf"
    mock_client.build_document.assert_awaited_once_with("facture", "000438/000438.pdf", doctemplate="sponge", langcode="")
    mock_client.download_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_invoice_document_odt_template_fetches_generated_odt_after_404(mock_client, document_tools_fns):
    """With an ODT template Dolibarr answers 404 after generating <ref>_<Template>.odt; the tool downloads that file."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.build_document.side_effect = DolibarrAPIError("Not Found: File not found", status_code=404)
    mock_client.download_document.return_value = {
        "filename": "000438_J-Rechnung.odt",
        "content-type": "application/vnd.oasis.opendocument.text",
        "content": "YmFzZTY0Y29udGVudA==",
        "encoding": "base64",
    }

    result = await document_tools_fns["build_invoice_document"](invoice_id=283, template=ODT_TEMPLATE, langcode="de_DE")

    assert isinstance(result, DocumentDownloadResult)
    assert result.filename == "000438_J-Rechnung.odt"
    mock_client.build_document.assert_awaited_once_with("facture", "000438/000438.pdf", doctemplate=ODT_TEMPLATE, langcode="de_DE")
    mock_client.download_document.assert_awaited_once_with("facture", "000438/000438_J-Rechnung.odt")


@pytest.mark.asyncio
async def test_build_invoice_document_reraises_non_404_errors(mock_client, document_tools_fns):
    """A real generation error (500) is not swallowed by the ODT 404 workaround."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.build_document.side_effect = DolibarrAPIError("Error generating document", status_code=500)

    with pytest.raises(DolibarrAPIError, match="Error generating document"):
        await document_tools_fns["build_invoice_document"](invoice_id=283, template=ODT_TEMPLATE, langcode="")

    mock_client.download_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_invoice_document_reraises_404_for_non_odt_template(mock_client, document_tools_fns):
    """A 404 without an ODT template (no ':' in doctemplate) is a real error, not the ODT naming quirk."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.build_document.side_effect = DolibarrAPIError("Not Found", status_code=404)

    with pytest.raises(DolibarrAPIError):
        await document_tools_fns["build_invoice_document"](invoice_id=283, template="", langcode="")

    mock_client.download_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_invoice_document_draft_invoice_raises(mock_client, document_tools_fns):
    """Draft invoices only have a provisional ref; generating a document for them is refused."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "(PROV283)", "last_main_doc": ""}

    with pytest.raises(ValueError, match="validate it first"):
        await document_tools_fns["build_invoice_document"](invoice_id=283, template="", langcode="")

    mock_client.build_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_invoice_document_uses_last_main_doc(mock_client, document_tools_fns):
    """download_invoice_document strips the 'facture/' prefix from last_main_doc."""
    mock_client.get_invoice_by_id.return_value = {
        "id": 283, "ref": "000438", "last_main_doc": "facture/000438/000438_J-Rechnung.odt",
    }
    mock_client.download_document.return_value = {
        "filename": "000438_J-Rechnung.odt", "content": "YmFzZTY0Y29udGVudA==", "encoding": "base64",
    }

    result = await document_tools_fns["download_invoice_document"](invoice_id=283, filename="")

    assert isinstance(result, DocumentDownloadResult)
    mock_client.download_document.assert_awaited_once_with("facture", "000438/000438_J-Rechnung.odt")


@pytest.mark.asyncio
async def test_download_invoice_document_explicit_filename(mock_client, document_tools_fns):
    """An explicit filename is resolved inside the invoice's document dir."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.download_document.return_value = {
        "filename": "000438_J-Rechnung.odt", "content": "YmFzZTY0Y29udGVudA==", "encoding": "base64",
    }

    await document_tools_fns["download_invoice_document"](invoice_id=283, filename="000438_J-Rechnung.odt")

    mock_client.download_document.assert_awaited_once_with("facture", "000438/000438_J-Rechnung.odt")


@pytest.mark.asyncio
async def test_download_invoice_document_without_generated_doc_raises(mock_client, document_tools_fns):
    """download_invoice_document raises a clear error if nothing was generated yet."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}

    with pytest.raises(ValueError, match="no generated document yet"):
        await document_tools_fns["download_invoice_document"](invoice_id=283, filename="")

    mock_client.download_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_invoice_document_resolves_template_name(mock_client, document_tools_fns):
    """A bare template name is resolved against DOLIBARR_ODT_TEMPLATE_DIR; the caller never sees server paths."""
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}
    mock_client.build_document.side_effect = DolibarrAPIError("Not Found", status_code=404)
    mock_client.download_document.return_value = {"filename": "000438_J-Rechnung.odt", "content": "YQ==", "encoding": "base64"}

    await document_tools_fns["build_invoice_document"](invoice_id=283, template="J-Rechnung", langcode="")

    mock_client.build_document.assert_awaited_once_with("facture", "000438/000438.pdf", doctemplate=ODT_TEMPLATE, langcode="")
    mock_client.download_document.assert_awaited_once_with("facture", "000438/000438_J-Rechnung.odt")


@pytest.mark.asyncio
async def test_build_invoice_document_template_name_without_config_raises(mock_client, document_tools_fns):
    """Without DOLIBARR_ODT_TEMPLATE_DIR a bare ODT name cannot be resolved."""
    mock_client.config = SimpleNamespace(dolibarr_odt_template_dir="")
    mock_client.get_invoice_by_id.return_value = {"id": 283, "ref": "000438", "last_main_doc": ""}

    with pytest.raises(ValueError, match="DOLIBARR_ODT_TEMPLATE_DIR"):
        await document_tools_fns["build_invoice_document"](invoice_id=283, template="J-Rechnung", langcode="")

    mock_client.build_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_proposal_document_odt_template_fetches_generated_odt_after_404(mock_client, document_tools_fns):
    """Proposals share the ODT quirk handling with invoices."""
    mock_client.get_proposal_by_id.return_value = {"id": 123, "ref": "PR2601-0001", "last_main_doc": ""}
    mock_client.build_document.side_effect = DolibarrAPIError("Not Found", status_code=404)
    mock_client.download_document.return_value = {"filename": "PR2601-0001_Jona-V-Angebot.odt", "content": "YQ==", "encoding": "base64"}

    result = await document_tools_fns["build_proposal_document"](proposal_id=123, template="Jona-V-Angebot", langcode="")

    assert result.filename == "PR2601-0001_Jona-V-Angebot.odt"
    mock_client.build_document.assert_awaited_once_with(
        "propal", "PR2601-0001/PR2601-0001.pdf",
        doctemplate="generic_proposal_odt:/srv/dolibarr/documents/doctemplates/proposals/Jona-V-Angebot.odt", langcode="",
    )
    mock_client.download_document.assert_awaited_once_with("propal", "PR2601-0001/PR2601-0001_Jona-V-Angebot.odt")
