# Architecture Documentation (arc42)

## 1. Introduction and Goals
This project implements a Model Context Protocol (MCP) server for Dolibarr ERP/CRM.
It allows AI agents to interact with a Dolibarr instance to perform operations like searching projects, managing customers, and creating invoices.

**Goals:**
- Provide a robust MCP interface for Dolibarr.
- Ensure type safety and validation using Pydantic.
- Use FastMCP for a simplified and modern MCP implementation.
- Securely handle API credentials.

## 2. Constraints
- **Language:** Python 3.10+
- **Framework:** FastMCP (v2.x)
- **External System:** Dolibarr REST API (v18+)
- **Deployment:** Docker / Local

## 3. Context and Scope
**Context:**
The MCP Server acts as a bridge between an AI Client (e.g., Claude Desktop, Cursor) and the Dolibarr ERP system.

**Scope:**
- **In Scope:** Projects, Customers, Contacts, Invoices, Orders, Products, Users.
- **Out of Scope:** Full ERP replication, UI components.

## 4. Solution Strategy
- **FastMCP:** Used for defining tools and resources with minimal boilerplate.
- **DolibarrClient:** A dedicated class for handling HTTP communication with Dolibarr, error handling, and response parsing.
- **Pydantic Models:** Used for defining the schema of inputs and outputs, ensuring data consistency.
- **Separation of Concerns:** Server logic (MCP) is separated from Business logic (Client).

## 5. Building Block View

### Level 1: Whitebox
- **MCP Server (`server.py`)**: The entry point. Defines tools using `@mcp.tool()`. Handles request routing.
- **Dolibarr Client (`dolibarr_client.py`)**: Encapsulates the Dolibarr API. Handles authentication (`DOLAPIKEY`), request construction, and error mapping.
- **Models (`models.py`)**: Pydantic models representing Dolibarr entities (Project, Customer, Invoice, etc.).
- **Config (`config.py`)**: Manages environment variables and configuration.

## 6. Runtime View
1.  **Tool Call:** AI Agent requests a tool execution (e.g., `search_projects`).
2.  **Validation:** FastMCP validates arguments against Pydantic models.
3.  **Execution:** `server.py` calls the corresponding method in `DolibarrClient`.
4.  **API Request:** `DolibarrClient` sends an HTTP request to Dolibarr API.
5.  **Response:** Dolibarr returns JSON.
6.  **Parsing:** `DolibarrClient` parses the JSON.
7.  **Mapping:** `server.py` maps the raw dict to a Pydantic model (e.g., `ProjectSearchResult`).
8.  **Return:** FastMCP returns the structured result to the AI Agent.

## 7. Deployment View
- **Docker:** `Dockerfile` and `docker-compose.yml` provided for containerized deployment.
- **Local:** Can be run directly via `uv run` or `python -m dolibarr_mcp`.

## 8. Cross-cutting Concepts
- **Error Handling:** `DolibarrAPIError` is caught and re-raised as `RuntimeError` for the user, or handled gracefully.
- **Security:** API Keys are loaded from environment variables. Search inputs are sanitized (`_sanitize_search`) to prevent injection.
- **Logging:** Standard Python logging.

## 9. Architecture Decisions
- **Migration to FastMCP:** Moved from low-level `mcp` library to `FastMCP` for better developer experience and reduced boilerplate (See `docs/developer/archive/MIGRATION_STRATEGY.md`).
- **Pydantic for Models:** Enforced strict typing for better reliability with LLMs.
- **Sanitization:** Custom `_sanitize_search` implemented to protect against SQL injection in Dolibarr's `sqlfilters`.

## 10. Quality Requirements
- **Reliability:** Connection tests on startup.
- **Maintainability:** Clear separation of client and server code.
- **Type Safety:** 100% type hinted.

## 11. Risks and Technical Debt
- **Dolibarr API Versioning:** API changes in Dolibarr might break the client.
- **FastMCP Stability:** FastMCP is evolving; version pinning is recommended.

## 12. Glossary
- **MCP:** Model Context Protocol.
- **Socid:** Dolibarr's internal ID for Third Parties (Société ID).
- **Ref:** Human-readable reference (e.g., PROJ-2024-001).
