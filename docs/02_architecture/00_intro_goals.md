# Dolibarr MCP Server – Architektur & Übersicht

**Version:** 1.1.0 (Beta)  
**Status:** Aktiv entwickelt  
**Zielgruppe:** Entwickler, System-Administratoren, Integrations-Architekten

---

## 1. Einführung und Ziele

### 1.1 Projektübersicht

**dolibarr-mcp** ist ein professioneller **Model Context Protocol (MCP)** Server, der eine umfassende Integration zwischen **Claude Desktop** (oder anderen MCP-kompatiblen Clients) und einer **Dolibarr ERP/CRM**-Instanz ermöglicht.

Der Server stellt strukturierte, optimierte **MCP-Tools** bereit, die es Claude und anderen LLM-Agenten erlauben, direkt auf Dolibarr-Daten zuzugreifen und Geschäftsprozesse zu automatisieren – ohne dass manuelle API-Integrationen notwendig sind.

**Hauptzweck:**
- Automatisierte, agentengesteuerte Integration mit Dolibarr
- Strukturierte CRUD-Operationen für alle wichtigen Geschäftsobjekte
- Optimierte Such-Tools zur Minimierung von Token-Verbrauch und Kosten
- Sichere, async HTTP-Kommunikation mit Dolibarr REST API
- Production-ready Deployment via Docker

### 1.2 Design-Philosophie

#### 1.2.1 **Spezialisierte Such-Tools** (nicht generische APIs)

Das System implementiert **spezialisierte Such-Tools** statt eines universellen `get_all_` Tools:

```
❌ Problematisch: get_customers(limit=10000) → kann zu Token-Explosion führen
✅ Besser: search_customers_by_name(pattern) → server-seitig gefiltert
```

**Vorteile:**
- **Server-seitige Filterung**: Dolibarr filtert mit SQL, nicht der Client mit Python
- **Token-Effizienz**: Claude erhält nur relevante Ergebnisse
- **Kosteneffizienz**: Weniger API-Requests, reduziertes Token-Budget
- **Bessere Performance**: Sortierung und Limits auf Datenbank-Ebene

#### 1.2.2 **Asynchrone Architektur (Async-First)**

Alle Ein-/Ausgabe-Operationen nutzen `asyncio` und `aiohttp`:
- **Non-blocking HTTP**: Mehrere Anfragen können parallel laufen
- **Session-Verwaltung**: Wiederverwendbare `aiohttp.ClientSession` für Effizienz
- **Timeout-Handling**: Robuste Fehlerbehandlung bei Netzwerkfehlern

#### 1.2.3 **Schichtenarchitektur nach Domain-Driven Design (DDD) und C4-Modell**

```
┌─────────────────────────────────────┐
│  MCP Server Layer (FastMCP)         │ ← Tool-Registrierung & STDIO
├─────────────────────────────────────┤
│  Domain Tools (src/tools/)          │ ← Business-Logic für jedes Modul
├─────────────────────────────────────┤
│  Dolibarr Client (dolibarr_client)  │ ← API-Abstraktions-Layer
├─────────────────────────────────────┤
│  Config & Models (config, models)   │ ← Settings, Pydantic-Validierung
├─────────────────────────────────────┤
│  HTTP Transport (aiohttp)           │ ← Dolibarr REST API
```

---

## 2. Randbedingungen (Constraints)

### 2.1 Technische Randbedingungen

| Randbedingung | Beschreibung | Auswirkung |
|-----------|-------------|--------|
| **Python 3.12+** | Minimale Python-Version | Nutze moderne Sprachfeatures (Type Parameters, Match-Statement) |
| **MCP Protocol v1.0+** | Offizielle MCP-Spezifikation | Tool-Signaturen und Fehlerbehandlung müssen MCP-konform sein |
| **Dolibarr 21.0+** | API-Version | REST-Endpoints und Response-Struktur basieren auf v21.0.1 |
| **Async-only** | Nur asynchroner Code in `src/` | Alle API-Aufrufe und Ein-/Ausgaben müssen asynchron sein |
| **STDIO Transport** | Einziger unterstützter Transport | Kommunikation mit Claude via JSON-RPC über stdin/stdout |

### 2.2 Funktionale Randbedingungen

- **Authentifizierung**: API-Schlüssel-basiert (DOLAPIKEY Header)
- **Fehlerbehandlung**: Alle Dolibarr-Fehler werden in MCP-kompatible Ausnahmen konvertiert
- **Validierung**: Pydantic v2.5+ erzwingt Datenvalidierung auf allen Ein-/Ausgaben
- **Konfiguration**: Umgebungsvariablen und `.env`-Datei

### 2.3 Non-Funktionale Randbedingungen

