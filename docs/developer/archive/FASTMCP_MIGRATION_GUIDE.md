# FastMCP vs. Low-Level Server: Analyse & Migrationsstrategie

## 🔍 Aktuelle Situation

**Der Code verwendet:** Low-Level `mcp.server.Server` API  
**Sollte verwenden:** FastMCP (nach Python MCP Expert Guidelines)

```python
# Aktuell (Low-Level):
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("dolibarr-mcp")

@server.list_tools()
async def handle_list_tools():
    return [Tool(...), Tool(...)]  # Manuelle Liste bauen

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "search_products":
        ...
    elif name == "get_invoices":
        ...
    elif name == "create_customer":
        # ~1400 Zeilen riesiger elif-Switch!
        ...
```

---

## ⚖️ Vergleich: FastMCP vs. Low-Level Server

| Aspekt | Low-Level Server | FastMCP | Winner |
|--------|------------------|---------|--------|
| **Code-Zeilen** | ~1466 Zeilen | ~300-400 | 🟢 FastMCP |
| **Dekoratoren** | Manuell `@server.list_tools()` | `@mcp.tool()` pro Tool | 🟢 FastMCP |
| **Type Safety** | Manuell mit Type Hints | Automatisch aus Type Hints | 🟢 FastMCP |
| **Schema-Generierung** | Manuell JSON Schema | Automatisch aus Pydantic | 🟢 FastMCP |
| **Error Handling** | Manuell try-except | Integriert | 🟢 FastMCP |
| **Tool-Logik Pro Funktion** | Verschachtelt in elif-Chain | Eigene Funktion | 🟢 FastMCP |
| **Lesbarkeitkeit** | Schwierig (big function) | Einfach & übersichtlich | 🟢 FastMCP |
| **Testing** | Komplex | Einfach (Unit-Tests) | 🟢 FastMCP |
| **Ressourcen-Management** | Context-Manager möglich | `@mcp.lifespan()` | 🟥 Tie |
| **HTTP Support** | Nein | Ja (streamable-http) | 🟢 FastMCP |
| **Low-Level Kontrolle** | Maximum | Eingeschränkt | 🟥 Low-Level |

---

## 🎯 FastMCP-Äquivalent

### **Vorher (Low-Level, 1466 Zeilen):**

```python
from mcp.server import Server

server = Server("dolibarr-mcp")

@server.list_tools()
async def handle_list_tools():
    return [
        Tool(name="search_projects", description="...", inputSchema={...}),
        Tool(name="get_customers", description="...", inputSchema={...}),
        # ... 40+ weitere Tools manuell
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "search_projects":
        query = _escape_sqlfilter(arguments["query"])
        limit = arguments.get("limit", 20)
        sqlfilters = f"((t.ref:like:'%{query}%') OR (t.title:like:'%{query}%'))"
        result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
    elif name == "get_customers":
        result = await client.get_customers(...)
    elif name == "create_invoice":
        # ... usw, 40+ branches
    else:
        result = {"error": f"Unknown tool: {name}"}
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### **Nachher (FastMCP, ~300 Zeilen):**

```python
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional

# Initiale MCP Server
mcp = FastMCP("dolibarr-mcp")

# Datenmodelle (Type Safety)
class ProjectSearchResult(BaseModel):
    id: int = Field(..., description="Project ID")
    ref: str = Field(..., description="Project reference")
    title: str = Field(..., description="Project title")
    socid: Optional[int] = Field(None, description="Customer ID")

class CustomerResult(BaseModel):
    id: int = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer name")
    email: Optional[str] = Field(None, description="Email")

# Jedes Tool ist eine separate, dekorierte Funktion
@mcp.tool()
async def search_projects(
    query: Optional[str] = None,
    filter_customer_id: Optional[int] = None,
    limit: int = Field(20, ge=1, le=100)
) -> List[ProjectSearchResult]:
    """Search projects by reference, title, or customer.
    
    Use filter_customer_id to find all projects of a specific customer.
    Can combine both query and filter_customer_id.
    """
    filters = []
    
    if query:
        query_escaped = _escape_sqlfilter(query)
        filters.append(f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))")
    
    if filter_customer_id:
        filters.append(f"(t.socid:{filter_customer_id})")
    
    sqlfilters = " AND ".join(filters) if filters else ""
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
    
    return [ProjectSearchResult(**item) for item in result]

@mcp.tool()
async def get_customers(
    limit: int = Field(100, ge=1, le=1000),
    page: int = Field(1, ge=1)
) -> List[CustomerResult]:
    """Get paginated list of customers."""
    result = await client.get_customers(limit=limit, page=page)
    return [CustomerResult(**item) for item in result]

