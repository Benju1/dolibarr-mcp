# Implementation Checklist: `search_projects` mit Filter

Basierend auf Python MCP Server Expert Guidelines.

## 🎯 Vollständige Implementierungs-Checklist

### 1️⃣ **Type Hints & Pydantic Models** (Type Safety First!)

**Status:** ⚠️ FEHLT - Aktuell nur `List[Dict[str, Any]]`

**Empfehlung:**
```python
from pydantic import BaseModel, Field

class ProjectSearchResult(BaseModel):
    """Structured project search result."""
    id: int = Field(..., description="Dolibarr project ID")
    ref: str = Field(..., description="Project reference")
    title: str = Field(..., description="Project title")
    socid: Optional[int] = Field(None, description="Associated customer ID")
    status: int = Field(..., description="Project status")
    # Weitere Fields je nach Dolibarr-Response
    
# Tool sollte zurückgeben: List[ProjectSearchResult]
```

**Warum wichtig:** 
- MCP kann automatisch Schema aus Pydantic generieren
- Type hints helfen dem Agent, die Daten zu verstehen
- Bessere IDE-Unterstützung & Fehlerbehandlung

---

### 2️⃣ **Error Handling mit Context** (Best Practice)

**Status:** ⚠️ TEILWEISE - Kein Context-Logging vorhanden

**Aktuell:**
```python
elif name == "search_projects":
    result = await client.search_projects(...)  # Keine Error-Handling!
```

**Sollte sein:**
```python
elif name == "search_projects":
    try:
        query = arguments.get("query", "").strip()
        filter_customer_id = arguments.get("filter_customer_id")
        limit = arguments.get("limit", 20)
        
        # Validierung
        if not query and not filter_customer_id:
            return TextContent(
                type="text",
                text="Warning: Empty search. Provide either 'query' or 'filter_customer_id'."
            )
        
        if limit > 100:
            limit = 100  # Cap to prevent excessive API calls
        
        filters = []
        if query:
            query_escaped = _escape_sqlfilter(query)
            filters.append(f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))")
        
        if filter_customer_id:
            filters.append(f"(t.socid:{filter_customer_id})")
        
        sqlfilters = " AND ".join(filters) if filters else ""
        result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
        
        return TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
        
    except DolibarrAPIError as e:
        return TextContent(
            type="text",
            text=f"Error searching projects: {e.message}"
        )
```

---

### 3️⃣ **Input Validation** (Robustheit)

**Status:** ❌ FEHLT - Keine Grenzen auf limit, keine Validation

**Hinzufügen:**
```python
# In Tool Definition:
"filter_customer_id": {
    "type": "integer",
    "description": "Filter by customer ID (socid)",
    "minimum": 1,  # ← Keine negativen IDs
},
"limit": {
    "type": "integer",
    "description": "Maximum number of results",
    "default": 20,
    "minimum": 1,
    "maximum": 100,  # ← Sicherheit vor DoS
},
"query": {
    "type": "string",
    "description": "Search term",
    "maxLength": 255,  # ← SQL-Injection Schutz + Performance
}
```

---

### 4️⃣ **Tests** (Test Early)

**Status:** ⚠️ TEILWEISE - Alte Tests existieren, aber nicht für neuen Filter

**Neue Tests schreiben:**
```python
@pytest.mark.asyncio
async def test_search_projects_by_customer_id(self, client):
    """Test searching projects filtered by customer."""
    with patch.object(client, 'request') as mock_request:
        mock_request.return_value = [
            {"id": 200, "ref": "PJ2401-001", "title": "Website", "socid": 135}
        ]
        
        results = await client.search_projects(
            sqlfilters="(t.socid:135)", 
            limit=20
        )
        
        assert len(results) == 1
        assert results[0]["socid"] == 135

@pytest.mark.asyncio
async def test_search_projects_combined_filters(self, client):
    """Test search with both query and customer filter."""
    with patch.object(client, 'request') as mock_request:
        mock_request.return_value = []
        
        # Simulate: Customer 135 + Query "Website"
        sqlfilters = "((t.ref:like:'%Website%') OR (t.title:like:'%Website%')) AND (t.socid:135)"
        await client.search_projects(sqlfilters=sqlfilters, limit=20)

@pytest.mark.asyncio  
async def test_search_projects_empty_filters(self, client):
    """Test empty search returns all projects."""
    with patch.object(client, 'request') as mock_request:
        mock_request.return_value = [{"id": 1}, {"id": 2}]
        
        results = await client.search_projects(sqlfilters="", limit=20)
        assert len(results) == 2
```

