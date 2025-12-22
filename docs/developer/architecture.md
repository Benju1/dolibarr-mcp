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
- **Language:** Python 3.12+
- **Framework:** FastMCP (v2.x)
- **External System:** Dolibarr REST API (v22.0.0+)
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
- **State Management:** A `state.py` module manages the global client instance to prevent circular imports and enable clean dependency injection.
- **Pydantic Models:** Used for defining the schema of inputs and outputs, ensuring data consistency.
- **Separation of Concerns:** Server logic (MCP) is separated from Business logic (Client).

## 5. Building Block View

### Level 1: Whitebox
- **MCP Server (`server.py`)**: The entry point. Initializes the server and registers tools.
- **State Manager (`state.py`)**: Holds the singleton `DolibarrClient` instance. Resolves circular dependencies between server and tools.
- **Tool Modules (`tools/*.py`)**: Domain-specific tool implementations (e.g., `proposals.py`, `invoices.py`). They import the client from `state.py`.
- **Dolibarr Client (`dolibarr_client.py`)**: Encapsulates the Dolibarr API. Handles authentication (`DOLAPIKEY`), request construction, and error mapping.
- **Models (`models.py`)**: Pydantic models representing Dolibarr entities (Project, Customer, Invoice, etc.).
- **Config (`config.py`)**: Manages environment variables and configuration.

## 6. Runtime View
1.  **Startup:** `server.py` initializes `DolibarrClient` and stores it in `state.py`.
2.  **Tool Call:** AI Agent requests a tool execution (e.g., `create_proposal`).
3.  **Validation:** FastMCP validates arguments against Pydantic models.
4.  **Execution:** The tool function retrieves the client from `state.py`.
5.  **2-Step Creation (Transactional Pattern):**
    *   **Step 1:** Tool calls `client.create_object()` (Header only).
    *   **Step 2:** Tool iterates over lines and calls `client.add_line()` for each item.
6.  **API Request:** `DolibarrClient` sends HTTP requests to Dolibarr API.
7.  **Response:** Dolibarr returns JSON.
8.  **Return:** FastMCP returns the structured result to the AI Agent.

## 7. Technical Decisions & Patterns

### 7.1 2-Step Creation Pattern
Dolibarr's REST API (v22.0.0) does **not** process line items (e.g., invoice lines) sent within the POST body of the parent object creation (e.g., `POST /invoices`). The `lines` field is ignored.
**Solution:** All creation tools (`create_proposal`, `create_order`, `create_invoice`) implement a 2-step process:
1.  Create the header object via `POST /endpoint`.
2.  Add lines individually via `POST /endpoint/{id}/lines`.

### 7.2 State Management
To avoid circular imports between the main server file (which registers tools) and tool modules (which need the client instance), a dedicated `state.py` module is used.
*   `server.py` -> imports `state` (writes client)
*   `tools/*.py` -> imports `state` (reads client)

### 7.4 Error Handling & Rollback
Since the creation of complex objects (Proposals, Orders, Invoices) involves multiple API calls (Header + N Lines), a failure during line addition could leave the system in an inconsistent state (e.g., an empty invoice).
**Solution:** The creation tools implement a rollback mechanism. If adding any line fails, the tool catches the exception, deletes the partially created header object via the API, and then re-raises the exception to the caller. This ensures atomicity of the creation operation from the user's perspective.


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
- **Universal Search Filter (USF) Syntax:** All `sqlfilters` parameters must follow Dolibarr's USF format `(field:operator:value)`, not raw SQL. See [DOLIBARR_USF_SYNTAX.md](./DOLIBARR_USF_SYNTAX.md) for complete reference.

## 10. Quality Requirements
- **Reliability:** Connection tests on startup.
- **Maintainability:** Clear separation of client and server code.
- **Type Safety:** 100% type hinted.

## 11. Risks and Technical Debt
- **Dolibarr API Versioning:** API changes in Dolibarr might break the client.
- **FastMCP Stability:** FastMCP is evolving; version pinning is recommended.

## 12. Glossary
- **MCP:** Model Context Protocol.
- **Socid/fk_soc:** Dolibarr's internal ID for Third Parties (Société ID). DB field is `fk_soc`, not `socid`.
- **Ref:** Human-readable reference (e.g., PROJ-2024-001).
- **USF:** Universal Search Filter - Dolibarr v20+ query syntax `(field:operator:value)`. See [DOLIBARR_USF_SYNTAX.md](./DOLIBARR_USF_SYNTAX.md).
