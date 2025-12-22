# Feature Request Analyse: `search_projects` mit Customer-ID

## 📋 Feature Request
`search_projects` sollte einen `filter_customer_id` (oder `filter_socid`) Parameter akzeptieren, um nach Projekten eines bestimmten Kunden zu filtern.

---

## ✅ BEWERTUNG: **FEATURE REQUEST IST SEHR SINNVOLL**

**Schweregrad:** 🔴 **HOCH**  
**Kategorie:** Design-Flaw / Missing Feature  
**Auswirkung:** Agent kann keine Kunden-Projekte filtern

---

## 🔍 Analyse des bestehenden Codes

### Aktuelle Situation

#### 1. **`search_projects` Tool** (in `dolibarr_mcp_server.py`, Zeile 1003)
```python
Tool(
    name="search_projects",
    description="Search projects by reference or title...",
    inputSchema={
        "properties": {
            "query": {"type": "string"},  # ← Nur generische Text-Suche!
            "limit": {"type": "integer", "default": 20}
        }
    }
)
```

**Problem:** Akzeptiert **nur** einen generischen `query`-Parameter.

#### 2. **Handler Implementation** (Zeile 1346)
```python
elif name == "search_projects":
    query = _escape_sqlfilter(arguments["query"])
    sqlfilters = f"((t.ref:like:'%{query}%') OR (t.title:like:'%{query}%'))"
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

**Problem:** Konstruiert nur eine `LIKE`-Filter für Ref/Title - **keine Option für Customer-Filter**.

#### 3. **Client-Methode** (in `dolibarr_client.py`, Zeile 567)
```python
async def search_projects(self, sqlfilters: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search projects using SQL filters."""
    params = {"limit": limit, "sqlfilters": sqlfilters}
    result = await self.request("GET", "projects", params=params)
```

**OK:** Client akzeptiert beliebige `sqlfilters` und leitet sie direkt an die API weiter. 
**Das ist die richtige Stelle, um Filter zu unterstützen!**

### 4. **Projekt-Struktur in Dolibarr**

Aus den Tests (z.B. `test_project_operations.py`, Zeile 47) und dem Create-Tool (Zeile 1040):
```python
{
    "id": 200,
    "ref": "PJ2401-001",
    "title": "Website Redesign",
    "socid": 1,  # ← **WICHTIG: Projekt hat `socid` Feld für Customer-ID!**
    "description": "...",
    "status": 1
}
```

**Bestätigung:** Projects in Dolibarr haben ein `socid` Feld, das die Customer-ID speichert.

---

## 🎯 Warum ist das sinnvoll?

| Punkt | Details |
|-------|---------|
| **API-Unterstützung** | Dolibarr-API unterstützt bereits `sqlfilters` mit `t.socid=X` |
| **Kunden-Projekte filtern** | Agent will häufig Projekte **eines spezifischen Kunden** sehen |
| **Konsistenz** | Andere Tools (z.B. `create_invoice`) haben auch `customer_id` Parameter |
| **Real-World Use Case** | "Zeig mir alle Projekte des Kunden 135" ist eine häufige Anfrage |
| **Low-Risk** | Erfordert **keine API-Änderungen**, nur MCP-Tool erweitern |

---

## 💡 Empfohlene Lösung

### **Variante A: Einfach (EMPFOHLEN)**

Füge `filter_customer_id` Parameter zu `search_projects` hinzu:

**Tool Definition** (MCP Server):
```python
Tool(
    name="search_projects",
    description=(
        "Search projects by reference, title, or customer. "
        "Use filter_customer_id to find all projects of a specific customer."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term for project ref or title (optional)",
            },
            "filter_customer_id": {
                "type": "integer",
                "description": "Filter by customer ID (socid) - optional",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 20,
            },
        },
        "required": [],  # Keiner zwingend erforderlich
        "additionalProperties": False,
    },
)
```

**Handler** (MCP Server):
```python
elif name == "search_projects":
    limit = arguments.get("limit", 20)
    query = arguments.get("query", "")
    filter_customer_id = arguments.get("filter_customer_id")
    
    filters = []
    
    # Wenn Query vorhanden: Ref/Title Suche
    if query:
        query_escaped = _escape_sqlfilter(query)
        filters.append(f"((t.ref:like:'%{query_escaped}%') OR (t.title:like:'%{query_escaped}%'))")
    
    # Wenn Customer-Filter vorhanden
    if filter_customer_id:
        filters.append(f"(t.socid:{filter_customer_id})")
    
    # Kombiniere Filter mit AND
    sqlfilters = " AND ".join(filters) if filters else ""
    result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

**Nutzung:**
```
Agent: "Zeig mir alle Projekte des Kunden 135"
MCP: search_projects(filter_customer_id=135)
Ergebnis: [Project1, Project2, ...]
```

---

### **Variante B: Erweitert (Optional)**

Zusätzliche nützliche Filter:
```python
"filter_customer_id": {"type": "integer"},
"filter_status": {"type": "integer"},  # z.B. 0=draft, 1=open, 2=closed
"search_in": {
    "type": "string",
    "enum": ["title", "ref", "description"],
    "default": "title"
}
```

---

## 🚀 Umsetzungsaufwand

| Komponente | Aufwand | Risiko |
|-----------|--------|--------|
| **Tool-Definition** | 5 min | Sehr niedrig |
| **Handler-Logik** | 10 min | Sehr niedrig |
| **Tests** | 15 min | Niedrig |
| **Dokumentation** | 5 min | Keine |
| **TOTAL** | ~35 min | Sehr niedrig |

**Keine API-Änderungen erforderlich** - die Dolibarr-API unterstützt bereits `socid` Filter!

---

## ⚠️ Edge Cases zu beachten

1. **Beide Parameter gesetzt** (Query + Customer-ID)  
   → Filter-Logik mit `AND` kombinieren ✓

2. **Weder Query noch Customer-ID** (leere Anfrage)  
   → Keine Filter: Gibt alle Projekte zurück (könnte auf Limit 20 setzen)

3. **Ungültige Customer-ID** (z.B. 999)  
   → Dolibarr gibt leeres Array zurück - OK ✓

4. **SQL-Injection Schutz**  
   → `filter_customer_id` ist Integer - safe ✓  
   → `query` wird via `_escape_sqlfilter()` geschützt ✓

---

## 📊 Vergleich mit bestehenden Tools

Das Pattern existiert bereits im Code:

**`create_invoice` Tool:**
```python
"customer_id": {
    "type": "integer",
    "description": "Customer ID (Dolibarr socid of the third party to invoice)"
}
```

**`create_project` Tool:**
```python
"socid": {
    "type": "integer",
    "description": "Associated company ID (thirdparty socid)"
}
```

→ **`search_projects` sollte analog sein!**

---

## ✅ Fazit

| Aspekt | Bewertung |
|--------|-----------|
| **Sinnvoll?** | ✅ JA - löst echtes Problem |
| **Machbar?** | ✅ JA - einfache Erweiterung |
| **Risky?** | ✅ NEIN - sehr sicher |
| **Priorität** | 🔴 HOCH |
| **Effort** | ⏱️ ~35 min |

**EMPFEHLUNG: Variante A umsetzen (einfacher Filter mit `filter_customer_id`)**

---

## 📝 Nächste Schritte

1. [ ] Feature implementieren (Tool + Handler)
2. [ ] Unit-Tests schreiben
3. [ ] Mit echtem Agent testen
4. [ ] Dokumentation aktualisieren
