# Architekturentscheidungen & Varianten (ADRs)

**Referenz:** ADR (Architecture Decision Record) Pattern  
**Status:** MVP v1.1.0

---

## Übersicht

Dieses Dokument beschreibt die zentralen Architekturentscheidungen des Dolibarr MCP Servers mit:
- **Entscheidung** (was & warum)
- **Alternativen** (was wäre anders gewesen?)
- **Pro/Contra** für jede Alternative
- **Status** (akzeptiert, deprecated, etc.)

---

## ADR-001: Specialized Tools statt Generischer APIs

### Status: ✅ Akzeptiert (Core Design Pattern)

### Entscheidung

**Wir implementieren spezialisierte Tools mit expliziter Filterung** (z.B. `search_customers_by_name`, `search_products_by_ref`) **statt universeller `get_all_X` Tools.**

### Rationale

Das MCP-Server-Design bevorzugt spezialisierte Such-Tools aus mehreren Gründen:

1. **Server-seitige Filterung**: Dolibarr führt SQL-Filter aus, nicht Python
2. **Token-Effizienz**: Claude erhält nur relevante Ergebnisse (< 100 Kunden statt 10.000)
3. **Kosteneffizienz**: Weniger Daten = niedrigere API-Costs für Claude
4. **Performance**: Sortierung & Limits auf DB-Ebene, nicht im Client
5. **Clear Intent**: Tool-Name deutet bereits an, was es macht

### Beispiel

```python
# ❌ Problematisch: Generic API
@server.call_tool()
async def get_customers(limit: int = 10000) -> str:
    """Get all customers (up to limit)."""
    customers = await client.get_thirdparties(limit=limit)
    return json.dumps(customers)
    
# Problem: Claude könnte versehentlich 10.000 Kunden laden
# → Kontext-Explosion, Token-Verschwendung

# ✅ Besser: Specialized Tools
@server.call_tool()
async def search_customers_by_name(name_pattern: str, limit: int = 10) -> str:
    """Search for customers by name (server-side filtered)."""
    customers = await client.get_thirdparties(
        sqlfilters=f"name LIKE '%{name_pattern}%'",
        limit=limit
    )
    return json.dumps(customers)

@server.call_tool()
async def search_customers_by_email(email: str) -> str:
    """Find customer by email address."""
    customers = await client.get_thirdparties(
        sqlfilters=f"email = '{email}'",
        limit=1
    )
    return json.dumps(customers)
```

### Alternativen Bewertet

#### Alt A: Single Generic `get_all_*` API
```python
get_customers(limit=10000, filters: dict = {}) -> list
```
**Pro:**
- ✅ Einfache Implementierung
- ✅ Maximale Flexibilität

**Contra:**
- ❌ Claude muss selbst filtern (in Prompt-Kontext)
- ❌ Risiko: Zu viele Daten laden
- ❌ Token-Explosion
- ❌ Höhere Costs für Unternehmen
- ❌ Weniger effizient

#### Alt B: Specialized + Generic Combo
```python
search_customers_by_name(pattern)
search_customers_by_email(email)
get_all_customers(limit)  # Fallback für Edge Cases
```
**Pro:**
- ✅ Beste beider Welten
- ✅ Fallback für unvorhergesehene Cases

**Contra:**
- ⚠️ Mehr Tools im Interface
- ⚠️ Claude könnte default auf get_all_customers fallen
- ⚠️ Komplexere Wartung

#### Alt C: Filter Builder Pattern (Objekt-basiert)
```python
get_customers(filters: CustomerFilter) -> list
# Where CustomerFilter = {name?: str, email?: str, status?: int}
```
**Pro:**
- ✅ Flexible Kombinationen
- ✅ Skalbar für neue Filter

**Contra:**
- ❌ Komplizierte API
- ❌ Claude braucht das Typ-Schema
- ❌ Mehr Prompt-Engineering erforderlich
- ❌ Nicht MCP-optimal

### ✅ Entscheidung: Alt A (Specialized Only)

**Implementiert in:** `tools/customers.py`, `tools/products.py`, `tools/projects.py`

**Zitat aus README.md:**
> „Design Philosophy: This server implements **specialized search tools** instead of a single unified `get_` tool."

---

## ADR-002: Async-Only Architecture (Kein Sync-Code)

### Status: ✅ Akzeptiert (Technical Requirement)

### Entscheidung

**Nur asynchrone I/O-Operationen** (`async def`), **keine synchronen oder threaded Operationen** für HTTP-Calls.

### Rationale

1. **Non-blocking**: Mehrere Requests können parallel laufen
2. **Resource-Efficient**: Tausende von offenen Connections mit kleinem Memory-Footprint
3. **MCP-Latency**: STDIO-basierte RPCs brauchen schnelle I/O
4. **Sauberer Code**: `async/await` ist klarer als `threading` oder `multiprocessing`
5. **Error-Handling**: Timeouts & Cancellation sind mit async leichter

