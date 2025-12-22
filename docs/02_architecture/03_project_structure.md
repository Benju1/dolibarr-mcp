# Projektstruktur & Modulverantwortlichkeiten

**Referenz:** arc42 Kapitel 4.3  
**Status:** MVP v1.1.0

---

## 1. Ordner-Layout

```
dolibarr-mcp/
│
├── src/dolibarr_mcp/                 # 📦 Main Python Package
│   │
│   ├── __init__.py                   # Package exports (DolibarrClient, Config)
│   ├── __main__.py                   # python -m dolibarr_mcp entry point
│   │
│   ├── CLI & Server
│   ├── cli.py                        # click commands: serve, test
│   ├── server.py                     # FastMCP server + lifespan management
│   │
│   ├── Configuration & Models
│   ├── config.py                     # Pydantic Settings (URL, API-Key, Log-Level)
│   ├── models.py                     # Pydantic DTOs (CustomerResult, InvoiceResult, etc.)
│   │
│   ├── API Client & State
│   ├── dolibarr_client.py            # Async HTTP wrapper (main integration point)
│   ├── state.py                      # Global client state management
│   │
│   ├── Utilities
│   ├── testing.py                    # Test fixtures & helpers
│   │
│   └── tools/                        # 🔧 Domain-Specific Tool Modules
│       ├── __init__.py               # Tool exports
│       ├── contacts.py               # Contacts CRUD tools
│       ├── customers.py              # Customers/Thirdparties search & CRUD
│       ├── invoices.py               # Invoices management
│       ├── orders.py                 # Orders management
│       ├── products.py               # Products search & CRUD
│       ├── projects.py               # Projects search & CRUD
│       ├── proposals.py              # Proposals management
│       ├── system.py                 # System status & connection tests
│       └── users.py                  # Users management
│
├── tests/                            # 🧪 Test Suite
│   │
│   ├── __init__.py
│   ├── Core Tests
│   ├── test_cli.py                   # CLI commands (serve, test)
│   ├── test_config.py                # Configuration validation
│   ├── test_dolibarr_client.py       # HTTP client & API wrapper
│   ├── test_fastmcp_server.py        # Server startup & shutdown
│   │
│   ├── Integration Tests
│   ├── test_crud_operations.py       # Generic CRUD patterns
│   ├── test_search_tools.py          # Search optimization
│   ├── test_usf_filters.py           # SQL filter validation
│   │
│   ├── Domain-Specific Tests
│   ├── test_invoice_atomic.py        # Invoice-specific operations
│   ├── test_project_operations.py    # Project-specific
│   ├── test_proposal_operations.py   # Proposal-specific
│   ├── test_proposal_tools.py        # Proposal tools
│   │
│   └── manual/                       # 📝 Manual Testing Tools
│       ├── inspect_tool.py           # Debug tool introspection
│       └── verify_server.py          # Verify server connectivity
│
├── docs/                             # 📚 Documentation
│   │
│   ├── 02_architecture/              # System Architecture (this chapter)
│   │   ├── 00_intro_goals.md         # Intro, Goals, Design Philosophy
│   │   ├── 01_context_scope.md       # Context, Scope, Out of Scope
│   │   ├── 02_building_blocks.md     # C4 Level 2, Components
│   │   ├── 03_project_structure.md   # (this file)
│   │   ├── 04_decisions.md           # Architecture Decisions (ADR)
│   │   ├── 05_implementation.md      # Implementation Plan
│   │   └── 06_risks.md               # Risks & Open Questions
│   │
│   ├── 04_guides/                    # User & Developer Guides
│   │   ├── quickstart.md             # Installation & First Run
│   │   ├── configuration.md          # Environment Variables
│   │   ├── development.md            # Testing, Linting, Docker
│   │   └── api-reference.md          # Tool Catalog & API Docs
│   │
│   ├── 00_archive/                   # Archived Documentation
│   │   └── (old docs, superseded by new structure)
│   │
│   └── README.md                     # Documentation Index
│
├── docker/                           # 🐳 Container Assets
│   ├── Dockerfile                    # Production Image (Python 3.12+)
│   └── docker-compose.yml            # Local dev stack (Dolibarr + MCP)
│
├── Configuration Files
├── pyproject.toml                    # Python package metadata & dependencies
├── .python-version                   # Python version (3.12)
├── .env.example                      # Example environment file (if present)
├── .gitignore
├── CHANGELOG.md                      # Release notes
├── LICENSE                           # MIT License
├── README.md                         # Project overview
└── .github/
    └── copilot-instructions.md       # GitHub Copilot guidelines
```

---

## 2. Modul-Verantwortlichkeiten

