# Risiken & Offene Punkte

**Referenz:** arc42 Kapitel 8 + Project Risk Register  
**Status:** MVP v1.1.0

---

## 1. Kritische Risiken

### ⚠️ RISIKO-001: Dolibarr API Instabilität & Kompatibilität

**Severity:** 🔴 **HIGH** (Project Blocker)  
**Probability:** Medium (20-30% für neue Dolibarr-Versionen)  
**Impact:** Tools können ausfallen, wenn API-Response-Format sich ändert

#### Beschreibung
Dolibarr ist ein komplexes ERP-System mit regelmäßigen Updates. API-Breaking-Changes können auftreten:
- Response-Struktur änderungen
- Feld-Renames oder Entfernung
- Neue Required-Fields
- Status-Code-Änderungen

**Beispiel Szenario:**
```
Dolibarr v22.0 released
Response-Format von /thirdparties ändert sich
Pydantic-Model bricht mit ValidationError
MCP Tools werden unbrauchbar
```

#### Mitigation
✅ **Implementiert:**
- Pydantic `extra="ignore"` → Unbekannte Felder ignorieren
- Field Aliases für Kompatibilität: `name = Field(alias="nom")`
- Versioning in CHANGELOG dokumentieren

🔄 **Empfohlene Maßnahmen:**
- Test gegen mehrere Dolibarr-Versionen (CI/CD)
- API-Version Pinning in Dolibarr-Instanz dokumentieren
- Early Warning System für API-Changes
- Fallback zu `raw_api()` Tool bei Problemen

