# Kritische Analyse & Implementierungsplan: FastMCP 2.0 Migration (Update)

## 🔍 Kritische Analyse des Konzepts (Update)

### 1. **FastMCP Versioning & Stabilität**
**Risiko:** FastMCP ist in Version 2.x und entwickelt sich schnell ("Breaking changes may occur in minor versions").
**Mitigation:** Wir müssen die Version in `pyproject.toml` **pinnen** (z.B. `fastmcp==2.11.3`), um unerwartete Breaking Changes in Production zu vermeiden.

### 2. **Dependency Licensing (Cyclopts)**
**Risiko:** FastMCP nutzt Cyclopts v4 (GPL-licensed docutils dependency).
**Bewertung:** Für interne Nutzung meist unkritisch, aber für Distribution relevant.
**Lösung:** Wir nutzen Standard-Installation, da wir keine strikten License-Constraints angegeben haben. Falls nötig, Upgrade auf Cyclopts v5.

### 3. **Transport Layer (Stdio vs. HTTP)**
**Konzept:** FastMCP abstrahiert den Transport.
**Vorteil:** Wir können `mcp.run()` nutzen und via CLI entscheiden, ob wir Stdio (für Claude Desktop) oder HTTP (für Remote) nutzen wollen.
**Kritik:** Unser aktueller Code ist hardcoded auf Stdio. FastMCP macht uns flexibler, aber wir müssen sicherstellen, dass `dolibarr-mcp` CLI Command weiterhin funktioniert.

### 4. **Async Context & Lifespan**
**Herausforderung:** Unser `DolibarrClient` nutzt `aiohttp.ClientSession`, die sauber geschlossen werden muss.
**Lösung:** FastMCP bietet `@mcp.lifespan` Context Manager. Das ist **besser** als unser aktuelles manuelles Handling, muss aber korrekt implementiert werden.

### 5. **Pydantic Integration**
**Vorteil:** FastMCP nutzt Pydantic nativ.
**Kritik:** Wir müssen sicherstellen, dass unsere Models sauber definiert sind, damit die generierten JSON Schemas für den LLM verständlich sind (Descriptions sind wichtig!).

### 6. **Custom Routes (Neu)**
**Vorteil:** FastMCP unterstützt `@mcp.custom_route` für Health Checks.
**Plan:** Wir fügen einen `/health` Endpoint hinzu, wenn HTTP Transport genutzt wird.

### 7. **Strict Input Validation (Neu)**
**Option:** `strict_input_validation=False` (Default) vs `True`.
**Entscheidung:** Wir bleiben bei `False` (Default) für bessere Kompatibilität mit LLMs (Coercion von "10" -> 10), aber nutzen Pydantic Models für Type Safety.

---

## 📋 Implementierungsplan

### **Phase 1: Dependencies & Setup (10 min)**

1.  **`pyproject.toml` aktualisieren:**
    *   `fastmcp==2.11.3` hinzufügen (Pinned Version!)
    *   `mcp` Dependency prüfen (FastMCP bringt eigene mit)

2.  **Installation:**
    *   `uv sync` oder `pip install -e .` ausführen

### **Phase 2: Core Server Rewrite (45 min)**

1.  **`src/dolibarr_mcp/server.py` erstellen (NEU):**
    *   Dies wird der neue FastMCP Server.
    *   Initialisierung: `mcp = FastMCP("dolibarr-mcp", dependencies=["aiohttp", "pydantic"])`
    *   **Neu:** `lifespan` Context Manager für `DolibarrClient` Setup/Teardown.

2.  **Lifespan Manager implementieren:**
    *   Ersetzt `test_api_connection()` Context Manager.
    *   Muss `DolibarrClient` initialisieren und in `mcp.context` oder global verfügbar machen.
    *   Muss Session beim Shutdown schließen.

3.  **Models definieren (`src/dolibarr_mcp/models.py`):**
    *   Pydantic Models für `ProjectSearchResult`, `Customer`, `Invoice`, etc.
    *   Wichtig für Structured Output.

### **Phase 3: Tool Migration - Iteration 1 (30 min)**

1.  **`search_projects` migrieren:**
    *   Mit neuem `filter_customer_id`.
    *   Input Validation via Pydantic Field.

2.  **`get_customers` migrieren:**
    *   Pagination Support.

3.  **`create_invoice` migrieren:**
    *   Komplexes Beispiel mit Nested Models (`lines`).

### **Phase 4: Entry Point & CLI Anpassung (15 min)**

1.  **`src/dolibarr_mcp/cli.py` anpassen:**
    *   `serve` Command muss jetzt `mcp.run()` aufrufen.
    *   Optionen für Transport hinzufügen (Stdio default).

2.  **`__main__.py` anpassen:**
    *   Auf neuen Entry Point zeigen.

### **Phase 5: Testing & Verification (20 min)**

1.  **Unit Tests anpassen:**
    *   Tests müssen jetzt FastMCP Tools aufrufen.
    *   `fastmcp.Client` für Integration Tests nutzen? Oder direkt Funktionen testen.

2.  **Manuelle Verifikation:**
    *   `fastmcp dev src/dolibarr_mcp/server.py` nutzen.
    *   MCP Inspector prüfen.

---

## 🛑 Warte auf Bestätigung

Soll ich mit **Phase 1 (Dependencies)** und **Phase 2 (Core Server Rewrite)** beginnen?
Ich werde `dolibarr_mcp_server.py` vorerst behalten und den neuen Server parallel in `server.py` aufbauen, um nichts zu brechen.
