# Implementierungsplan & Technical Roadmap

**Referenz:** arc42 Kapitel 6 + 7  
**Status:** MVP v1.1.0

---

## 1. Überblick: Was ist implementiert?

### ✅ MVP v1.1.0 – Implementierter Scope

| Feature | Status | Details |
|---------|--------|---------|
| **CRUD-Operationen** | ✅ Vollständig | Users, Customers, Products, Invoices, Orders, Proposals, Contacts, Projects |
| **Spezialisierte Such-Tools** | ✅ Vollständig | search_customers_by_name/email, search_products_by_ref, search_projects |
| **Async HTTP Client** | ✅ Vollständig | aiohttp mit Session-Management, Timeouts, Error-Handling |
| **MCP STDIO Server** | ✅ Vollständig | FastMCP mit Tool-Registration und Lifespan-Management |
| **Configuration** | ✅ Vollständig | .env Support, Pydantic Validation, URL-Normalisierung |
| **Data Models** | ✅ Vollständig | Pydantic DTOs für alle Entities |
| **Error Handling** | ✅ Vollständig | DolibarrAPIError, Validation, Network Errors |
| **Docker Support** | ✅ Vollständig | Dockerfile + docker-compose.yml |
| **CLI Interface** | ✅ Vollständig | `python -m dolibarr_mcp serve` und `test` commands |
| **Tests** | ✅ Grundlagen | Unit & Integration Tests, pytest-asyncio |

### 🔄 Geplant (Nicht MVP)

| Feature | Status | Release | Details |
|---------|--------|---------|---------|
| Batch Operations | 🔄 Design | v2.0 | Mehrere Entities auf einmal |
| Webhooks | 🔄 Design | v2.0 | Event-basierte Notifications |
| Performance Monitoring | 🔄 Design | v1.2 | Metrics & Logging |
| Advanced Caching | 🔄 Design | v2.0 | Client-side Cache für Queries |
| Custom Modules | 🔄 Design | v2.0 | User-definierbare Tools |

---

## 2. Implementierungs-Task Checklist (MVP)

### 🟢 PHASE 1: Core Infrastructure (✅ DONE)

```
✅ 1.1 Project Setup
  ✅ Python 3.12+ venv & pyproject.toml
  ✅ Dependencies: fastmcp, mcp, pydantic, aiohttp, click
  ✅ .python-version file

✅ 1.2 CLI Interface
  ✅ __main__.py entry point
  ✅ cli.py mit click commands
  ✅ Command: python -m dolibarr_mcp serve
  ✅ Command: python -m dolibarr_mcp test

✅ 1.3 Configuration
  ✅ config.py (Pydantic BaseSettings)
  ✅ .env file support (python-dotenv)
  ✅ URL normalization + validation
  ✅ API-Key validation
  ✅ Alias support (DOLIBARR_URL, DOLIBARR_SHOP_URL, ...)
```

### 🟢 PHASE 2: HTTP Client & Models (✅ DONE)

```
✅ 2.1 Async HTTP Client
  ✅ DolibarrClient class
  ✅ aiohttp.ClientSession management
  ✅ Request building (GET, POST, PUT, DELETE)
  ✅ Response parsing & error handling
  ✅ Custom DolibarrAPIError exception
  ✅ Timeout & retry logic

✅ 2.2 Data Models
  ✅ DolibarrBaseModel (base Pydantic class)
  ✅ CustomerResult
  ✅ ProductResult
  ✅ InvoiceResult (mit InvoiceLine)
  ✅ ProjectSearchResult
  ✅ OrderResult
  ✅ ProposalResult
  ✅ ContactResult
  ✅ UserResult
  ✅ All models mit field aliases & validation

✅ 2.3 Global State
  ✅ state.py (get_client, set_client)
  ✅ Thread-safe Lock management
```

### 🟢 PHASE 3: MCP Server & Tool Registration (✅ DONE)

