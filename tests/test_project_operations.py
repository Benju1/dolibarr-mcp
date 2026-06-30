"""
Project Management Integration Tests for Dolibarr MCP Server.

These tests verify complete CRUD operations for Dolibarr projects.
Run with: pytest tests/test_project_operations.py -v
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dolibarr_mcp import DolibarrClient, Config
from dolibarr_mcp import state as state_module
from dolibarr_mcp.dolibarr_client import DolibarrAPIError
from dolibarr_mcp.models import ProjectSearchResult
from dolibarr_mcp.tools.projects import register_project_tools


class TestProjectOperations:
    """Test complete CRUD operations for Dolibarr projects."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config(
            dolibarr_url="https://test.dolibarr.com",
            dolibarr_api_key="test_api_key",
            log_level="INFO"
        )

    @pytest.fixture
    def client(self, config):
        """Create a test client instance."""
        return DolibarrClient(config)

    @pytest.mark.asyncio
    async def test_project_crud_lifecycle(self, client):
        """Test complete project CRUD lifecycle."""
        with patch.object(client, 'request') as mock_request:
            # Create
            mock_request.return_value = {"id": 200}
            project_id = await client.create_project({
                "title": "New Website",
                "description": "Website redesign project",
                "socid": 1,
                "status": 1
            })
            assert project_id == 200

            # Read
            mock_request.return_value = {
                "id": 200,
                "ref": "PJ2401-001",
                "title": "New Website",
                "description": "Website redesign project"
            }
            project = await client.get_project_by_id(200)
            assert project["title"] == "New Website"
            assert project["ref"] == "PJ2401-001"

            # Update
            mock_request.return_value = {"id": 200, "title": "Updated Website Project"}
            result = await client.update_project(200, {"title": "Updated Website Project"})
            assert result["title"] == "Updated Website Project"

            # Delete
            mock_request.return_value = {"success": True}
            result = await client.delete_project(200)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_projects(self, client):
        """Test searching projects."""
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = [
                {"id": 200, "ref": "PJ2401-001", "title": "Website Redesign"},
                {"id": 201, "ref": "PJ2401-002", "title": "Mobile App"}
            ]

            # Search by query
            results = await client.search_projects(sqlfilters="(t.title:like:'%Website%')", limit=10)

            assert len(results) == 2
            assert results[0]["title"] == "Website Redesign"

            # Verify call arguments
            call_args = mock_request.call_args
            assert call_args is not None
            method, endpoint = call_args[0]
            kwargs = call_args[1]

            assert method == "GET"
            assert endpoint == "projects"
            assert kwargs["params"]["sqlfilters"] == "(t.title:like:'%Website%')"

    @pytest.mark.asyncio
    async def test_get_projects_with_filters(self, client):
        """Test getting projects with status filter."""
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = []

            await client.get_projects(limit=50, page=2, status=1)

            call_args = mock_request.call_args
            kwargs = call_args[1]
            params = kwargs["params"]

            assert params["limit"] == 50
            assert params["page"] == 2
            assert params["sqlfilters"] == "(t.fk_statut:=:1)"

    @pytest.mark.asyncio
    async def test_add_project_contact(self, client):
        """Test adding a contact to a project."""
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = 42
            result = await client.add_project_contact(200, {
                "fk_socpeople": 151,
                "type_contact": "PROJECTCONTRIBUTOR",
                "source": "external",
            })
            assert result == 42
            mock_request.assert_called_once_with(
                "POST", "projects/200/contacts",
                data={
                    "fk_socpeople": 151,
                    "type_contact": "PROJECTCONTRIBUTOR",
                    "source": "external",
                }
            )

    @pytest.mark.asyncio
    async def test_get_project_contacts(self, client):
        """Test getting contacts assigned to a project."""
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = [
                {"id": 1, "fk_socpeople": 151, "type_contact": "PROJECTCONTRIBUTOR",
                 "source": "external", "lastname": "Mueller", "firstname": "Michael"},
            ]
            result = await client.get_project_contacts(200)
            assert len(result) == 1
            assert result[0]["fk_socpeople"] == 151
            mock_request.assert_called_once_with("GET", "projects/200/contacts")

    @pytest.mark.asyncio
    async def test_remove_project_contact(self, client):
        """Test removing a contact from a project."""
        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = {"success": True}
            result = await client.remove_project_contact(200, 151, "PROJECTCONTRIBUTOR")
            assert result["success"] is True
            mock_request.assert_called_once_with(
                "DELETE", "projects/200/contact/151/PROJECTCONTRIBUTOR"
            )

    @pytest.mark.asyncio
    async def test_add_project_contact_404_version_error(self, client):
        """404 from add_project_contact re-raises with Dolibarr version hint."""
        with patch.object(client, 'request', side_effect=DolibarrAPIError("Not Found", status_code=404)):
            with pytest.raises(DolibarrAPIError, match="Requires Dolibarr 21.0"):
                await client.add_project_contact(200, {
                    "fk_socpeople": 151,
                    "type_contact": "PROJECTCONTRIBUTOR",
                    "source": "external",
                })

    @pytest.mark.asyncio
    async def test_get_project_contacts_404_version_error(self, client):
        """404 from get_project_contacts re-raises with Dolibarr version hint."""
        with patch.object(client, 'request', side_effect=DolibarrAPIError("Not Found", status_code=404)):
            with pytest.raises(DolibarrAPIError, match="Requires Dolibarr 21.0"):
                await client.get_project_contacts(200)

    @pytest.mark.asyncio
    async def test_remove_project_contact_404_version_error(self, client):
        """404 from remove_project_contact re-raises with Dolibarr version hint."""
        with patch.object(client, 'request', side_effect=DolibarrAPIError("Not Found", status_code=404)):
            with pytest.raises(DolibarrAPIError, match="Requires Dolibarr 21.0"):
                await client.remove_project_contact(200, 151, "PROJECTCONTRIBUTOR")