@mcp.tool()
async def create_invoice(
    customer_id: int = Field(..., description="Customer ID (socid)"),
    date: str = Field(..., description="Invoice date (YYYY-MM-DD)"),
    lines: List[dict] = Field(..., description="Invoice lines"),
    project_id: Optional[int] = None
) -> dict:
    """Create a new invoice."""
    payload = {
        "socid": customer_id,  # Automatische Mapping möglich
        "date": date,
        # ...
    }
    return await client.create_invoice(**payload)

# Lifespan: Server-Startup/Shutdown
@mcp.lifespan()
async def lifespan():
    """Startup und Cleanup."""
    print("🚀 Starting Dolibarr MCP server...", file=sys.stderr)
    
    # Optional: API-Verbindung testen
    config = Config()
    async with DolibarrClient(config) as client:
        status = await client.get_status()
        print("✅ Dolibarr API connection verified", file=sys.stderr)
    
    yield  # Server läuft
    
    print("👋 Server shutting down", file=sys.stderr)

# Starten
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## 📊 Code-Reduktion

| Komponente | Low-Level | FastMCP | Ersparnis |
|-----------|-----------|---------|-----------|
| Tool-Definition | 1100 Zeilen (manuelle JSON Schemas) | 200 Zeilen (Pydantic) | **82% weniger** |
| Tool-Handler | 300 Zeilen (riesiger elif-Switch) | 150 Zeilen (einzelne Funktionen) | **50% weniger** |
| Type Hints | 100 Zeilen (manuell) | 50 Zeilen (automatisch) | **50% weniger** |
| Logging/Error | 50 Zeilen | 30 Zeilen (built-in) | **40% weniger** |
| **TOTAL** | **1466 Zeilen** | **~400 Zeilen** | **🟢 73% Reduktion!** |

---

## ✅ Gründe zur Migration zu FastMCP

### 1. **Wartbarkeit** 🔧
- Jedes Tool hat eigene Funktion (nicht in riesiger elif-Chain)
- Einfacher zu lesen, zu testen, zu debuggen
- Neues Tool = eine neue Funktion + Dekorator

### 2. **Type Safety** 🛡️
```python
# FastMCP generiert Schema AUTOMATISCH aus Type Hints
@mcp.tool()
async def search_projects(
    query: Optional[str] = None,
    filter_customer_id: Optional[int] = None,
    limit: int = Field(20, ge=1, le=100)  # ← Automatische Validation!
) -> List[ProjectSearchResult]:
    ...

# ← MCP Schema wird automatisch generiert mit:
# - Type definitions
# - Required/Optional
# - Min/Max constraints (ge=1, le=100)
# - Field descriptions
```

### 3. **Strukturierte Outputs** 📦
```python
# Pydantic Models automatisch in MCP Schema konvertiert
class ProjectSearchResult(BaseModel):
    id: int
    ref: str
    title: str
    socid: Optional[int]

# Agent sieht jetzt strukturierte Daten, nicht nur JSON-String!
```

### 4. **Fehlerbehandlung** 🚨
```python
# FastMCP built-in Error Handling
@mcp.tool()
async def search_projects(...):
    try:
        ...
    except DolibarrAPIError as e:
        # FastMCP konvertiert Exception automatisch zu MCP Error
        raise  # = Clean Error Message zum Agent

# Low-Level müsste manuell TextContent mit Error JSON bauen
```

### 5. **Testing** 🧪
```python
# FastMCP Tools sind einfach zu testen
@pytest.mark.asyncio
async def test_search_projects():
    # Tool ist normale async Funktion - einfach zu mocken!
    result = await search_projects(query="Website", limit=10)
    assert len(result) > 0

# Low-Level muss komplexe Server-Mocks bauen
```

### 6. **HTTP Support** 🌐
```python
# FastMCP kann auf HTTP umgestellt werden:
mcp.run(transport="streamable-http")

# Low-Level müsste neu geschrieben werden
```

---

## ⚠️ Nachteile von FastMCP

| Nachteil | Details | Lösung |
|---------|---------|--------|
| Weniger Low-Level Kontrolle | FastMCP versteckt Details | Normalerweise nicht nötig |
| Neue Abstraktion lernen | Andere API als Low-Level | Sehr einfach zu lernen |
| Evtl. Performance | Decorator-Overhead | Negligible für MCP |

→ **Fazit:** Nachteile sind irrelevant für diesen Use Case.