```
✅ 3.1 FastMCP Server
  ✅ server.py initialization
  ✅ Lifespan context manager (startup/shutdown)
  ✅ Client initialization & testing
  ✅ Tool registration from all modules

✅ 3.2 Tool Modules Registration
  ✅ tools/__init__.py exports
  ✅ register_customer_tools(mcp)
  ✅ register_product_tools(mcp)
  ✅ register_invoice_tools(mcp)
  ✅ register_order_tools(mcp)
  ✅ register_proposal_tools(mcp)
  ✅ register_project_tools(mcp)
  ✅ register_contact_tools(mcp)
  ✅ register_user_tools(mcp)
  ✅ register_system_tools(mcp)
```

### 🟢 PHASE 4: Domain Tools Implementation (✅ DONE)

```
✅ 4.1 Customer Tools (tools/customers.py)
  ✅ search_customers_by_name(pattern, limit)
  ✅ search_customers_by_email(email)
  ✅ get_customer(customer_id)
  ✅ create_customer(name, email, ...)
  ✅ update_customer(customer_id, data)
  ✅ delete_customer(customer_id)
  ✅ Google-style docstrings

✅ 4.2 Product Tools (tools/products.py)
  ✅ search_products_by_ref(ref_pattern)
  ✅ search_products_by_label(label_pattern)
  ✅ get_product(product_id)
  ✅ create_product(label, type, price, ...)
  ✅ update_product(product_id, data)
  ✅ delete_product(product_id)

✅ 4.3 Invoice Tools (tools/invoices.py)
  ✅ create_invoice(socid, lines, ...)
  ✅ get_invoice(invoice_id)
  ✅ search_invoices_by_customer(socid)
  ✅ update_invoice(invoice_id, data)
  ✅ delete_invoice(invoice_id)

✅ 4.4 Project Tools (tools/projects.py)
  ✅ search_projects_by_ref(ref_pattern)
  ✅ search_projects_by_customer(socid)
  ✅ get_project(project_id)
  ✅ create_project(title, ref, ...)
  ✅ update_project(project_id, data)
  ✅ delete_project(project_id)

✅ 4.5 Order Tools (tools/orders.py)
  ✅ create_order(socid, lines, ...)
  ✅ get_order(order_id)
  ✅ search_orders_by_customer(socid)
  ✅ update_order(order_id, data)
  ✅ delete_order(order_id)

✅ 4.6 Proposal Tools (tools/proposals.py)
  ✅ get_proposal(proposal_id)
  ✅ create_proposal(socid, lines, ...)
  ✅ get_proposals(limit)
  ✅ update_proposal(proposal_id, data)
  ✅ delete_proposal(proposal_id)

✅ 4.7 Contact Tools (tools/contacts.py)
  ✅ create_contact(lastname, firstname, socid)
  ✅ get_contact(contact_id)
  ✅ search_contacts_by_email(email)
  ✅ update_contact(contact_id, data)
  ✅ delete_contact(contact_id)

✅ 4.8 User Tools (tools/users.py)
  ✅ get_user(user_id)
  ✅ create_user(login, firstname, lastname, ...)
  ✅ get_users(limit)
  ✅ update_user(user_id, data)
  ✅ delete_user(user_id)

✅ 4.9 System Tools (tools/system.py)
  ✅ get_status()
  ✅ test_connection()
  ✅ dolibarr_raw_api(path, method, data)
```

### 🟢 PHASE 5: Testing (✅ DONE)

```
✅ 5.1 Unit Tests
  ✅ test_config.py (Config validation)
  ✅ test_dolibarr_client.py (HTTP wrapper)
  ✅ pytest-asyncio fixtures

✅ 5.2 Integration Tests
  ✅ test_fastmcp_server.py (Server startup/shutdown)
  ✅ test_crud_operations.py (Full workflows)
  ✅ test_search_tools.py (Search optimizations)
  ✅ test_usf_filters.py (SQL filter validation)

✅ 5.3 Domain-Specific Tests
  ✅ test_invoice_atomic.py
  ✅ test_project_operations.py
  ✅ test_proposal_operations.py
  ✅ test_proposal_tools.py
  ✅ test_cli.py

✅ 5.4 Test Utilities
  ✅ testing.py (fixtures, helpers)
  ✅ manual/inspect_tool.py (debug tool)
  ✅ manual/verify_server.py (connectivity check)
```