### 2.1 **CLI Layer** (`cli.py`, `__main__.py`)

| Datei | Verantwortlichkeit | Schnittstelle |
|-------|------------------|--------------|
| `__main__.py` | Entry point für `python -m dolibarr_mcp` | sys.argv → CLI |
| `cli.py` | click command definitions | CLI args → Server/Tests |

**Zuständig für:**
- ✅ Argument parsing (`click`)
- ✅ Environment loading (`.env` via Config)
- ✅ Starting/Stopping MCP server
- ✅ Testing API connection
- ✅ User-facing messages (print to stdout/stderr)

**NOT zuständig für:**
- ❌ Business logic
- ❌ API calls (delegieren an `DolibarrClient`)
- ❌ Logging (nur für user-messages)

**Beispiel:**
```python
# cli.py
@click.command()
@click.option("--url", envvar="DOLIBARR_URL")
@click.option("--api-key", envvar="DOLIBARR_API_KEY")
def test(url, api_key):
    """Test connection to Dolibarr."""
    config = Config(dolibarr_url=url, dolibarr_api_key=api_key)
    # ... test logic
```

---

### 2.2 **Server Layer** (`server.py`)

| Komponente | Verantwortlichkeit |
|-----------|------------------|
| `FastMCP` instance | MCP STDIO transport, tool registration |
| `server_lifespan()` | Startup & shutdown hooks |
| Tool registration | Call `register_*_tools(mcp)` for each module |

**Zuständig für:**
- ✅ Initializing FastMCP server
- ✅ Creating/managing `DolibarrClient` session
- ✅ Registering all tool modules
- ✅ Lifecycle management (startup/shutdown)
- ✅ Error handling for initialization

**NOT zuständig für:**
- ❌ Individual tool implementations
- ❌ API call logic
- ❌ Business logic

**Struktur:**
```python
@asynccontextmanager
async def server_lifespan(server: FastMCP):
    # Startup
    config = Config()
    client = DolibarrClient(config)
    await client.start_session()
    set_client(client)
    
    yield  # Server runs
    
    # Shutdown
    await client.close_session()
    set_client(None)

mcp = FastMCP("dolibarr-mcp", lifespan=server_lifespan)

# Register all tool modules
register_proposal_tools(mcp)
register_customer_tools(mcp)
# ... etc
```

---

### 2.3 **Config Layer** (`config.py`)

| Klasse | Verantwortlichkeit |
|--------|------------------|
| `Config` (Pydantic) | Load, validate, normalize settings |

**Zuständig für:**
- ✅ Reading `.env` file (python-dotenv)
- ✅ Validating environment variables (Pydantic)
- ✅ Normalizing URLs (with `/api/index.php`)
- ✅ Alias support (DOLIBARR_URL, DOLIBARR_SHOP_URL, DOLIBARR_BASE_URL)
- ✅ Placeholder detection (warn if using dummy values)

**NOT zuständig für:**
- ❌ Storing secrets securely (OS/Secrets manager responsibility)
- ❌ API key rotation

**Struktur:**
```python
class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", ...)
    
    dolibarr_url: str = Field(...)
    dolibarr_api_key: str = Field(...)
    log_level: str = "INFO"
    
    @field_validator("dolibarr_url")
    def validate_dolibarr_url(cls, v: str) -> str:
        # Normalize URL
        # Validate HTTPS requirement
        return normalized_url
```

---

### 2.4 **Models Layer** (`models.py`)

| Klasse | Verantwortlichkeit |
|--------|------------------|
| `DolibarrBaseModel` | Base for all DTOs (extra fields ignored) |
| `CustomerResult` | DTO for Customer/Thirdparty entities |
| `InvoiceResult` | DTO for Invoice entities |
| `ProductResult` | DTO for Product entities |
| `ProjectSearchResult` | DTO for Project search results |
| `OrderResult` | DTO for Order entities |
| `ProposalResult` | DTO for Proposal entities |
| `ContactResult` | DTO for Contact entities |
| `UserResult` | DTO for User entities |

**Zuständig für:**
- ✅ Type definitions for Dolibarr responses
- ✅ Field mapping (aliases für Dolibarr naming)
- ✅ Pydantic validation & coercion
- ✅ Documentation (Field descriptions)

**NOT zuständig für:**
- ❌ Business logic
- ❌ Serialization to JSON (models handle that)

**Beispiel:**
```python
class CustomerResult(DolibarrBaseModel):
    """Structured customer/thirdparty result."""
    id: int = Field(..., description="Customer ID")
    name: str = Field(..., alias="nom", description="Name")
    email: str | None = None
    phone: str | None = None
    status: int = Field(..., description="1=Active, 0=Inactive")
```