class TestCreateProjectTool:
    """Tests for the create_project MCP tool."""

    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        state_module.set_client(client)
        yield client
        state_module.set_client(None)

    @pytest.fixture
    def project_tools(self):
        mcp = AsyncMock()
        registered = {}

        def tool_decorator():
            def wrapper(fn):
                registered[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_project_tools(mcp)
        return registered

    @pytest.mark.asyncio
    async def test_create_project_without_ref(self, mock_client, project_tools):
        """Omitting ref sends 'auto' to trigger Dolibarr's numbering module."""
        mock_client.create_project.return_value = 42

        result = await project_tools["create_project"](
            title="Test Project", ref=None, socid=None,
            description=None, status=1,
        )

        payload = mock_client.create_project.call_args[0][0]
        assert payload["ref"] == "auto"
        assert result == 42

    @pytest.mark.asyncio
    async def test_create_project_with_explicit_ref(self, mock_client, project_tools):
        """Explicit ref is passed through as-is."""
        mock_client.create_project.return_value = 43

        result = await project_tools["create_project"](
            title="Test Project", ref="CUSTOM-001", socid=None,
            description=None, status=1,
        )

        payload = mock_client.create_project.call_args[0][0]
        assert payload["ref"] == "CUSTOM-001"
        assert result == 43


class TestUpdateProjectTool:
    """Tests for the update_project MCP tool."""

    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        state_module.set_client(client)
        yield client
        state_module.set_client(None)

    @pytest.fixture
    def project_tools(self):
        mcp = AsyncMock()
        registered = {}

        def tool_decorator():
            def wrapper(fn):
                registered[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_project_tools(mcp)
        return registered

    @pytest.mark.asyncio
    async def test_update_project_basic(self, mock_client, project_tools):
        """update_project sends title and description, returns re-read result."""
        mock_client.update_project.return_value = None
        mock_client.get_project_by_id.return_value = {
            "id": 306, "ref": "PJ0306", "title": "New Title",
            "status": 1, "description": "New desc",
        }

        result = await project_tools["update_project"](
            project_id=306, title="New Title", description="New desc",
            status=None, socid=None, usage_opportunity=None,
            fk_opp_status=None, opp_amount=None, opp_percent=None,
        )

        mock_client.update_project.assert_awaited_once_with(
            306, {"title": "New Title", "description": "New desc"}
        )
        assert isinstance(result, ProjectSearchResult)
        assert result.id == 306
        assert result.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_project_opportunity_fields(self, mock_client, project_tools):
        """update_project forwards opportunity fields to client."""
        mock_client.update_project.return_value = None
        mock_client.get_project_by_id.return_value = {
            "id": 306, "ref": "PJ0306", "title": "Lead Project",
            "status": 1, "fk_opp_status": 2, "opp_amount": 5000.0,
        }

        await project_tools["update_project"](
            project_id=306, title=None, description=None,
            status=None, socid=None,
            usage_opportunity=1, fk_opp_status=2,
            opp_amount=5000.0, opp_percent=75.0,
        )

        mock_client.update_project.assert_awaited_once_with(306, {
            "usage_opportunity": 1, "fk_opp_status": 2,
            "opp_amount": 5000.0, "opp_percent": 75.0,
        })

    @pytest.mark.asyncio
    async def test_update_project_empty_payload_skips_put(self, mock_client, project_tools):
        """update_project with no optional fields skips PUT, only re-reads."""
        mock_client.get_project_by_id.return_value = {
            "id": 306, "ref": "PJ0306", "title": "Unchanged",
            "status": 1,
        }

        result = await project_tools["update_project"](
            project_id=306, title=None, description=None,
            status=None, socid=None, usage_opportunity=None,
            fk_opp_status=None, opp_amount=None, opp_percent=None,
        )

        mock_client.update_project.assert_not_awaited()
        mock_client.get_project_by_id.assert_awaited_once_with(306)
        assert result.title == "Unchanged"

    @pytest.mark.asyncio
    async def test_update_project_zero_values_pass_through(self, mock_client, project_tools):
        """Zero values (status=0, opp_amount=0.0) are sent, not skipped."""
        mock_client.update_project.return_value = None
        mock_client.get_project_by_id.return_value = {
            "id": 306, "ref": "PJ0306", "title": "Project",
            "status": 0, "opp_amount": 0.0,
        }

        await project_tools["update_project"](
            project_id=306, title=None, description=None,
            status=0, socid=None, usage_opportunity=None,
            fk_opp_status=None, opp_amount=0.0, opp_percent=None,
        )

        mock_client.update_project.assert_awaited_once_with(306, {
            "status": 0, "opp_amount": 0.0,
        })


class TestDeleteProjectTool:
    """Tests for the delete_project MCP tool."""

    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        state_module.set_client(client)
        yield client
        state_module.set_client(None)

    @pytest.fixture
    def project_tools(self):
        mcp = AsyncMock()
        registered = {}

        def tool_decorator():
            def wrapper(fn):
                registered[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_project_tools(mcp)
        return registered

    @pytest.mark.asyncio
    async def test_delete_project(self, mock_client, project_tools):
        """delete_project calls client and returns confirmation."""
        mock_client.delete_project.return_value = None

        result = await project_tools["delete_project"](project_id=200)

        mock_client.delete_project.assert_awaited_once_with(200)
        assert result == {"status": "deleted", "project_id": 200}
