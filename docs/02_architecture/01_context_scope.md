# Kontext & Abgrenzung (Context & Scope)

**Referenz:** arc42 Kapitel 3  
**Status:** Finalisiert für MVP v1.1.0

---

## 1. Systemkontext (C4 Level 1)

```mermaid
C4Context
    title Dolibarr MCP Server – Systemkontext

    Person(user, "LLM Agent", "Claude Desktop oder andere MCP-Clients")
    System(mcp_server, "Dolibarr MCP Server", "Python FastMCP Server mit Async HTTP Client")
    System_Ext(dolibarr_api, "Dolibarr REST API", "ERP/CRM REST Endpoints (v21.0+)")
    System_Ext(env_config, "Umgebungskonfiguration", ".env, Env-Variablen, Secrets")

    Rel(user, mcp_server, "JSON-RPC über STDIO")
    Rel(mcp_server, dolibarr_api, "HTTP REST mit API-Key")
    Rel(mcp_server, env_config, "Liest Config")
    
    UpdateLayoutConfig(c4Type="C4Context", fontSize=14, margin=50)
```

### 1.1 Externe Systeme

#### **Dolibarr ERP/CRM (REST API v21.0+)**
- **Rolle:** Zentrales Geschäfts-Datensystem
- **Schnittstelle:** HTTP REST API auf `/api/index.php`
- **Authentifizierung:** `DOLAPIKEY` Header mit Benutzer-Token
- **Ressourcen:** Users, Customers, Products, Invoices, Orders, Proposals, Contacts, Projects
- **Performance:** Abhängig von Dolibarr-Instanz-Performance; üblicherweise < 500ms pro Request
- **Verfügbarkeit:** Kritisch; Server-Ausfälle führen zu MCP-Tool-Fehlern

#### **MCP Host / Claude Desktop**
- **Rolle:** Startet & kommuniziert mit MCP Server
- **Schnittstelle:** STDIO (stdin/stdout) mit JSON-RPC 2.0
- **Latenz-Anforderungen:** Tools sollten < 5 Sekunden antworten (Claude-Timeout)
- **Error-Handling:** Claude zeigt MCP-Errors in Chat-Interface

#### **Systemumgebung (.env & Secrets)**
- **Konfiguration:** `DOLIBARR_URL`, `DOLIBARR_API_KEY`, `LOG_LEVEL`
- **Scopes:** Getrennt für Development/Testing/Production
- **Security:** API-Keys dürfen nicht in Code/Logs auftauchen

---

## 2. Nutzerrollen & Usecases

### 2.1 **LLM Agent / Claude**
**Hauptnutzer des Systems**

**Usecases:**
1. „Finde einen Kunden mit der Email `john@example.com`" → `search_customers_by_email()`
2. „Erstelle eine neue Rechnung für Kunde #42" → `create_invoice()`
3. „Zeige alle offenen Bestellungen" → `search_orders_by_status()`
4. „Aktualisiere Produktbestand" → `update_product()`

**Anforderungen:**
- Schnelle Responses (< 5s)
- Klare Error-Messages
- Strukturierte Daten (JSON)
- Optimierte Tool-Katalog (nicht zu viele Tools)

### 2.2 **Dolibarr Admin**
**Konfiguriert Server & API-Zugriff**

**Aufgaben:**
- Erstellt API-Schlüssel für den MCP-Server User
- Verwaltet Berechtigungen im Dolibarr (CRUD-Limits pro Modul)
- Überwacht API-Quotas und Performance
- Konfiguriert `.env` oder Secrets im MCP Host

**Anforderungen:**
- Dokumentation für Setup & Testing
- Validation-Tools (z.B. `dolibarr-mcp test`)
- Klare Error-Messages beim falschen Setup

### 2.3 **Entwickler / Integrations-Architekt**
**Wartet Code, erweitert Tools, debuggt Issues**

**Aufgaben:**
- Schreiben von neuen Tools/Domain-Modulen
- Unit- & Integration-Tests
- Debugging von API-Fehlern
- Deployment & Monitoring

**Anforderungen:**
- Klare Architektur & Code-Conventions
- Type Hints & Docstrings (Google-Style)
- Testbarkeit (pytest mit asyncio)
- Lokales Dev-Setup (Docker, Dolibarr-Test-Instanz)

---

## 3. Schnittstellen & Abhängigkeiten

### 3.1 Externe Schnittstellen

| System | Protokoll | Authentifizierung | Fehlerbehandlung |
|--------|-----------|-------------------|-----------------|
| **Dolibarr API** | HTTP REST (JSON) | API-Key Header | HTTP-Status + Error-JSON |
| **MCP Host** | STDIO (JSON-RPC) | N/A (IPC) | JSON-RPC Error Response |
| **Environment** | Env-Vars + .env | N/A | Validation @ Startup |

### 3.2 Abhängigkeiten (Dependencies)

```
Core Runtime:
  ├─ fastmcp 2.11.3        ← MCP Server Framework
  ├─ mcp >= 1.0.0          ← MCP Protocol Library
  ├─ pydantic >= 2.5.0     ← Data Validation
  ├─ aiohttp >= 3.9.0      ← Async HTTP Client
  ├─ click >= 8.1.0        ← CLI Framework
  └─ python-dotenv         ← .env File Support

Development/Testing:
  ├─ pytest >= 7.4.0       ← Test Framework
  ├─ pytest-asyncio        ← Async Test Support
  └─ pytest-cov >= 4.1.0   ← Code Coverage
```

---

## 4. Out of Scope (MVP v1.1.0)

### ❌ Nicht implementiert (bewusst)