---

### 2.5 **HTTP Client** (`dolibarr_client.py`)

| Klasse | Verantwortlichkeit |
|--------|------------------|
| `DolibarrAPIError` | Custom exception for API failures |
| `DolibarrClient` | Async HTTP wrapper around Dolibarr API |

**Zuständig für:**
- ✅ Building HTTP requests (method, URL, headers, payload)
- ✅ Session management (`aiohttp.ClientSession`)
- ✅ Response parsing & error handling
- ✅ Timeout & retry logic
- ✅ CRUD operations (get_X, create_X, update_X, delete_X)
- ✅ Search/filter operations

**NOT zuständig for:**
- ❌ Business logic
- ❌ Tool logic (search_customers_by_name)
- ❌ Response formatting

**API Methods (pattern):**
```python
class DolibarrClient:
    # Get single entity
    async def get_product(id: int) -> dict
    
    # List/Search entities
    async def get_products(sqlfilters: str = "", limit: int = 50) -> list[dict]
    
    # Create entity
    async def create_product(data: dict) -> int  # returns id
    
    # Update entity
    async def update_product(id: int, data: dict) -> bool
    
    # Delete entity
    async def delete_product(id: int) -> bool
    
    # Raw API access (fallback)
    async def raw_api(path: str, method: str, data: dict | None) -> dict
```

---

### 2.6 **State Management** (`state.py`)

| Function | Verantwortlichkeit |
|----------|------------------|
| `set_client(client)` | Store client session globally |
| `get_client()` | Retrieve client session (with error if not set) |

**Zuständig für:**
- ✅ Thread-safe storage of `DolibarrClient`
- ✅ Providing client to tool modules
- ✅ Error handling if client not initialized

**NOT zuständig for:**
- ❌ Creating the client (server.py responsibility)
- ❌ Client lifecycle management

**Struktur:**
```python
_client: DolibarrClient | None = None
_lock = threading.Lock()

def set_client(client: DolibarrClient | None) -> None:
    global _client
    with _lock:
        _client = client

def get_client() -> DolibarrClient:
    with _lock:
        if not _client:
            raise RuntimeError("Client not initialized")
        return _client
```

---

### 2.7 **Tool Modules** (`tools/*.py`)

| Module | Entities | Tools |
|--------|----------|-------|
| `tools/customers.py` | Thirdparties (Customers) | search_customers, create_customer, update_customer, delete_customer |
| `tools/products.py` | Products | search_products, get_product, create_product, update_product |
| `tools/invoices.py` | Invoices | create_invoice, get_invoice, update_invoice, delete_invoice, search_invoices |
| `tools/orders.py` | Orders | create_order, get_order, update_order, delete_order |
| `tools/proposals.py` | Proposals | get_proposal, create_proposal, update_proposal, get_proposals |
| `tools/projects.py` | Projects | search_projects, get_project, create_project, update_project |
| `tools/contacts.py` | Contacts | create_contact, get_contact, update_contact, delete_contact |
| `tools/users.py` | Users | get_user, create_user, update_user, list_users |
| `tools/system.py` | System | get_status, test_connection |

**Jedes Modul:**

**Zuständig für:**
- ✅ Domain-specific tool implementations
- ✅ Specialized search tools (with server-side filtering)
- ✅ Input validation & error handling
- ✅ Response formatting (JSON string)
- ✅ Google-style docstrings

**NOT zuständig for:**
- ❌ HTTP transport (DolibarrClient handles it)
- ❌ Data model definitions (models.py)

**Struktur:**
```python
def register_customer_tools(server: FastMCP):
    """Register all customer management tools."""
    
    @server.call_tool()
    async def search_customers_by_name(name_pattern: str, limit: int = 10) -> str:
        """Search customers by name (server-side filtered).
        
        Args:
            name_pattern: Partial customer name to search for
            limit: Maximum results (default 10)
            
        Returns:
            JSON string with list of matching customers
        """
        client = get_client()
        customers = await client.get_thirdparties(
            sqlfilters=f"name LIKE '%{name_pattern}%'",
            limit=limit
        )
        return json.dumps(customers, default=str)
    
    @server.call_tool()
    async def create_customer(name: str, email: str | None = None) -> str:
        """Create a new customer.
        
        Args:
            name: Customer name
            email: Optional email address
            
        Returns:
            JSON string with created customer data
        """
        client = get_client()
        data = {"name": name}
        if email:
            data["email"] = email
        result = await client.create_thirdparty(data)
        return json.dumps(result, default=str)
```

---

