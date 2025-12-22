# Architektur-Analyse: FastMCP 2.0 Migration - Was wiederverwendbar ist

## 🏗️ Deine aktuelle Architektur

```
src/dolibarr_mcp/
├── dolibarr_client.py          ← Business Logic Layer (Dolibarr API Client)
├── dolibarr_mcp_server.py      ← MCP Framework Layer (Low-Level Server)
├── config.py                   ← Configuration Management
├── cli.py                      ← Command Line Interface
├── __main__.py                 ← Entry Point
├── test_connection.py          ← Testing
└── testing.py                  ← Testing Utilities
```

---

## ✅ Was KANN/SOLLTE wiederverwendet werden

### 1. **`dolibarr_client.py`** → 100% WIEDERVERWENDBAR ✅

**Status:** Framework-agnostisch  
**Grund:** Ist der Business Logic Layer, nicht MCP-spezifisch

```python
# dolibarr_client.py ist pure Python - unabhängig vom MCP-Framework
class DolibarrClient:
    async def search_projects(self, sqlfilters: str, limit: int = 20):
        """Diese Methode funktioniert mit Low-Level Server UND FastMCP"""
        return await self.request("GET", "projects", params=params)
    
    async def create_invoice(self, data: Dict):
        """Diese Methode bleibt gleich"""
        return await self.request("POST", "invoices", data=data)
```

**Was zu tun:**
- ✅ Behalten wie es ist
- ✅ Nur minimal anpassen (z.B. neue `filter_customer_id` Parameter in `search_projects`)
- ✅ Unit-Tests weiterverwenden

**Zeilen:** ~600 Zeilen → 100% Reuse

---

### 2. **`config.py`** → 95% WIEDERVERWENDBAR ✅

**Status:** Rein Pydantic-basiert, Framework-agnostisch

```python
# config.py braucht keine Änderung für FastMCP
class Config(BaseSettings):
    dolibarr_url: str
    dolibarr_api_key: str
    log_level: str
```

**Was zu tun:**
- ✅ Behalten wie es ist
- Optional: Neue Fields hinzufügen (z.B. `enable_http_transport: bool = False`)

**Zeilen:** ~180 Zeilen → 100% Reuse (oder mit 5 Zeilen Erweiterung)

---

### 3. **`cli.py`** → 90% WIEDERVERWENDBAR ✅

**Status:** Nur der `serve` Command ändert sich leicht

```python
# Aktuell (Low-Level):
@cli.command()
def serve():
    asyncio.run(server_main())  # ← Nur diese Zeile ändert sich!

# Mit FastMCP:
@cli.command()
def serve():
    asyncio.run(server_main())  # ← Exakt die gleiche Zeile!
    # (server_main() wird in dolibarr_mcp_server.py neu geschrieben,
    #  aber CLI braucht kein Update)
```

**Was zu tun:**
- ✅ Behalten wie es ist
- Optional: Neue CLI Optionen (`--transport stdio|http`, `--stateless`)

**Zeilen:** ~57 Zeilen → 100% Reuse

---

### 4. **`test_connection.py` & `testing.py`** → 80% WIEDERVERWENDBAR ✅

**Status:** Testing-Utilities sind framework-agnostisch

```python
# Diese können behalten werden
async def test_connection(url: str, api_key: str):
    async with DolibarrClient(config) as client:
        status = await client.get_status()
        return status
```

**Was zu tun:**
- ✅ Behalten wie es ist
- ✅ Evtl. neue Tests für FastMCP-spezifische Features

**Zeilen:** ~100 Zeilen → 100% Reuse

---

### 5. **`__main__.py`** → 100% WIEDERVERWENDBAR ✅

**Status:** Entry Point ist framework-agnostisch

**Zeilen:** ~20 Zeilen → 100% Reuse

---

## ❌ Was MUSS neu geschrieben werden

### **`dolibarr_mcp_server.py`** → 0% WIEDERVERWENDBAR ❌

