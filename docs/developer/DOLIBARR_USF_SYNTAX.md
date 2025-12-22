# Dolibarr Universal Search Filter (USF) Syntax

> **Status:** Definitive Reference für dolibarr-mcp
> **Dolibarr Version:** v20+ (API Breaking Change)
> **Last Updated:** 2025-12-22

## Übersicht

Die Dolibarr REST API (v20+) akzeptiert **nicht** frei-formbares SQL, sondern eine spezifische Query-Filter-Syntax: das **Universal Search Filter (USF)** Format.

Das ist ein häufiger Fehler und führt zu **HTTP 400 "Bad syntax of the search string"** Fehlern.

---

## ✅ Korrekte USF-Syntax

### Format
```
(field:operator:value)
```

### Komponenten
| Teil | Bedeutung | Beispiel |
|------|-----------|----------|
| `field` | Dolibarr-Datenbankfeld mit Tabellen-Alias | `t.socid`, `t.fk_soc`, `t.ref` |
| `operator` | USF-Operator (nicht Standard-SQL) | `=`, `:=:`, `like:` |
| `value` | Filter-Wert, bei `like:` mit Wildcards | `135`, `'Carlos'`, `'%proj%'` |

### Beispiele

#### Exakte Übereinstimmung
```
(t.fk_soc:=:135)
```
Filtert Projekte mit `fk_soc = 135`

#### Like-Filter (Text-Suche)
```
(t.ref:like:'%PRJ%')
```
Filtert Projekte, deren Referenz `PRJ` enthält

```
(t.title:like:'%Software%')
```
Filtert Projekte mit „Software" im Titel

#### Mehrere Filter kombinieren
```
(t.fk_soc:=:135) and (t.ref:like:'%PRJ%')
```
Logisches UND: Kunde 135 UND Referenz enthält „PRJ"

---

## ❌ Häufige Fehler

### Fehler 1: Standard-SQL-Syntax verwenden
```
❌ FALSCH:  (t.socid=135)
✅ RICHTIG: (t.fk_soc:=:135)
```

Die API erwartet **Doppelpunkte** um den Operator: `:=:` (nicht nur `=`)

### Fehler 2: Falscher Feldname
```
❌ FALSCH:  (t.socid=135)
✅ RICHTIG: (t.fk_soc:=:135)
```

Für die Project-Klasse ist der korrekte Feldname **`fk_soc`** (nicht `socid`).
Die JSON-API-Parameter sind nicht 1:1 mit DB-Spalten identisch.
→ Siehe [Dolibarr Doxygen: Project Class](https://doxygen.dolibarr.org/dolibarr_19.0/build/html/d9/d6e/class_project.html)

### Fehler 3: Fehlende/falsche Operator-Syntax
```
❌ FALSCH:  (t.socid = 135)
❌ FALSCH:  (t.socid:=135)
✅ RICHTIG: (t.fk_soc:=:135)
```

Der Operator muss **von beiden Seiten mit Doppelpunkten umgeben** sein: `:=:` (nicht `:=`)

### Fehler 4: Like-String ohne Wildcards
```
❌ FALSCH:  (t.title:like:'Software')
✅ RICHTIG: (t.title:like:'%Software%')
```

Bei `like:` muss der String SQL-Wildcards (`%`) enthalten.

### Fehler 5: Zitate falsch
```
❌ FALSCH:  (t.ref:like:%test%)
✅ RICHTIG: (t.ref:like:'%test%')
```

Text-Werte **immer in Einfach-Anführungszeichen** setzen.

---

## 📋 Operator-Referenz

| Operator | Syntax | Beispiel | Bedeutung |
|----------|--------|---------|-----------|
| Gleich | `:=:` | `(t.socid:=:135)` | Exakte Übereinstimmung |
| Like | `:like:` | `(t.ref:like:'%PRJ%')` | Text-Suche mit Wildcards |
| Greater Than | `:>:` | `(t.datec:>:'2024-01-01')` | > |
| Less Than | `:<:` | `(t.datec:<:'2024-12-31')` | < |

---

## 🔧 Dolibarr-Feldnamen (häufige Fehler)

Manche API-Parameter maps nicht 1:1 auf DB-Spalten:

### Project-Klasse
| Konzept | DB-Spalte | USF-Feldname | Beschreibung |
|---------|-----------|-------------|--------------|
| Kunde-ID | `fk_soc` | `t.fk_soc` | **NICHT** `socid`! |
| Projekt-Ref | `ref` | `t.ref` | Projekt-Referenz |
| Titel | `title` | `t.title` | Projekt-Name |

### Customer-Klasse (Dolibarr: "Societe")
| Konzept | DB-Spalte | USF-Feldname |
|---------|-----------|-------------|
| Name | `nom` | `t.nom` |
| Alias | `name_alias` | `t.name_alias` |

---

## 💡 Best Practices in dolibarr-mcp

### ✅ Sanitization

Immer `_sanitize_search()` verwenden:
```python
def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection."""
    s = s.strip()
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]
```

Dann USF mit sanitized Input:
```python
query_sanitized = _sanitize_search(query)
sqlfilters = f"(t.ref:like:'%{query_sanitized}%')"
```

### ✅ Multi-Filter bauen

```python
filters = []

if query:
    query_sanitized = _sanitize_search(query)
    filters.append(f"(t.ref:like:'%{query_sanitized}%')")

if filter_customer_id:
    filters.append(f"(t.fk_soc:=:{int(filter_customer_id)})")

sqlfilters = " and ".join(filters) if filters else ""
result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

### ✅ Debugging

Wenn API-Error: **immer die `sqlfilters` inspizieren:**
```python
logger.debug(f"Generated sqlfilters: {sqlfilters}")
```

---

## 🔗 Quellen & Referenzen

1. **Dolibarr Wiki:** [Universal Search Filter Syntax](https://wiki.dolibarr.org/index.php/Universal_Search_Filter_Syntax)
2. **Dolibarr Forum:** [Issue in Dolibarr 20 - Using my Dolibarr](https://www.dolibarr.org/forum/t/issue-in-dolibarr-20/29437)
3. **Dolibarr Doxygen:** [Project Class Reference](https://doxygen.dolibarr.org/dolibarr_19.0/build/html/d9/d6e/class_project.html)

---

## 📝 Zusammenfassung für Entwickler

| Punkt | Details |
|-------|---------|
| **Syntax** | `(field:operator:value)` mit `:` statt `=` |
| **Like-Operator** | `:like:` mit `%` Wildcards: `(t.ref:like:'%test%')` |
| **Gleichheit** | `:=:` ohne Quotes bei Zahlen: `(t.fk_soc:=:135)` |
| **Kombination** | `" and "` (nicht `AND`) zwischen Filtern |
| **Feldnamen** | DB-Spalten verwenden, nicht JSON-Keys! |
| **Sanitization** | Immer `_sanitize_search()` vor der USF-Konstruktion |

---

## 🚨 Troubleshooting

**Error:** `Bad syntax of the search string: (t.socid=135)`

→ **Fix:** Verwende USF-Syntax mit `:=:`: `(t.fk_soc:=:135)`

**Error:** `Bad syntax of the search string: (t.ref:like:test)`

→ **Fix:** Text in Quotes + Wildcards: `(t.ref:like:'%test%')`

---

## HistorY

- **v1.1.0** (2025-12-22): Dokumentation erstellt nach kritischen Filter-Fehlern in search_projects