| Feature | Grund | Alternative |
|---------|-------|-------------|
| **Sync Support** | Komplex, Async ist besser für LLM-Latenz | Nutze async-only Codebase |
| **Multiple Dolibarr Instanzen** | Out of Scope für MVP; würde Multi-Tenancy erfordern | Pro Instance einen Server-Prozess |
| **Webhooks / Event-Streaming** | Nicht im MCP-Protocol; würde eigenen Service erfordern | REST Polling via Tools |
| **Batch-Operationen** (z.B. bulk-update) | Komplex, einzelne Operationen sind MVP-sufficient | Mehrere sequenzielle Tool-Calls |
| **Custom Dolibarr Modules** | Abhängig von Installation; zu variabel für MVP | Raw API Access via `dolibarr_raw_api` |
| **Offline Mode / Caching** | Keine Strategie für Daten-Konsistenz | Online-Only Ansatz |
| **SAML / OAuth Integration** | Dolibarr nutzt API-Keys; keine LDAPrequesta | API-Key basierte Authentifizierung |
| **Full Multi-Language** | Dokumentation in Englisch/Deutsch; UI kann LLM übersetzen | LLM-seitig mit Claude |

### ⚠️ Bewusst eingeschränkt

| Aspekt | Einschränkung | Rationale |
|--------|--------------|-----------|
| **Error Messages** | Englisch in Code, Deutsch in Docs | Standardisierung für Entwickler |
| **Logging** | Nur `logging` Modul (kein print in libs) | Production-ready Logging |
| **HTTPS Enforcement** | Empfohlen, nicht erzwungen (DEV-Setups) | Flexibilität für Testing |
| **Rate Limiting** | Keine Client-seitige Throttle; Dolibarr handles | Vereinfachtes Design |

---

## 5. Integrationspunkte (Schnittstellen im Detail)

### 5.1 HTTP-Schnittstelle zu Dolibarr

```python
# Base URL (mit oder ohne /api/index.php Normalisierung)
https://your-dolibarr.com/api/index.php

# Endpoints (Beispiele)
GET    /users
POST   /thirdparties              # Create Customer
GET    /thirdparties/{id}         # Read Customer
PUT    /thirdparties/{id}         # Update Customer
DELETE /thirdparties/{id}         # Delete Customer

GET    /products?sqlfilters=...   # Search with Filters
POST   /invoices                  # Create Invoice
```

**Headers:**
```
DOLAPIKEY: {api_key}
Content-Type: application/json
Accept: application/json
```

**Response-Format:**
```json
{
  "success": { "code": 200, "id": 123, ... },
  "error": { "code": 404, "message": "Not found" }
}
```

### 5.2 STDIO-Schnittstelle zu MCP Host

**MCP Protocol:** JSON-RPC 2.0  
**Transport:** stdin/stdout

**Tool-Call:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_customers_by_name",
    "arguments": { "name_pattern": "Acme" }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "text",
    "text": "[{\"id\": 1, \"name\": \"Acme Corp\", ...}]"
  }
}
```

### 5.3 Konfiguration via Environment

```bash
# .env File (Development)
DOLIBARR_URL=https://your-dolibarr.com/api/index.php
DOLIBARR_API_KEY=abc123...
LOG_LEVEL=INFO

# Oder direkt in Claude Desktop (claude_desktop_config.json)
{
  "mcpServers": {
    "dolibarr": {
      "env": {
        "DOLIBARR_URL": "https://...",
        "DOLIBARR_API_KEY": "..."
      }
    }
  }
}
```

---

## 6. Compliance & Security

### 6.1 Authentifizierung & Authorization
- **API-Key Auth:** Dolibarr validates API-Key in jedem Request
- **MCP-Level:** Keine zusätzliche Auth (STDIO ist IPC)
- **Scopes:** Permissions werden von Dolibarr User-Rolle gesteuert

### 6.2 Datenschutz
- **Data-in-Transit:** HTTPS nur für Production (empfohlen)
- **Secrets Management:** API-Keys in Env-Vars, nie in Code
- **Logging:** Niemals API-Keys in Logs (sanitized)

### 6.3 Fehlerbehandlung
- **Dolibarr-Fehler:** Konvertiert zu MCP-kompatiblem Error Format
- **Network-Fehler:** Timeout-Handling, Retry-Logik (einfach)
- **Validation-Fehler:** Pydantic wirft descriptive Errors

---

## 7. Performance-Anforderungen

| Aspekt | Ziel | Aktuell |
|--------|------|---------|
| Tool Response Time | < 5 Sekunden (Claude-Timeout) | 🟢 Erreicht (abhängig von Dolibarr) |
| API Requests pro Tool | 1–2 (kein N+1) | 🟢 Optimiert |
| Memory Usage | < 100 MB im Idle | ✅ Schätzung |
| Session-Startup | < 2 Sekunden | ⚠️ Abhängig von Dolibarr-Latenz |
| Large Result Sets | Pagination mit Limits | 🟢 Implementiert |

---

## 8. Abhängigkeiten & Constraints Summary

### Must-Haves (MVP)
✅ Python 3.12+  
✅ Dolibarr 21.0+ REST API  
✅ Async I/O  
✅ MCP Protocol v1.0+  
✅ API-Key Authentication  

### Nice-to-Haves
🔄 Custom Domain-Module  
🔄 Extended Error Diagnostics  
🔄 Performance Monitoring  

### Won't-Have (MVP)
❌ Webhooks / Event Streaming  
❌ Multi-Dolibarr Tenants  
❌ Sync Support  
❌ Batch Operations  

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Nächste Review:** Vor Release v2.0.0