### Beispiel: async/await Pattern

```python
# Tool implementiert async
@server.call_tool()
async def create_invoice(socid: int, lines: list[dict]) -> str:
    """Create invoice (async operation)."""
    client = get_client()
    
    # Await all I/O
    invoice_id = await client.create_invoice({
        "socid": socid,
        "lines": lines
    })
    
    # Fetch related data in parallel
    invoice, customer = await asyncio.gather(
        client.get_invoice(invoice_id),
        client.get_thirdparty(socid)
    )
    
    return json.dumps({"invoice": invoice, "customer": customer})
```

### Alternativen Bewertet

#### Alt A: Sync-Only (Standard Requests)
```python
import requests

@server.call_tool()
def get_customer(customer_id: int) -> str:
    """Get customer (BLOCKING)."""
    response = requests.get(f".../{customer_id}")
    return json.dumps(response.json())
```
**Pro:**
- ✅ Einfacher zu verstehen
- ✅ Weniger boilerplate

**Contra:**
- ❌ **BLOCKING**: While waiting for HTTP, server can't handle other requests
- ❌ Single-threaded = one request at a time
- ❌ Höhere Latenz für Claude
- ❌ MCP nicht optimal
- ❌ Scaling-Problem

#### Alt B: Mix aus Sync & Async
```python
# Manche Tools sind async, manche sync
async def search_products(...):
    ...

def get_status():
    return requests.get(...).json()
```
**Pro:**
- ✅ Flexibility wo Sync OK ist

**Contra:**
- ❌ **Kompliziert**: Inconsistent API
- ❌ Debugging-Albtraum
- ❌ Error-Handling unterschiedlich
- ❌ Testing Nightmare

#### Alt C: Async + Thread Pool für Blocking Calls
```python
import concurrent.futures

@server.call_tool()
async def get_customer(customer_id: int) -> str:
    """Get customer (async wrapper über blocking code)."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        requests.get,
        f".../{customer_id}"
    )
    return json.dumps(result.json())
```
**Pro:**
- ✅ Legacy Code funktioniert
- ✅ Backwards compatible

**Contra:**
- ❌ Performance-Killer: Thread-Overhead
- ❌ Versteckt das Problem (Sync Code in Async Wrapper)
- ❌ Nicht scalable

### ✅ Entscheidung: Async-Only (Alt A)

**Implementiert mit:**
- `aiohttp.ClientSession` für HTTP
- `async def` für alle I/O-Operationen
- `asyncio.gather()` für parallele Requests
- `pytest-asyncio` für Async Tests

**Konsequenzen:**
- ✅ Schnelle, non-blocking MCP Server
- ✅ Saubere, wartbare Code-Basis
- ✅ Skalierbar für große Workloads

---

## ADR-003: Schichtenarchitektur nach DDD Principles

### Status: ✅ Akzeptiert (Organizational Pattern)

### Entscheidung

**Wir strukturieren den Code in klare Schichten:**
1. **Tool Layer** (Domain Logic) – `tools/*.py`
2. **Client Layer** (API Adapter) – `dolibarr_client.py`
3. **Config/Model Layer** (Data & Settings) – `config.py`, `models.py`
4. **HTTP Layer** (Transport) – `aiohttp`

### Rationale

1. **Separation of Concerns**: Jede Schicht hat ONE Verantwortlichkeit
2. **Testability**: Tools können mit Mock-Client getestet werden
3. **Maintainability**: Changes in API-Format isoliert auf `DolibarrClient`
4. **Reusability**: Client kann in anderen Projekten genutzt werden
5. **DDD-aligned**: Domain-Entities im Center, Infrastructure outside

### Schichten-Diagramm

```
┌──────────────────────────────────────┐
│ MCP Host (Claude)                    │
└────────────────┬─────────────────────┘
                 │ JSON-RPC STDIO
┌────────────────┴─────────────────────┐
│ MCP Server (FastMCP)                 │
├──────────────────────────────────────┤
│ DOMAIN LAYER (tools/*)               │  ← Business Logic
│ - search_customers_by_name()          │
│ - create_invoice()                    │
│ - search_products_by_ref()            │
├──────────────────────────────────────┤
│ ADAPTER LAYER (DolibarrClient)       │  ← API Abstraction
│ - get_thirdparties(sqlfilters)        │
│ - create_invoice(data)                │
│ - search_products(sqlfilters)         │
├──────────────────────────────────────┤
│ CONFIG/MODEL LAYER                   │  ← Data Contracts
│ - Config (URL, API-Key)               │
│ - CustomerResult, InvoiceResult, ...  │
├──────────────────────────────────────┤
│ HTTP LAYER (aiohttp)                 │  ← Transport
└────────────────┬─────────────────────┘
                 │ HTTP REST
        ┌────────┴──────────┐
        │  Dolibarr API     │
        │  /users           │
        │  /thirdparties    │
        │  /products        │
        │  /invoices        │
        └───────────────────┘
```