### 2.8 **Testing Utilities** (`testing.py`)

| Function | Verantwortlichkeit |
|----------|------------------|
| Test fixtures | Provide mock/real clients for testing |
| Helper functions | Validate responses, create test data |

**Zuständig für:**
- ✅ Pytest fixtures (mock clients, test data)
- ✅ Common test utilities
- ✅ Sample data for testing

---

## 3. Dependency Graph

```
CLI (user input)
  ↓
cli.py (parse args, call commands)
  ↓
server.py (init FastMCP server)
  ├─ config.py (load settings)
  ├─ dolibarr_client.py (create HTTP client)
  └─ state.py (store client globally)
  ├─ tools/* (register all tools)
  │   ├─ customers.py
  │   ├─ invoices.py
  │   ├─ products.py
  │   └─ ... (all other tools)
  │
  └─ Each Tool:
      ├─ get_client() from state.py
      ├─ client.search_X() / client.create_X()
      ├─ models.py (validate response)
      └─ json.dumps() (return to MCP)
        ↓
MCP Client (Claude)
```

---

## 4. Code Ownership & Maintenance Guidelines

| Modul | Owner | Änderungs-Policy |
|-------|-------|-----------------|
| `cli.py`, `server.py` | Core Team | Breaking changes require review |
| `config.py`, `models.py` | Core Team | Backwards-compatible only |
| `dolibarr_client.py` | Core Team | API wrapper changes need testing |
| `tools/customers.py` | Feature Owner | Can add new tools freely |
| `tools/invoices.py` | Feature Owner | Can add new tools freely |
| `tools/products.py` | Feature Owner | Can add new tools freely |
| `tools/*.py` | Feature Owner | Can add new tools freely |
| `state.py`, `testing.py` | Core Team | Few changes expected |

---

## 5. Communication Patterns

### 5.1 Between Components

```
CLI 🔄 server.py
├─ Input: start_command() with config
└─ Output: STDIO start/stop signals

server.py 🔄 DolibarrClient
├─ Input: session_startup / session_shutdown
└─ Output: HTTP requests / responses

tools/* 🔄 DolibarrClient
├─ Input: Tool call with parameters
├─ DolibarrClient: API request
└─ Output: JSON response (validated)

tools/* 🔄 models.py
├─ Input: Raw API response
├─ Models: Pydantic validation
└─ Output: Typed DTO instance

Tools 🔄 state.py
├─ Input: None (get_client())
└─ Output: DolibarrClient instance
```

### 5.2 Error Flow

```
Tool Called with Invalid Data
  ↓ (Pydantic validation)
ValidationError raised
  ↓ (Tool catches)
MCP Error Response: "Invalid data: {field}: {reason}"
  ↓
Claude receives error and asks user for correction
```

---

## 6. Testing Strategy

| Test Type | Location | Scope |
|-----------|----------|-------|
| **Unit Tests** | `tests/test_*.py` | Individual functions (config, models, client methods) |
| **Integration Tests** | `tests/test_*_operations.py` | Full tool flow (input → API → output) |
| **CLI Tests** | `tests/test_cli.py` | Command-line interface |
| **Server Tests** | `tests/test_fastmcp_server.py` | Server startup/shutdown, tool registration |
| **Manual Tests** | `tests/manual/` | Interactive debugging (inspect_tool.py, verify_server.py) |

**Running Tests:**
```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_customers.py -v

# With coverage
uv run pytest --cov=src/dolibarr_mcp --cov-report=html
```

---

## 7. Schlüsselprinzipien

### ✅ Single Responsibility (Einzelne Verantwortung)
- Jedes Modul hat EINE klare Aufgabe
- Tools sind spezialisiert (nicht generisch `get_all`)
- Client verwaltet HTTP, nicht Business-Logik

### ✅ Async-First (Asynchrone Architektur)
- Alle Ein-/Ausgabe-Operationen asynchron (aiohttp, async/await)
- Keine blockierenden Aufrufe im Produktionscode
- Fixtures nutzen `pytest-asyncio` zum Testen

### ✅ Type Safety (Typ-Sicherheit)
- Type Hints auf alle öffentlichen Funktionen
- Pydantic Models für Validierung
- Google-Style Docstrings

### ✅ Fehlerbehandlung (Error Handling)
- Spezifische Exception-Typen (DolibarrAPIError, ValidationError)
- Graceful Degradation (Timeouts, Retries)
- Klare Error-Messages zum Debugging

### ✅ Testbarkeit (Testability)
- Dependency Injection (get_client aus State)
- Mock-freundliches Design
- Fixtures in testing.py

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Zielgruppe:** Entwickler, Architekten