**Status:** Framework-spezifisch (Low-Level Server API)

**Was ist aktuell:**
- 1466 Zeilen
- Verwendet: `@server.list_tools()`, `@server.call_tool()`, `if-elif` Chain
- Manuell: JSON Schemas, Error Handling, Type Hints

**Was wird neu:**
- ~400-500 Zeilen mit FastMCP
- Verwendet: `@mcp.tool()` Dekoratoren, Pydantic Models
- Automatisch: Schema-Generierung, Type Safety, Error Handling

**Was zu tun:**
- 🔄 Komplett mit FastMCP umschreiben (aber sehr viel einfacher!)
- ✅ Code-Struktur aber deutlich klarer

---

## 📊 Wiederverwendungs-Übersicht

| Datei | Zeilen | Wiederverwendbar | Aufwand |
|-------|--------|------------------|---------|
| `dolibarr_client.py` | ~600 | ✅ 100% | ➡️ Nur Minor Tweaks |
| `config.py` | ~180 | ✅ 95% | ➡️ Optional erweitern |
| `cli.py` | ~57 | ✅ 90% | ➡️ Keine Änderung nötig |
| `test_connection.py` | ~50 | ✅ 80% | ➡️ Kompatibel |
| `testing.py` | ~50 | ✅ 80% | ➡️ Kompatibel |
| `__main__.py` | ~20 | ✅ 100% | ➡️ Keine Änderung nötig |
| **`dolibarr_mcp_server.py`** | **~1466** | **❌ 0%** | **🔄 Komplett neu** |
| **TOTAL** | **~2400** | **✅ 91%** | **Pragmatisch!** |

---

## 🎯 Strategischer Ansatz: **REWRITE, DON'T REBUILD**

### **Was bedeutet das?**

**Nicht:**
```
"Ich schreibe das komplette Projekt neu"
→ Unnötige Arbeit, Fehler-Anfälligkeit
```

**Sondern:**
```
"Ich schreibe nur dolibarr_mcp_server.py um"
→ Alles andere bleibt, getestet & funktionierend
```

### **Konkrete Struktur nach Migration:**

```
src/dolibarr_mcp/
├── dolibarr_client.py          ✅ UNVERÄNDERT (600 Zeilen)
├── dolibarr_mcp_server.py      🔄 UMGESCHRIEBEN (1466 → 450 Zeilen)
├── config.py                   ✅ UNVERÄNDERT (180 Zeilen)
├── cli.py                      ✅ UNVERÄNDERT (57 Zeilen)
├── __main__.py                 ✅ UNVERÄNDERT (20 Zeilen)
├── test_connection.py          ✅ UNVERÄNDERT (50 Zeilen)
└── testing.py                  ✅ UNVERÄNDERT (50 Zeilen)
```

---

## 🚀 Migration Roadmap

### **Phase 1: Vorbereitung (30 min)**
```bash
# 1. FastMCP zum Projekt hinzufügen
pip install fastmcp

# 2. Pydantic Models definieren (separate Datei optional)
src/dolibarr_mcp/models.py  ← NEW (100 Zeilen mit alle Response-Typen)
```

### **Phase 2: Server-Rewrite (3-4 Stunden)**

**Approach:** Nicht alle 40+ Tools auf einmal - sondern **schrittweise**

```
Iteration 1 (30 min): POC mit 3 Tools
  ✅ search_projects (neu mit filter!)
  ✅ get_customers
  ✅ create_invoice

Iteration 2 (45 min): User Management
  ✅ get_users, get_user_by_id, create_user, update_user, delete_user

Iteration 3 (45 min): Product Management
  ✅ get_products, get_product_by_id, create_product, update_product, delete_product

Iteration 4 (45 min): Invoice Management
  ✅ get_invoices, create_invoice_draft, add_invoice_line, validate_invoice, etc.

Iteration 5 (30 min): Restliche Tools + Raw API
```