### Alternativen Bewertet

#### Alt A: Fat Client (Everything in DolibarrClient)
```python
class DolibarrClient:
    # Hunderte von Methoden
    async def search_customers_by_name(pattern)
    async def search_customers_by_email(email)
    async def create_invoice_with_lines(...)
    # ...
```
**Pro:**
- ✅ Einfach zu starten

**Contra:**
- ❌ **God Object**: DolibarrClient wird riesig
- ❌ Schwer zu testen (alles in einem Modul)
- ❌ Schwer zu warten
- ❌ Tools & Client vermischt
- ❌ Keine Domain-Abstraktions

#### Alt B: Flat Structure (No Layers)
```
src/
  get_customers()
  create_invoice()
  search_products()
  # Alle in root, kein klares Pattern
```
**Pro:**
- ✅ Minimal initial setup

**Contra:**
- ❌ Keine Struktur → schnell chaotisch
- ❌ Reusability = 0 (alles MCP-tools gebunden)
- ❌ Testing difficult (alles vermischt)
- ❌ Keine Separation

#### Alt C: Heavy OOP (Entity Objects)
```python
class Customer:
    id: int
    name: str
    
    async def save(self): ...
    async def delete(self): ...
    
class Invoice:
    ...
```
**Pro:**
- ✅ OOP-Like
- ✅ Business Logic in Objects

**Contra:**
- ❌ Zu komplexvür diesen Use-Case
- ❌ Active Record Pattern → schwer zu testen
- ❌ Overkill für MCP-Tools
- ❌ Nicht async-freundlich

### ✅ Entscheidung: DDD Layered Architecture (Alt A)

**Vorteile für dolibarr-mcp:**
- ✅ Klare Verantwortlichkeiten
- ✅ Tools fokussieren auf Domain Logic
- ✅ DolibarrClient kann in anderen Projekten genutzt werden
- ✅ Easy Testing: Mock DolibarrClient in tools tests
- ✅ Future-proof: API-Changes isoliert auf Client

---

## ADR-004: Pydantic v2 für Data Validation

### Status: ✅ Akzeptiert (Technical Choice)

### Entscheidung

**Nutze Pydantic v2.5+ für:**
- Konfiguration (Settings in `config.py`)
- Response-Validierung (Models in `models.py`)

### Rationale

1. **Type Safety**: Type hints werden zur Runtime überprüft
2. **Performance**: Pydantic v2 ist schneller als v1
3. **DX**: Clear error messages für ungültige Daten
4. **Validation**: Custom validators für Business-Rules
5. **Serialization**: `.model_dump()` & `.model_dump_json()`

### Beispiel: Config Validation

```python
from pydantic import BaseSettings, field_validator

class Config(BaseSettings):
    dolibarr_url: str
    dolibarr_api_key: str
    
    @field_validator("dolibarr_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("URL must use HTTPS")
        return v
    
    @field_validator("dolibarr_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if "dummy" in v.lower():
            raise ValueError("Use real API key, not dummy placeholder")
        return v

# Usage
config = Config()  # Reads from .env & Environment
# If invalid: ValidationError mit klarem Message
```

### Alternativen Bewertet

#### Alt A: Manual Validation (No Pydantic)
```python
def load_config():
    url = os.getenv("DOLIBARR_URL")
    api_key = os.getenv("DOLIBARR_API_KEY")
    
    if not url:
        raise ValueError("DOLIBARR_URL missing")
    if not url.startswith("https://"):
        raise ValueError("URL must use HTTPS")
    
    return {"url": url, "api_key": api_key}
```
**Pro:**
- ✅ Keine externe Dependencies

**Contra:**
- ❌ Viel boilerplate
- ❌ Fehleranfällig
- ❌ Keine Type-Hints at Runtime
- ❌ Custom-Validatoren schwer zu schreiben

#### Alt B: Dataclasses (Python 3.10+)
```python
from dataclasses import dataclass

@dataclass
class Config:
    dolibarr_url: str
    dolibarr_api_key: str
    # Keine Built-in Validation
```
**Pro:**
- ✅ Python Standard Library
- ✅ Lightweight

**Contra:**
- ❌ **Keine Validation**: Must manually validate
- ❌ JSON Serialization awkward
- ❌ .env Integration manual
- ❌ Type checking at runtime nicht möglich

#### Alt C: Config Files (YAML/TOML)
```yaml
# config.yaml
dolibarr:
  url: https://...
  api_key: xxx
```
**Pro:**
- ✅ Human readable
- ✅ Non-code configuration