### 🟢 PHASE 6: Docker & Deployment (✅ DONE)

```
✅ 6.1 Docker Support
  ✅ Dockerfile (Python 3.12 slim)
  ✅ docker-compose.yml (Dolibarr + MCP)
  ✅ Build & run instructions
```

---

## 3. Module & Schnittstellen im Detail

### 3.1 Module: `dolibarr_client.py`

**Verantwortlichkeit:** Async HTTP Wrapper um Dolibarr REST API

**Key Methods:**
```python
class DolibarrClient:
    # Session Management
    async def start_session() → None
    async def close_session() → None
    
    # Users
    async def get_user(user_id: int) → dict
    async def create_user(data: dict) → int
    async def get_users(limit: int = 50) → list[dict]
    
    # Customers (thirdparties)
    async def get_thirdparty(id: int) → dict
    async def get_thirdparties(sqlfilters: str = "", limit: int = 50) → list[dict]
    async def create_thirdparty(data: dict) → int
    async def update_thirdparty(id: int, data: dict) → bool
    async def delete_thirdparty(id: int) → bool
    
    # Products
    async def get_product(id: int) → dict
    async def get_products(sqlfilters: str = "", limit: int = 50) → list[dict]
    async def create_product(data: dict) → int
    async def update_product(id: int, data: dict) → bool
    async def delete_product(id: int) → bool
    
    # Invoices
    async def create_invoice(data: dict) → int
    async def get_invoice(id: int) → dict
    async def get_invoices(sqlfilters: str = "") → list[dict]
    async def update_invoice(id: int, data: dict) → bool
    async def delete_invoice(id: int) → bool
    
    # Orders
    async def create_order(data: dict) → int
    async def get_order(id: int) → dict
    async def get_orders(sqlfilters: str = "") → list[dict]
    async def update_order(id: int, data: dict) → bool
    async def delete_order(id: int) → bool
    
    # Proposals
    async def create_proposal(data: dict) → int
    async def get_proposal(id: int) → dict
    async def get_proposals(limit: int = 50) → list[dict]
    async def update_proposal(id: int, data: dict) → bool
    async def delete_proposal(id: int) → bool
    
    # Projects
    async def create_project(data: dict) → int
    async def get_project(id: int) → dict
    async def get_projects(sqlfilters: str = "") → list[dict]
    async def update_project(id: int, data: dict) → bool
    async def delete_project(id: int) → bool
    
    # Contacts
    async def create_contact(data: dict) → int
    async def get_contact(id: int) → dict
    async def get_contacts(sqlfilters: str = "") → list[dict]
    async def update_contact(id: int, data: dict) → bool
    async def delete_contact(id: int) → bool
    
    # System
    async def get_status() → dict
    
    # Raw API (passthrough)
    async def raw_api(path: str, method: str, data: dict | None) → dict
```

**Error Handling:**
```python
class DolibarrAPIError(Exception):
    """Raised when Dolibarr API returns error (4xx, 5xx)."""
    def __init__(self, message: str, status_code: int, response_data: dict)
```

**Fehlerbehandlung-Strategie:**
1. Build Request
2. Send HTTP Request (timeout: 30s)
3. Check Status Code
4. If 4xx/5xx: Raise `DolibarrAPIError(message, status_code, response_data)`
5. If 2xx: Parse JSON & Return

**Testing Strategy:**
```python
# test_dolibarr_client.py
@pytest.mark.asyncio
async def test_get_customer():
    async with DolibarrClient(test_config) as client:
        result = await client.get_thirdparty(123)
        assert result["id"] == 123

# Mock-Testable: Inject config with test credentials
```

---

### 3.2 Module: `tools/customers.py`

**Verantwortlichkeit:** Spezialisierte Such- & CRUD-Tools für Customers

**Tools:**