### **Phase 3: Testing & Validation (30 min)**
```bash
# Validieren mit MCP Inspector
uv run mcp dev src/dolibarr_mcp/dolibarr_mcp_server.py

# Existierende Unit-Tests sollten noch passen
pytest tests/ -v
```

### **Phase 4: Cleanup (15 min)**
```bash
# Alte Low-Level Imports entfernen
# Code formatieren
# Documentation aktualisieren
```

---

## 💡 Praktisches Beispiel: Was sich ändert

### **Tool: `search_projects` mit neuem Filter**

#### **Aktuell (Low-Level):**
```python
# In list_tools() (~20 Zeilen):
Tool(
    name="search_projects",
    description="Search projects by reference or title",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
)

# In call_tool() (~10 Zeilen):
elif name == "search_projects":
    query = _escape_sqlfilter(arguments["query"])
    limit = arguments.get("limit", 20)
    sqlfilters = f"((t.ref:like:'%{query}%') OR (t.title:like:'%{query}%'))"
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

#### **Mit FastMCP (neu):**
```python
# Eine Funktion mit Dekorator (~15 Zeilen):
@mcp.tool()
async def search_projects(
    query: Optional[str] = None,
    filter_customer_id: Optional[int] = None,
    limit: int = Field(20, ge=1, le=100)
) -> List[ProjectSearchResult]:
    """Search projects by reference, title, or customer."""
    filters = []
    
    if query:
        query_escaped = _escape_sqlfilter(query)
        filters.append(f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))")
    
    if filter_customer_id:
        filters.append(f"(t.socid:{filter_customer_id})")
    
    sqlfilters = " AND ".join(filters) if filters else ""
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
    
    return [ProjectSearchResult(**item) for item in result]
```

**Änderungen:**
- ✅ Neue `filter_customer_id` Parameter hinzufügen
- ✅ Weniger Code (Dekoratoren machen Schema-Generierung)
- ✅ Type Safe (Pydantic validation)
- ✅ Struktuierte Output (`ProjectSearchResult`)

---

## ✅ Fazit & Empfehlung

### **NICHT komplett neu schreiben:**
```
❌ Backup des ganzen Projekts
❌ Von Grund auf neu anfangen
❌ Alle Dateien rewrite
```

### **SONDERN strategisch umbauen:**
```
✅ dolibarr_client.py behalten
✅ Alle anderen Module behalten
✅ NUR dolibarr_mcp_server.py rewrite (mit FastMCP)
✅ Schrittweise iterieren (nicht alles auf einmal)
✅ Bestehende Tests weiterverwenden
```

### **Effizient & Sicher:**
- 🎯 91% Code wiederverwendbar
- 🚀 Schneller als Komplett-Rewrite
- 🛡️ Weniger Fehler (bestehender Code bleibt getestet)
- 📈 Inkrementelle Verbesserungen

### **Aufwand-Schätzung:**
| Phase | Zeit | Ergebnis |
|-------|------|----------|
| Setup | 30 min | FastMCP installiert, Models definiert |
| POC | 30 min | 3 Tools funktionieren mit FastMCP |
| Alle Tools | 2-3h | Komplette Migration |
| Testing | 30 min | Alles getestet & validiert |
| **TOTAL** | **~4 Stunden** | **Production-Ready** |

---

## 🎯 Nächste Schritte

**Wenn du diesen Weg gehst:**

1. `models.py` erstellen (Pydantic Models für alle Response-Typen)
2. `dolibarr_mcp_server.py` Kopie als Backup
3. FastMCP Skeleton schreiben (Entry Point + Lifespan)
4. POC mit 3 Tools testen (`uv run mcp dev`)
5. Remaining Tools gruppeneweise rewrite
6. Alte `dolibarr_mcp_server.py` löschen

**Zeit sparen:** Tools in dieser Priorität migrieren:
1. Search Tools (search_projects, search_customers, etc.)
2. CRUD in dieser Reihenfolge: Customer → Product → Invoice → Order → Project → User → Contact
3. Raw API zuletzt