**Contra:**
- ❌ Noch eine Datei zu verwalten
- ❌ Environment Variables nicht Standard
- ❌ Deployment komplizierter
- ❌ Docker unfriendly (Secrets in Env Vars besser)

### ✅ Entscheidung: Pydantic v2 (Alt A)

**Implementiert in:**
- `config.py`: `Config(BaseSettings)` mit .env Support
- `models.py`: Response DTOs mit Validation

**Benefits:**
- ✅ Type-safe
- ✅ Clear error messages
- ✅ Built-in Serialization
- ✅ Easy Testing (create models in tests)

---

## ADR-005: Global State via Function (Nicht Singleton Class)

### Status: ✅ Akzeptiert (Testability Pattern)

### Entscheidung

**Nutze Module-Level Functions (`get_client()`, `set_client()`) statt Singleton-Klasse** für Global State.

### Rationale

1. **Simple**: `get_client()` ist einfacher als `ClientManager.instance().get_client()`
2. **Testable**: Easy to mock in tests
3. **Thread-safe**: Nutze `threading.Lock()` statt complex patterns
4. **Python Idiom**: Standard way to handle global state in Python

### Beispiel: `state.py`

```python
import threading

_client: DolibarrClient | None = None
_lock = threading.Lock()

def set_client(client: DolibarrClient | None) -> None:
    """Set global client (call from server.py on startup)."""
    global _client
    with _lock:
        _client = client

def get_client() -> DolibarrClient:
    """Get global client (call from tools)."""
    with _lock:
        if not _client:
            raise RuntimeError("Client not initialized. Did you start the server?")
        return _client
```

### Alternativen Bewertet

#### Alt A: Dependency Injection (Keine Globals)
```python
# server.py
client = DolibarrClient(config)
register_tools(mcp, client)

# tools/customers.py
def register_customer_tools(mcp, client):
    @mcp.call_tool()
    async def search_customers_by_name(name_pattern: str) -> str:
        customers = await client.search_customers(...)
```
**Pro:**
- ✅ Sehr testbar
- ✅ Keine globalen Variablen
- ✅ Explizit wo client kommt

**Contra:**
- ❌ Alle register_X_tools() Signaturen müssen (mcp, client) akzeptieren
- ❌ Server.py wird kompliziert (muss client zu allen weitergeben)
- ❌ FastMCP hat constraints für Tool-Registration

#### Alt B: Singleton Class
```python
class ClientManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClientManager()
        return cls._instance
    
    def get_client(self):
        return self._client

# Usage: ClientManager.get_instance().get_client()
```
**Pro:**
- ✅ Pattern-based approach

**Contra:**
- ❌ Boilerplate
- ❌ Overkill für einfachen Use-Case
- ❌ Less Pythonic
- ❌ Testing erfordert Singleton.reset()

#### Alt C: Context Variable (asyncio.contextvars)
```python
from contextvars import ContextVar

_client_context: ContextVar[DolibarrClient] = ContextVar("client")

def set_client(client: DolibarrClient) -> None:
    _client_context.set(client)

def get_client() -> DolibarrClient:
    return _client_context.get()
```
**Pro:**
- ✅ Async-native
- ✅ Task-local storage

**Contra:**
- ⚠️ Overkill (nur ein Client global, nicht pro-task)
- ⚠️ Komplexer zu verstehen
- ⚠️ Less standard approach

### ✅ Entscheidung: Global Functions mit Lock (Alt A)

**Implementiert in:** `state.py`

**Why:**
- ✅ Simple & clear
- ✅ Thread-safe
- ✅ Easy to mock in tests
- ✅ Minimal boilerplate

---

## Summary: Alle Entscheidungen

| ADR | Titel | Status | Key Decision |
|-----|-------|--------|--------------|
| **ADR-001** | Specialized Tools | ✅ Akzeptiert | `search_customers_by_name` statt `get_all_customers` |
| **ADR-002** | Async-Only | ✅ Akzeptiert | `async def` everywhere, kein sync Code |
| **ADR-003** | DDD Layers | ✅ Akzeptiert | Tools → Client → Config/Models → HTTP |
| **ADR-004** | Pydantic v2 | ✅ Akzeptiert | Data Validation mit Type Safety |
| **ADR-005** | Global State | ✅ Akzeptiert | `get_client()` function mit threading.Lock |

---

## Deprecated Decisions (Future)

🔮 **Mögliche zukünftige Entscheidungen (nicht für MVP):**

- **Batch Operations**: Mehrere Invoices auf einmal erstellen
- **Webhooks**: Event-basierte Notifications statt Polling
- **Caching**: Client-side Caching für häufige Queries
- **Multi-Tenant**: Support für mehrere Dolibarr Instanzen
- **Custom Modules**: User-definierbare Tools laden

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Review-Cycle:** Nach jedem Major Release