---

## 🚀 Migration Plan

### **Phase 1: Vorbereitung (30 min)**
- [ ] `fastmcp` zur `requirements.txt` hinzufügen
- [ ] Pydantic Models für Response-Typen definieren
- [ ] Alte Low-Level Importe entfernen

### **Phase 2: Schrittweise Migration (2-3 Stunden)**
- [ ] `search_projects` + `get_customers` + `create_invoice` zuerst migriern
- [ ] Tests schreiben & validieren
- [ ] Dann weitere Tools in Gruppen migrieren:
  - User Management (5 Tools)
  - Customer Management (5 Tools)
  - Product Management (5 Tools)
  - Invoice Management (7 Tools)
  - Order Management (5 Tools)
  - Contact Management (5 Tools)
  - Project Management (5 Tools)
  - Raw API (1 Tool)

### **Phase 3: Finalisierung (30 min)**
- [ ] Alle Tests grün
- [ ] Mit `uv run mcp dev` validieren
- [ ] Alte Code aufräumen

---

## 💡 FastMCP Best Practices (aus Agent Guidelines)

✅ **Decorator Pattern:**
```python
@mcp.tool()  # ← Dekorator statt manuell in list_tools
async def search_projects(...):
    ...

@mcp.resource()  # ← Optional: Dynamische Resources
async def get_invoice_document(invoice_id: int):
    ...

@mcp.prompt()  # ← Optional: Wiederverwendbare Prompts
async def invoice_template():
    ...
```

✅ **Context Parameter (optional für Logging):**
```python
from fastmcp import Context

@mcp.tool()
async def search_projects(
    ctx: Context,  # ← Optional für Logging/Progress
    query: str,
    limit: int = 20
) -> List[ProjectSearchResult]:
    await ctx.info(f"Searching projects with query: {query}")
    # ...
```

✅ **Lifespan für Ressourcen-Management:**
```python
@mcp.lifespan()
async def server_lifecycle():
    # Startup
    config = Config()
    client = DolibarrClient(config)
    await client.start_session()
    
    yield  # Server läuft
    
    # Cleanup
    await client.close_session()
```

---

## 📋 Beispiel: Komplette Migration eines Tools

### **Vorher (Low-Level, ~30 Zeilen verteilt):**

```python
# In list_tools():
Tool(
    name="search_projects",
    description="Search projects by reference or title...",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term for project ref or title"},
            "limit": {"type": "integer", "description": "Maximum number of results", "default": 20},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
)

# In call_tool():
elif name == "search_projects":
    query = _escape_sqlfilter(arguments["query"])
    limit = arguments.get("limit", 20)
    sqlfilters = f"((t.ref:like:'%{query}%') OR (t.title:like:'%{query}%'))"
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

### **Nachher (FastMCP, ~15 Zeilen, übersichtlich):**

```python
from typing import Optional, List
from pydantic import BaseModel, Field

class ProjectSearchResult(BaseModel):
    id: int
    ref: str
    title: str
    socid: Optional[int] = None

@mcp.tool()
async def search_projects(
    query: str = Field(..., description="Search term for project ref or title"),
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
) -> List[ProjectSearchResult]:
    """Search projects by reference or title."""
    query_escaped = _escape_sqlfilter(query)
    sqlfilters = f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))"
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
    return [ProjectSearchResult(**item) for item in result]
```

**Ersparnis:** -15 Zeilen, +1000% Klarheit! ✨

---

## 🎯 Empfehlung

**STARK EMPFOHLEN:** Migration zu FastMCP

**Gründe:**
1. ✅ 73% Code-Reduktion
2. ✅ Bessere Wartbarkeit & Lesbarkeit
3. ✅ Type Safety automatisch
4. ✅ Einfacheres Testing
5. ✅ Zukünftig: HTTP Support möglich
6. ✅ Konsistent mit Python MCP Expert Guidelines

**Timeline:**
- Quick Win: 2-3 Tools als Proof-of-Concept (~45 min)
- Vollständig: Alle Tools (~3-4 Stunden)

**Priorisierung:**
1. `search_projects` (neu mit Filter!)
2. `search_customers`, `search_products_by_ref`
3. CRUD Operations (gruppen-weise)
4. Raw API zuletzt

---

## 🔗 Zusätzliche Ressourcen

- [FastMCP Documentation](https://github.com/jlopp/fastmcp)
- [MCP SDK Python](https://github.com/modelcontextprotocol/python-sdk)
- [Pydantic Field Validation](https://docs.pydantic.dev/latest/api/fields/)