#### Kontakt
**Owner:** @dolibarr-mcp-team  
**Related:** [ADR-004: Pydantic v2](04_decisions.md#adr-004-pydantic-v2-für-data-validation)

---

### ⚠️ RISIKO-002: API-Key Security & Leakage

**Severity:** 🔴 **HIGH** (Security)  
**Probability:** Medium (Developer Error)  
**Impact:** Unerlaubter Zugriff auf Dolibarr-Daten & -Systeme

#### Beschreibung
API-Keys sind sensitive Credentials. Risiken:
- API-Key in `.git` committed
- API-Key in Logs/Logs sichtbar
- API-Key im Docker Image gepacked
- Man-in-the-Middle (HTTPS nicht erzwungen)

**Beispiel Szenario:**
```
Developer lädt .env zu Git hoch → API-Key in GitHub History
Attacker findet Key → Zugriff auf Dolibarr-Instanz
```

#### Mitigation
✅ **Implementiert:**
- `.env` in `.gitignore`
- Pydantic-Validatoren checken auf Placeholder-Values
- Logging sanitization (niemals API-Key in logs)
- Config-Validierung erzwingt non-placeholder values

🔄 **Empfohlene Maßnahmen (Operations):**
- HTTPS-Only für Production (empfohlen, nicht erzwungen)
- API-Key Rotation Policy (z.B. monatlich)
- Audit Logging für API-Zugriffe in Dolibarr
- CI/CD Secret Management (GitHub Secrets, etc.)
- Pre-commit Hooks zum API-Key detektieren

#### Kontakt
**Owner:** @dolibarr-mcp-team  
**Related:** [01_context_scope.md#6-compliance--security](01_context_scope.md#6-compliance--security)

---

### ⚠️ RISIKO-003: Performance & Timeout bei großen Datenmengen

**Severity:** 🟡 **MEDIUM** (User Experience)  
**Probability:** Medium (bei großen Dolibarr-Instanzen)  
**Impact:** Tools reagieren nicht, Claude-Timeouts (5s limit)

#### Beschreibung
Dolibarr-Instanzen können mit hunderttausenden Records gefüllt sein:
- `search_products_by_label("*")` könnte 100.000 Records zurückgeben
- Network bandwidth bottleneck
- Pydantic-Validierung wird langsam
- JSON Serialisierung wird groß

**Beispiel Szenario:**
```
User: "Find all active customers"
Tool: search_customers (no pattern → matches all 50.000)
API Response: 50.000 customers × 500 bytes = 25 MB
Pydantic validation: Bottleneck
Tool timeout: > 5s
Claude: "Tool timed out"
```

#### Mitigation
✅ **Implementiert:**
- Default `limit=10` auf alle Search-Tools
- SQL-Filter auf Server-Seite (Dolibarr macht Filtering)
- Spezialisierte Tools (nicht generic get_all)

🔄 **Empfohlene Maßnahmen:**
- Paginations-Unterstützung (offset + limit in zukünftigen Versionen)
- Index-Optimierung in Dolibarr-Instanz
- Response Streaming statt Loading zu Memory
- Monitoring & Alerting für Tool-Latencies

#### Kontakt
**Owner:** @dolibarr-mcp-team  
**Related:** [ADR-001: Specialized Tools](04_decisions.md#adr-001-specialized-tools-statt-generischer-apis)

---

## 2. Operationale Risiken

### 🟡 RISIKO-004: Unvollständige Error-Handling in Edge-Cases

**Severity:** 🟡 **MEDIUM** (Debugging)  
**Probability:** Medium (unerwartete API-Responses)  
**Impact:** Kryptische Error-Messages für User

#### Beschreibung
Nicht alle Edge-Cases sind behandelt:
- Malformed JSON Response
- Unexpected HTTP Status Codes
- Partial-Success Responses (some lines fail)
- Connection Drops mid-request

**Beispiel Szenario:**
```
Tool: create_invoice mit 100 line items
Status: 400 "Invalid line 87: price too high"
Current: DolibarrAPIError("Bad Request", 400, {...})
Issue: User weiß nicht, welche Linie Problem ist
Better: "Invoice validation failed: Line 87 (price too high)"
```

#### Mitigation
✅ **Implementiert:**
- `DolibarrAPIError` mit response_data Zugriff
- Basic Error-Mapping (4xx, 5xx categories)

🔄 **Empfohlene Maßnahmen:**
- Error-Message Parsing & Enrichment
- Partial Success Handling (return what worked + what failed)
- Detailed Error Logging (traceback in DEBUG mode)
- Integration Tests für edge-cases

#### Kontakt
**Owner:** @dolibarr-mcp-team

---

### 🟡 RISIKO-005: Datenbank-Transaktionen & Konsistenz

**Severity:** 🟡 **MEDIUM** (Data Integrity)  
**Probability:** Low (mit Warnings implementiert)  
**Impact:** Inkonsistente Daten in Dolibarr

#### Beschreibung
MCP-Tools sind nicht transaktional:
- `create_invoice` mit 10 lines: Was wenn line 7 fails?
- Update mehrerer Entities: Teilweise erfolgreich, teilweise nicht
- Dolibarr Locks/Constraints können zu Race-Conditions führen
- Kein Rollback-Mechanismus

**Beispiel Szenario:**
```
Tool: create_invoice(socid=42, lines=[...10...])
Step 1: create_invoice → invoice_id=999
Step 2: add line 1-6 → Success
Step 3: add line 7 → Constraint Violation (invalid product)
Step 4: add line 8-10 → Skipped
Result: Invoice mit 6 lines statt 10
Dolibarr: Incomplete invoice in system
```

#### Mitigation
✅ **Implementiert:**
- Docstrings warnen vor Partial-Failures
- CLI Tests zeigen Limitations

🔄 **Empfohlene Maßnahmen:**
- Pre-validation vor API-Calls
- Atomic Operations wo möglich (Dolibarr nutzen)
- Batch-Rollback in v2.0 (komplexes Feature)
- Documentation klären Expectations

#### Kontakt
**Owner:** @dolibarr-mcp-team  
**Planned:** v2.0 (Batch Operations)

---

## 3. Technische Schulden

### 🟠 SCHULD-001: Begrenzte Test-Abdeckung für Domain-Tools

**Severity:** 🟠 **MEDIUM** (Quality)  
**Status:** In Arbeit  
**Effort:** Hoch

#### Problem
- Unit Tests für Tools erfordern Live Dolibarr-Instanz
- Keine Mocks für DolibarrClient verfügbar
- Integration Tests sind langsam & fragil

#### Lösung (geplant)
- Fixture-based Mocking für DolibarrClient
- Test Factory für Sample-Data
- Better Test Database Management

---

### 🟠 SCHULD-002: Dokumentation für Tool-Parameter

**Severity:** 🟠 **MEDIUM** (Documentation)  
**Status:** In Arbeit  
**Effort:** Mittel

#### Problem
- Parameter-Beschreibungen sind minimal
- Dolibarr-spezifische Constraints nicht dokumentiert
- Beispiele fehlen für komplexe Operationen

#### Lösung (geplant)
- Erweiterte Docstrings mit Constraints
- Example-Abschnitte in jedem Tool
- API Reference aus Docstrings generieren

---

### 🟠 SCHULD-003: Logging & Observability

**Severity:** 🟠 **MEDIUM** (Operations)  
**Status:** Basis implementiert  
**Effort:** Mittel

#### Problem
- Keine Structured Logging (nur basic logging module)
- Keine Metrics (Latency, Error Rates, etc.)
- Keine Tracing von MCP-Calls zu API-Calls

#### Lösung (geplant)
- Structured Logging (JSON format)
- Prometheus Metrics Integration
- OpenTelemetry Tracing

---

## 4. Bekannte Limitierungen (By Design)

### 📋 LIMITATION-001: Kein Multi-Tenant Support

**Status:** ✅ Akzeptiert  
**Rationale:** MVP-Scope  
**Workaround:** Pro Dolibarr-Instanz einen Server-Prozess

```
# Pro Instanz:
Instance A: DOLIBARR_URL=https://a.example.com → MCP Server A
Instance B: DOLIBARR_URL=https://b.example.com → MCP Server B

# Claude Host muss beide Servers registrieren:
claude_desktop_config.json:
{
  "mcpServers": {
    "dolibarr-a": {...},
    "dolibarr-b": {...}
  }
}
```

### 📋 LIMITATION-002: Synchrone API-Calls Nicht Unterstützt

**Status:** ✅ Akzeptiert  
**Rationale:** ADR-002  
**Workaround:** Alle Tools sind async (MCP Hosts müssen async unterstützen)

### 📋 LIMITATION-003: Keine Webhook-Support

**Status:** ✅ Akzeptiert  
**Rationale:** Out of Scope, würde separaten Service erfordern  
**Workaround:** Polling via `search_*` Tools

### 📋 LIMITATION-004: Batch-Operationen Fehlen

**Status:** ✅ Akzeptiert  
**Rationale:** MVP-Scope  
**Workaround:** Mehrere sequenzielle Tool-Calls

---

## 5. Offene Fragen & Decisions Pending

### ❓ OFFEN-001: Rückwärts-Kompatibilität mit älteren Dolibarr-Versionen

**Frage:** Support für Dolibarr < 21.0?  
**Status:** Entscheidung ausstehend  
**Owner:** @core-team

**Optionen:**
1. Only support 21.0+ (Current)
2. Support 19.0+ (mehr Arbeit, mehr Compat-Code)
3. Support alle recent versions mit Version Detection

**Auswirkung:** Dokumentation, Testing, Compat-Lagen

---

### ❓ OFFEN-002: Rate-Limiting & Throttling

**Frage:** Sollen Tools selbst Dolibarr-Rate-Limits respektieren?  
**Status:** Entscheidung ausstehend  
**Owner:** @core-team

**Optionen:**
1. Keine Client-seitige Throttle (Current)
2. Exponential Backoff für 429 Responses
3. Adaptive Rate-Limiting basierend auf Success-Rate

**Auswirkung:** Performance unter Last, Dolibarr-Stability

---

### ❓ OFFEN-003: Credential Rotation & Lifecycle

**Frage:** Wie werden API-Keys rotiert?  
**Status:** Entscheidung ausstehend  
**Owner:** @security-team

**Optionen:**
1. Manual Rotation (aktuell)
2. Automatic Rotation Support (komplexer)
3. Key Expiry & Warnings

**Auswirkung:** Security Posture, Operational Burden

---

## 6. Abhängigkeits-Risiken

### 📦 DEP-RISK-001: FastMCP Framework Instability

| Package | Version | Risk | Mitigation |
|---------|---------|------|------------|
| **fastmcp** | 2.11.3 | Framework Breaking Changes | Pin version, Monitor releases |
| **mcp** | ≥1.0.0 | API Instability | Use latest patch, Test updates |
| **pydantic** | ≥2.5.0 | Minor breaking in minors | Pin major.minor |
| **aiohttp** | ≥3.9.0 | Security Fixes required | Update regularly |

**Monitoring:**
```bash
# Check for security updates
uv pip audit

# Update strategy
uv sync --upgrade  # Update all dependencies
# Test in CI before merge
```

---

### 📦 DEP-RISK-002: Python Version Support

| Version | Status | EOL | Risk |
|---------|--------|-----|------|
| 3.12 | ✅ Supported | Oct 2028 | Low |
| 3.13 | ✅ Supported | Oct 2029 | Low |
| 3.14+ | 🔄 Future | Oct 2030 | Monitor |

**Mitigation:**
- Update `.python-version` regelmäßig
- CI Tests gegen min + latest Python
- Nutze `match` Statement (3.10+) → Keine Legacy

---

## 7. Risk Tracking & Monitoring

### Risk Assessment Template

```markdown
## RISIKO-NNN: [Title]

**Severity:** 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW  
**Probability:** High / Medium / Low  
**Impact:** [Description of impact]  
**Owner:** @person / @team  
**Status:** ⏰ Open / ✅ Mitigated / ❌ Accepted  

### Description
[Detailed explanation]

### Mitigation
- ✅ Already implemented
- 🔄 Recommended actions

### Related Issues
- GitHub Issue #123
- ADR-NNN
```

### Quarterly Review Checklist

- [ ] Review all open risks
- [ ] Update risk severity/probability based on recent changes
- [ ] Check mitigation effectiveness
- [ ] Promote closed/mitigated risks to "Lessons Learned"
- [ ] Identify new risks from user feedback / incidents

---

## 8. Lessons Learned (Post-Release)

*To be filled after each release*

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Nächste Review:** Nach Release v1.2  
**Zielgruppe:** Projektmanagement, DevOps, Security