| Tool | Input | Output | Error Cases |
|------|-------|--------|-------------|
| `search_customers_by_name` | pattern: str, limit: int | JSON: list[CustomerResult] | No matches, API error |
| `search_customers_by_email` | email: str | JSON: CustomerResult or null | Not found, API error |
| `get_customer` | customer_id: int | JSON: CustomerResult | Not found, API error |
| `create_customer` | name: str, email?: str | JSON: {id, ...} | Validation, API error |
| `update_customer` | customer_id: int, data: dict | JSON: success/failure | Not found, API error |
| `delete_customer` | customer_id: int | JSON: success | Not found, API error |

**Implementierungs-Details:**

```python
def register_customer_tools(server: FastMCP):
    @server.call_tool()
    async def search_customers_by_name(name_pattern: str, limit: int = 10) -> str:
        """Search customers by name (server-side filtered).
        
        Args:
            name_pattern: Partial name to search for (e.g., "Acme" finds "Acme Corp")
            limit: Max results to return (default 10)
            
        Returns:
            JSON string with list of customers
            
        Raises:
            RuntimeError: If client not initialized
            DolibarrAPIError: If Dolibarr API fails
        """
        client = get_client()
        
        # Server-side filter via sqlfilters
        customers = await client.get_thirdparties(
            sqlfilters=f"name LIKE '%{name_pattern}%'",
            limit=limit
        )
        
        # Validate with Pydantic
        validated = [CustomerResult(**c) for c in customers]
        
        # Return as JSON
        return json.dumps([c.model_dump() for c in validated], default=str)
```

**Error Handling:**
- `DolibarrAPIError` → MCP Error: "API Error: 404 Customer not found"
- `ValidationError` → MCP Error: "Invalid customer data: {details}"
- `RuntimeError` → MCP Error: "Client not initialized"

**SQL Filter Syntax (Dolibarr):**
```sql
-- Examples
name LIKE '%Acme%'
email = 'john@example.com'
status = 1
date_creation > 1234567890
```

---

### 3.3 Module: `tools/products.py`

**Verantwortlichkeit:** Spezialisierte Such- & CRUD-Tools für Products

**Tools:**

| Tool | Input | Output | Error Cases |
|------|-------|--------|-------------|
| `search_products_by_ref` | ref_pattern: str | JSON: list[ProductResult] | No matches, API error |
| `search_products_by_label` | label_pattern: str | JSON: list[ProductResult] | No matches, API error |
| `get_product` | product_id: int | JSON: ProductResult | Not found, API error |
| `create_product` | label: str, type: int, price: float | JSON: {id, ...} | Validation, API error |
| `update_product` | product_id: int, data: dict | JSON: success/failure | Not found, API error |
| `delete_product` | product_id: int | JSON: success | Not found, API error |

---

### 3.4 Module: `tools/invoices.py`

**Verantwortlichkeit:** Spezialisierte Invoice-Management Tools

**Tools:**

| Tool | Input | Output | Komplexität |
|------|-------|--------|------------|
| `create_invoice` | socid: int, lines: list[dict] | JSON: {id, ref, ...} | ⭐⭐⭐ |
| `get_invoice` | invoice_id: int | JSON: InvoiceResult | ⭐ |
| `search_invoices_by_customer` | socid: int | JSON: list[InvoiceResult] | ⭐ |
| `update_invoice` | invoice_id: int, data: dict | JSON: success | ⭐⭐ |
| `delete_invoice` | invoice_id: int | JSON: success | ⭐ |

**Komplexe Operation: `create_invoice`**