| Anforderung | Ziel | Aktueller Status |
|-----------|------|-----------------|
| **Verfügbarkeit** | Server bleibt bis zur Client-Disconnection aktiv | ✅ Implementiert |
| **Performance** | API-Response < 2 Sekunden für Such-Queries | ⚠️ Abhängig von Dolibarr-Performance |
| **Error-Recovery** | Graceful Shutdown, Session-Cleanup | ✅ Implementiert |
| **Security** | API-Keys niemals in Logs, HTTPS-only | ✅ Implementiert |
| **Documentation** | 100% Code-Coverage für public APIs | 🔄 In Arbeit |

---

## 3. Strategische Ziele (MVP & Beyond)

### Phase 1: MVP (aktuell) – v1.1.0
✅ **Kernfunktionalität**
- Alle CRUD-Operationen für: Customers, Products, Invoices, Orders, Proposals, Contacts, Projects, Users
- System-Info & Verbindungs-Tests
- Optimierte Such-Tools (Products, Customers, Projects)
- Docker-Support für Deployment
- Umfangreiche Test-Coverage

### Phase 2: Stabilisierung (Q1 2025)
🔄 **Optimierungen**
- Performance-Tuning für große Datenmengen
- Erweiterte Such-Fähigkeiten (Filter-Kombinationen, Sortiering)
- Bessere Error-Messages und Diagnostik
- Dokumentation erweitern

### Phase 3: Erweiterungen (Q2+ 2025)
📋 **Geplante Features**
- Batch-Operationen (mehrere Records auf einmal)
- Workflow-Automation (Order → Invoice → Payment)
- Webhooks für Event-Notifications
- Custom Fields Support
- Multi-Language Support

---

## 4. Stakeholder & Nutzerrollen

| Rolle | Verantwortung | Beispiele |
|------|--------------|----------|
| **LLM Agent (Claude)** | Nutzt MCP-Tools zur Automatisierung | Kundendaten abrufen, Rechnungen erstellen, Bestätigungen verschicken |
| **MCP Host** | Stellt Server-Verbindung bereit, launcht Prozess | Claude Desktop, Continue IDE, Custom Integrations |
| **Dolibarr Admin** | Konfiguriert API-Key, verwaltet Berechtigungen | Erstellt User-Token, weist Berechtigungen zu |
| **Entwickler** | Wartet Code, erweitert Tools, schreibt Tests | Integration mit neuen Dolibarr-Modulen, Custom Tools |

---

## 5. Schlüsselentscheidungen (kurz)

Siehe [03_decisions.md](03_decisions.md) für vollständige Architekturentscheidungen.

### 5.1 Spezialisierte Such-Tools statt generische APIs
**Entscheidung:** Jedes Fachbereich-Modul bietet spezialisierte Tools mit expliziter Filterung
**Begründung:** Bessere Performance, weniger Token, Kostenoptimierung

### 5.2 Asynchrone Architektur (Async-First), kein synchroner Code
**Entscheidung:** Nur `async def` für Ein-/Ausgabe-Operationen, keine `threading` oder `multiprocessing`
**Begründung:** Saubere Kontrolle über Ressourcen, bessere Performance, robuste Fehlerbehandlung

### 5.3 Schichtenarchitektur (Domain-Driven Design)
**Entscheidung:** Trennung in Tools → Client → Konfiguration/Modelle
**Begründung:** Wartbarkeit, Testbarkeit, Wiederverwendbarkeit

---

## 6. Struktur dieses Dokumentations-Projekts

Folgende Dokumente erweitern diese Übersicht:

1. **[01_context_scope.md](01_context_scope.md)** – Systemkontext, externe Abhängigkeiten, Out of Scope
2. **[02_building_blocks.md](02_building_blocks.md)** – C4 Level 2, Komponenten, Mermaid Diagramme
3. **[03_project_structure.md](03_project_structure.md)** – Folder-Layout, Verantwortlichkeiten
4. **[04_decisions.md](04_decisions.md)** – Architektur-Entscheidungen mit Alternativen (ADR-Style)
5. **[05_implementation.md](05_implementation.md)** – Implementierungsplan, Module, Error-Handling, Tests
6. **[06_risks.md](06_risks.md)** – Risiken, Abhängigkeiten, offene Fragen

**Guides** (unter `04_guides/`):
- [quickstart.md](../04_guides/quickstart.md) – Installation & erster Start
- [configuration.md](../04_guides/configuration.md) – Umgebungsvariablen & Setup
- [development.md](../04_guides/development.md) – Testing, Linting, Docker
- [api-reference.md](../04_guides/api-reference.md) – Tool-Katalog & API-Übersicht

---

## 7. Nächste Schritte

1. **Kontext & Scope verstehen** → Lese [01_context_scope.md](01_context_scope.md)
2. **Architektur erkunden** → Lese [02_building_blocks.md](02_building_blocks.md) für C4-Diagramme
3. **Code-Struktur entdecken** → Lese [03_project_structure.md](03_project_structure.md)
4. **Architekturentscheidungen analysieren** → Lese [04_decisions.md](04_decisions.md)
5. **Implementierung starten** → Folge [05_implementation.md](05_implementation.md)

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Lizenz:** MIT
