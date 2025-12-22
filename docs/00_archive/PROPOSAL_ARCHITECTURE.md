# Architektur-Analyse: Proposals vs. Invoices

## Aktuelle Struktur

### INVOICES (Vollständig)
```
Client-Methoden:
  ✅ create_invoice()          - Neue Rechnung erstellen mit Zeilen
  ✅ get_invoices()             - Liste aller Rechnungen
  ✅ get_invoice_by_id()        - Einzelne Rechnung abrufen
  ✅ update_invoice()           - Rechnung aktualisieren
  ✅ delete_invoice()           - Rechnung löschen
  ✅ add_invoice_line()         - Zeile HINZUFÜGEN (atomic)
  ✅ update_invoice_line()      - Zeile ÄNDERN (atomic)
  ✅ delete_invoice_line()      - Zeile LÖSCHEN (atomic)
  ✅ validate_invoice()         - Entwurf validieren (workflow)
  ✅ add_payment_to_invoice()   - Zahlung hinzufügen (workflow)

MCP-Tools (10 exposed):
  ✅ create_invoice            - CREATE
  ✅ get_invoices              - LIST
  ✅ get_invoice_by_id         - READ
  ✅ update_invoice            - UPDATE
  ✅ validate_invoice          - WORKFLOW
  ✅ add_payment_to_invoice    - WORKFLOW
  (add_invoice_line, etc. sind exposed aber komplex)
```

### PROPOSALS (Minimal)
```
Client-Methoden:
  ✅ get_proposals()            - Liste aller Angebote
  ✅ get_proposal_by_id()       - Einzelnes Angebot abrufen
  ❌ create_proposal()          - FEHLT
  ❌ update_proposal()          - FEHLT
  ❌ delete_proposal()          - FEHLT
  ❌ add_proposal_line()        - FEHLT (atomic)
  ❌ update_proposal_line()     - FEHLT (atomic)
  ❌ delete_proposal_line()     - FEHLT (atomic)
  ❌ validate_proposal()        - FEHLT (workflow: Draft → Open)
  ❌ convert_proposal_to_order()- FEHLT (workflow: Proposal → Order)

MCP-Tools (2 exposed):
  ✅ get_proposals             - LIST (read-only)
  ✅ get_proposal_by_id        - READ (read-only)
```

## Das Problem

### Invoice ist CRUD + Workflow (vollständig)
- ✅ Erstellen, ändern, löschen
- ✅ Zeilen verwalten (atomar)
- ✅ Workflow-Aktionen (validieren, Zahlungen)

### Proposal ist nur READ (unvollständig)
- ❌ Kann nur LESEN
- ❌ Kann nicht erstellen/ändern
- ❌ Keine Zeilen-Verwaltung
- ❌ Keine Workflow-Aktionen

## Dolibarr REST API: Sind die Endpoints vorhanden?

Ja! Dolibarr REST API v21 hat:
```
POST   /proposals                 - Angebot erstellen
GET    /proposals                 - Liste
GET    /proposals/{id}            - Details
PUT    /proposals/{id}            - Aktualisieren
DELETE /proposals/{id}            - Löschen
POST   /proposals/{id}/lines      - Zeile hinzufügen
PUT    /proposals/{id}/lines/{lid}- Zeile ändern
DELETE /proposals/{id}/lines/{lid}- Zeile löschen
POST   /proposals/{id}/validate   - Zum Open-Status wechseln
POST   /proposals/{id}/convert    - In Bestellung konvertieren
```

## Empfehlungen

### Option A: Minimal (MVP - jetzt implementiert)
- ✅ `get_proposals()` 
- ✅ `get_proposal_by_id()`
- **Beschreibung**: "Read-only proposal access for viewing and filtering"

### Option B: Parity mit Invoices (vollständig)
Würde erfordern:
- `create_proposal()` + Test
- `update_proposal()` + Test
- `delete_proposal()` + Test
- `add_proposal_line()` + Test
- `update_proposal_line()` + Test
- `delete_proposal_line()` + Test
- `validate_proposal()` + Workflow-Test
- `convert_proposal_to_order()` + Workflow-Test

**Arbeitsaufwand**: ca. 3-4 Stunden (8-10 neue Client-Methoden, 15+ Tests)

### Option C: Hybrid (Basis-CRUD)
- `create_proposal()` + Basic fields
- `update_proposal()` + Basic fields
- `delete_proposal()`
- `validate_proposal()`
- (Zeilen-Verwaltung später)

**Arbeitsaufwand**: ca. 1-2 Stunden

## Meine Einschätzung

**Status quo ist OK für Beta**, aber:
- ✅ Konsistent mit "read-only search tools" Philosophy
- ❌ Unvollständig vs. Invoice CRUD
- ⚠️ Agent kann nur Angebote anschauen, nicht bearbeiten

**Für Production würde ich Option B (vollständig) empfehlen**, weil:
1. Dolibarr-Workflow erfordert: Angebot erstellen → validieren → konvertieren
2. Invoice ist schon "full-featured", Proposal sollte Parity haben
3. REST API ist vorhanden, nur Wrapper fehlen

---

**Sollen wir Proposals erweitern?** Oder ist das read-only für jetzt OK?