```python
@server.call_tool()
async def create_invoice(
    socid: int,
    lines: list[dict],
    date: int | None = None,
    note: str | None = None,
    type: int = 0
) -> str:
    """Create invoice with multiple line items.
    
    Args:
        socid: Customer ID
        lines: List of invoice lines [{desc, qty, subprice, tva_tx, ...}]
        date: Optional invoice date (timestamp)
        note: Optional note/memo
        type: Invoice type (0=Standard, 1=Credit note, ...)
        
    Returns:
        JSON with created invoice (id, ref, total_ttc, etc.)
    """
    client = get_client()
    
    # Validate lines
    validated_lines = [InvoiceLine(**line) for line in lines]
    
    # Build payload
    payload = {
        "socid": socid,
        "lines": [l.model_dump() for l in validated_lines]
    }
    
    if date:
        payload["date"] = date
    if note:
        payload["note"] = note
    if type:
        payload["type"] = type
    
    # Create
    invoice_id = await client.create_invoice(payload)
    
    # Fetch created invoice
    invoice = await client.get_invoice(invoice_id)
    
    # Validate & return
    validated = InvoiceResult(**invoice)
    return json.dumps(validated.model_dump(), default=str)
```

---

### 3.5 Module: `server.py` – Startup/Shutdown

**Verantwortlichkeit:** FastMCP Initialization & Lifespan Management

**Flow:**

```
1. User runs: python -m dolibarr_mcp serve

2. __main__.py → cli.py → cli.serve()

3. cli.serve() → mcp.run()

4. FastMCP → server_lifespan() context manager

5. server_lifespan ENTER:
   ├─ Load Config from environment
   ├─ Create DolibarrClient(config)
   ├─ client.start_session() (create aiohttp.ClientSession)
   ├─ Test connection: await client.get_status()
   ├─ set_client(client) to global state
   ├─ Register all tools (customers, products, etc.)
   └─ MCP Server listening on STDIO

6. Server receives tool calls from Claude

7. Tools execute (see tools/* details)

8. Server shutdown (Claude disconnects or user Ctrl-C)

9. server_lifespan EXIT:
   └─ await client.close_session()
```

**Logging Strategy:**
```python
import logging

logger = logging.getLogger(__name__)

async def server_lifespan(server: FastMCP):
    logger.info("Starting Dolibarr MCP Server...")
    
    # Startup
    logger.debug(f"Dolibarr URL: {config.dolibarr_url}")
    logger.info(f"✅ Connected to Dolibarr v{version}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
```

---

## 4. Error-Handling-Strategie

### 4.1 Exception Hierarchy

```python
# Base exception (library)
DolibarrAPIError(Exception)
    ├─ Status Code 4xx (Client Error)
    ├─ Status Code 5xx (Server Error)
    └─ Network Error (timeout, connection refused)

# Validation (Pydantic)
ValidationError
    └─ Field errors: {field: "reason"}

# Tool Runtime
RuntimeError
    └─ Client not initialized
```

### 4.2 Error Flow

```
Tool Called
    ↓
Try:
    Validate Input (Pydantic) →  ValidationError if invalid
    Get Client               →  RuntimeError if not set
    Call DolibarrClient      →  DolibarrAPIError if API fails
    Parse Response           →  ValidationError if format wrong
    
Except DolibarrAPIError(msg, code, data):
    Log error
    Return MCP Error: "Dolibarr API {code}: {msg}"

Except ValidationError(errors):
    Log error
    Return MCP Error: "Invalid input: {field}: {reason}"

Except Exception(e):
    Log error (with traceback)
    Return MCP Error: "Internal Error: {str(e)}"
```

### 4.3 Error Message Examples

```python
# 404 Not Found
DolibarrAPIError("Customer not found", 404, {"error": {"message": "..."}})
→ MCP Error: "API Error: Customer not found (404)"

# 401 Unauthorized
DolibarrAPIError("Invalid API Key", 401, {...})
→ MCP Error: "API Error: Invalid API Key (401)"

# Network timeout
aiohttp.ClientConnectorError("Cannot connect to host")
→ MCP Error: "Network error: Cannot connect to host"

# Validation error
Pydantic ValidationError: name [required]
→ MCP Error: "Invalid input: name is required"
```

---

## 5. Test-Strategie

### 5.1 Test Pyramid

```
        /\
       /E2E\      (Manual Tests)
      /    /\
     /Unit  \ Integration Tests
    /Tests  /\   (test_*_operations.py)
   /______/  \
  /Integration\  (test_fastmcp_server.py)
 /____Tests____\
```