**Test mit `uv run mcp dev`:**
```bash
# Mit MCP Inspector testen
uv run mcp dev src/dolibarr_mcp/dolibarr_mcp_server.py

# Dann in Inspector:
# Tool: search_projects
# Input: {"filter_customer_id": 135, "limit": 20}
```

---

### 5️⃣ **Documentation** (Clear Docstrings)

**Status:** ⚠️ TEILWEISE - Tool-Beschreibung ist ok, aber könnte besser sein

**Improve Tool Description:**
```python
Tool(
    name="search_projects",
    description=(
        "Search projects by reference, title, or customer. "
        "Supports filtering by customer ID (socid). "
        "Use 'query' to search project ref/title (e.g., 'PJ2401' or 'Website'). "
        "Use 'filter_customer_id' to find all projects belonging to a specific customer. "
        "Can combine both filters. "
        "Returns matching projects with id, ref, title, and customer association."
    ),
    # ...
)
```

**Add Examples zur Tool-Beschreibung (Optional, aber hilfreich):**
```python
# Beispiele für Agent (in Docstring):
"""
Examples:
  - search_projects(query="Website") 
    → Find projects with 'Website' in ref or title
  
  - search_projects(filter_customer_id=135)
    → Find all projects of customer 135
  
  - search_projects(query="Website", filter_customer_id=135)
    → Find 'Website' projects of customer 135 only
"""
```

---

### 6️⃣ **API Reference Dokumentation** (docs/api-reference.md)

**Status:** ❌ FEHLT - API-Ref hat keine Details zu Filter-Parametern

**Hinzufügen zu docs/api-reference.md:**
```markdown
### Projects - Search Filters

#### Search by Query
```bash
GET /projects?sqlfilters=((t.ref:like:'%Website%') OR (t.title:like:'%Website%'))
```

#### Search by Customer
```bash
GET /projects?sqlfilters=(t.socid:135)
```

#### Combined Search
```bash
GET /projects?sqlfilters=((t.ref:like:'%Website%') OR (t.title:like:'%Website%')) AND (t.socid:135)
```

#### MCP Tool Usage
```python
# By customer only
search_projects(filter_customer_id=135)

# By query only
search_projects(query="Website")

# Combined
search_projects(query="Website", filter_customer_id=135, limit=50)
```
```

---

### 7️⃣ **Edge Cases & Robustheit**

**Status:** ⚠️ TEILWEISE - Nicht dokumentiert

**Prüfe diese Edge Cases:**

| Edge Case | Verhalten | Handling |
|-----------|-----------|----------|
| `query=""` + `filter_customer_id=null` | Leerer Request | ⚠️ Gibt alle Projekte zurück (ok) |
| `filter_customer_id=999` (nicht existierend) | Leeres Array | ✅ Ok - API gibt [] zurück |
| `query` mit SQL-Injection Versuch: `'; DROP TABLE projects; --` | SQL-Injection | ✅ Safe - `_escape_sqlfilter()` schützt |
| `limit=10000` | DoS-Risiko | ✅ Field validation `maximum: 100` |
| `query` mit Unicode: `"café"` | Encoding-Issue | ⚠️ Muss testen |
| `filter_customer_id=-1` (negativ) | Ungültig | ✅ Field validation `minimum: 1` |

---

### 8️⃣ **Context-Manager für Logging** (Best Practice)

**Status:** ✅ VORHANDEN - Aber nicht genutzt in search_projects Handler

**Optional verbessern:**
```python
elif name == "search_projects":
    try:
        # Validieren
        query = arguments.get("query", "").strip()
        filter_customer_id = arguments.get("filter_customer_id")
        limit = arguments.get("limit", 20)
        
        # Limitieren
        limit = min(limit, 100)
        
        # Konstruiere Filter
        filters = []
        if query:
            query_escaped = _escape_sqlfilter(query)
            filters.append(f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))")
        if filter_customer_id:
            filters.append(f"(t.socid:{filter_customer_id})")
        
        sqlfilters = " AND ".join(filters) if filters else ""
        
        # Log zur Debugging (optional, aber empfohlen)
        logging.debug(f"search_projects: query={query}, customer={filter_customer_id}, sqlfilters={sqlfilters}")
        
        result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
        
        # Strukturierte Response
        return TextContent(
            type="text",
            text=json.dumps({
                "count": len(result),
                "projects": result
            }, indent=2)
        )
        
    except DolibarrAPIError as e:
        logging.error(f"API error in search_projects: {e}")
        return TextContent(
            type="text",
            text=f"Error: {e.message}"
        )
    except Exception as e:
        logging.exception(f"Unexpected error in search_projects: {e}")
        return TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )
```

---

### 9️⃣ **Strukturierte Output** (Pydantic)

**Status:** ❌ FEHLT - Zurück gibt nur JSON-String

**Besser mit Pydantic:**
```python
from pydantic import BaseModel
from typing import List

class ProjectSearchResponse(BaseModel):
    """Structured response for project search."""
    count: int
    projects: List[dict]
    filters_applied: dict

# Dann in Handler:
response = ProjectSearchResponse(
    count=len(result),
    projects=result,
    filters_applied={
        "query": query,
        "customer_id": filter_customer_id,
        "limit": limit
    }
)

return TextContent(
    type="text",
    text=json.dumps(response.model_dump(), indent=2)
)
```

---

### 🔟 **Tool Completion Support** (Optional aber nice-to-have)

**Status:** ❌ NICHT IMPLEMENTIERT

**Falls gewünscht:** Dynamische Customer-ID Suggestions
```python
# In search_projects Tool Definition (optional):
"filter_customer_id": {
    "type": "integer",
    "description": "Filter by customer ID (socid)",
    "completion": {
        "description": "List available customer IDs",
        # → Würde Autocomplete im Client ermöglichen
    }
}
```
(Diese Feature ist MCP 2.0+, aktuell nicht Standard)

---

## 📊 Zusammenfassung: Was MUSS / SOLLTE

| # | Feature | MUSS | SOLLTE | KANN | Status |
|---|---------|------|--------|------|--------|
| 1 | Type Hints & Pydantic | ❌ | ✅ | - | Empfohlen |
| 2 | Error Handling | ✅ | ✅ | - | Kritisch |
| 3 | Input Validation | ✅ | ✅ | - | Kritisch |
| 4 | Tests | ❌ | ✅ | - | Empfohlen |
| 5 | Docstrings | ✅ | ✅ | - | Wichtig |
| 6 | API-Doku | ❌ | ✅ | - | Empfohlen |
| 7 | Edge Cases | ❌ | ✅ | - | Empfohlen |
| 8 | Logging/Context | ❌ | ✅ | - | Optional |
| 9 | Structured Output | ❌ | ✅ | - | Empfohlen |
| 10 | Completion Support | ❌ | ❌ | ✅ | Zukünftig |

---

## 🚀 Minimale Implementation (MVP)

Wenn Zeit knapp ist, diese Schritte nicht skipping:

```python
# 1. Tool Definition mit Validation
Tool(
    name="search_projects",
    description="Search projects by reference, title, or customer ID",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "maxLength": 255},
            "filter_customer_id": {"type": "integer", "minimum": 1},
            "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100}
        }
    }
)

# 2. Handler mit Error Handling
try:
    filters = []
    if arguments.get("query"):
        filters.append(f"((t.ref:like:'%{_escape_sqlfilter(arguments['query'])}%') OR (t.title:like:'%{_escape_sqlfilter(arguments['query'])}%'))")
    if arguments.get("filter_customer_id"):
        filters.append(f"(t.socid:{arguments['filter_customer_id']})")
    
    sqlfilters = " AND ".join(filters) if filters else ""
    result = await client.search_projects(sqlfilters=sqlfilters, limit=min(arguments.get("limit", 20), 100))
    return TextContent(type="text", text=json.dumps(result, indent=2))
except Exception as e:
    return TextContent(type="text", text=f"Error: {str(e)}")

# 3. Unit Test
# → test_search_projects_by_customer_id() + test_search_projects_combined()
```

---

## ✅ Recommendation Summary

**Priorität A (MUSS):**
- ✅ Input Validation (limit, customer_id Grenzen)
- ✅ Error Handling (try-except mit DolibarrAPIError)
- ✅ SQL-Injection Schutz (via _escape_sqlfilter)

**Priorität B (SOLLTE):**
- ✅ Tests schreiben (3-4 neue Tests)
- ✅ Docstring verbessern
- ✅ API-Dokumentation aktualisieren
- ✅ Logging hinzufügen

**Priorität C (KANN):**
- ✅ Pydantic Models
- ✅ Structured Output
- ✅ Completion Support