### 5.2 Unit Tests (test_dolibarr_client.py)

```python
@pytest.mark.asyncio
async def test_get_customer_success():
    """Test successful customer retrieval."""
    async with DolibarrClient(test_config) as client:
        result = await client.get_thirdparty(123)
        assert result["id"] == 123
        assert "name" in result

@pytest.mark.asyncio
async def test_get_customer_not_found():
    """Test 404 error handling."""
    async with DolibarrClient(test_config) as client:
        with pytest.raises(DolibarrAPIError) as exc_info:
            await client.get_thirdparty(99999)
        assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_create_customer_validation():
    """Test input validation."""
    async with DolibarrClient(test_config) as client:
        with pytest.raises(ValidationError):
            # Missing required field
            data = {"email": "test@example.com"}  # No 'name'
            await client.create_thirdparty(data)
```

### 5.3 Integration Tests (test_crud_operations.py)

```python
@pytest.mark.asyncio
async def test_customer_create_read_update_delete():
    """Test full CRUD lifecycle."""
    async with DolibarrClient(test_config) as client:
        # Create
        customer_id = await client.create_thirdparty({
            "name": "Test Corp",
            "email": "test@example.com"
        })
        assert customer_id > 0
        
        # Read
        customer = await client.get_thirdparty(customer_id)
        assert customer["name"] == "Test Corp"
        
        # Update
        success = await client.update_thirdparty(customer_id, {
            "email": "updated@example.com"
        })
        assert success
        
        # Delete
        success = await client.delete_thirdparty(customer_id)
        assert success
```

### 5.4 Tool Tests (test_search_tools.py)

```python
@pytest.mark.asyncio
async def test_search_customers_by_name():
    """Test search tool with server-side filtering."""
    # Requires running server & Dolibarr instance
    result_json = await search_customers_by_name("Acme")
    result = json.loads(result_json)
    
    assert isinstance(result, list)
    assert len(result) <= 10  # Default limit
    if result:
        assert "Acme" in result[0]["name"]
```

### 5.5 Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_customers.py -v

# With coverage
uv run pytest --cov=src/dolibarr_mcp --cov-report=html

# Async verbose
uv run pytest tests/test_dolibarr_client.py -v -s

# Only fast unit tests (no API calls)
uv run pytest tests/test_config.py tests/test_models.py -v
```

---

## 6. Configuration & Environment Setup

### 6.1 Development Setup

```bash
# 1. Clone repo
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp

# 2. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Create .env
cat > .env << EOF
DOLIBARR_URL=https://your-dolibarr.example.com/api/index.php
DOLIBARR_API_KEY=your_api_key_here
LOG_LEVEL=DEBUG
EOF

# 5. Test connection
uv run python -m dolibarr_mcp test

# 6. Run server
uv run python -m dolibarr_mcp serve
```

### 6.2 Docker Setup

```bash
# Run with docker-compose (includes Dolibarr test instance)
docker-compose -f docker/docker-compose.yml up

# Server available at localhost:5000
# Dolibarr available at localhost:8080
```

### 6.3 Environment Variables

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `DOLIBARR_URL` | Yes | `https://dolibarr.example.com/api/index.php` | Normalized with validation |
| `DOLIBARR_API_KEY` | Yes | `abc123...` | From Dolibarr user profile |
| `LOG_LEVEL` | No | `INFO`, `DEBUG`, `WARNING` | Default: `INFO` |

---

## 7. Zukünftige Roadmap (Post-MVP)

### v1.2 (Q1 2025) – Stabilisierung
- 🔄 Performance Tuning
- 🔄 Extended Error Messages
- 🔄 Better Documentation
- 🔄 Expanded Test Coverage

### v2.0 (Q2+ 2025) – Major Features
- 🔄 Batch Operations
- 🔄 Webhooks/Events
- 🔄 Advanced Caching
- 🔄 Custom Modules Support

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Zielgruppe:** Entwickler, DevOps, Projekt-Manager
