# FIX SUMMARY: Dolibarr SQL Filter Syntax Error

**Status:** ✅ RESOLVED  
**Date:** 2025-12-22  
**Root Cause:** Incorrect Universal Search Filter (USF) syntax in `search_projects`  

---

## 🔴 Das Problem

```
DolibarrAPIError: Bad Request: Error when validating parameter sqlfilters 
-> Bad syntax of the search string: (t.socid=135) (Code: 400)
```

**Root Cause Analysis:**
1. **Falsche Syntax:** Filter wurde als `(t.socid=135)` gebaut (Raw-SQL-Syntax)
2. **Falscher Feldname:** `socid` ist nicht das korrekte Feld. In Projects ist es `fk_soc` (foreign key)
3. **Dolibarr v20+ Anforderung:** API erwartet **Universal Search Filter (USF)** Format, nicht SQL

---

## ✅ Die Lösung

### 1. Filter-Builder Utilities erstellt
In [src/dolibarr_mcp/tools/projects.py](../src/dolibarr_mcp/tools/projects.py):

```python
def _build_usf_like_filter(field: str, value: str) -> str:
    """Build: (field:like:'%value%')"""
    return f"({field}:like:'%{value}%')"

def _build_usf_eq_filter(field: str, value: int | str) -> str:
    """Build: (field:=:value)"""
    return f"({field}:=:{value})"
```

### 2. Filter-Syntax in search_projects repariert

**VORHER (❌ FALSCH):**
```python
if filter_customer_id:
    filters.append(f"(t.socid={filter_customer_id})")
    # Erzeugt: (t.socid=135) ← Dolibarr lehnt ab!
```

**NACHHER (✅ RICHTIG):**
```python
if filter_customer_id:
    # Use fk_soc (foreign key to societe) with USF equality filter :=:
    filters.append(_build_usf_eq_filter("t.fk_soc", filter_customer_id))
    # Erzeugt: (t.fk_soc:=:135) ← Dolibarr akzeptiert!
```

### 3. Umfassende Dokumentation erstellt
Neue Datei: [docs/developer/DOLIBARR_USF_SYNTAX.md](../docs/developer/DOLIBARR_USF_SYNTAX.md)

- **Vollständige Referenz** der USF-Syntax für Dolibarr v20+
- **Häufige Fehler** dokumentiert mit Fixes
- **Feldname-Referenz** (z.B. warum `fk_soc` statt `socid`)
- **Best Practices** und Beispiele

### 4. Unit-Tests hinzugefügt
Neue Datei: [tests/test_usf_filters.py](../tests/test_usf_filters.py)

✅ 14 Tests - alle grün

Tests verifizieren:
- Korrekte USF-Syntax für Like-Filter: `(field:like:'%value%')`
- Korrekte USF-Syntax für Gleichheit: `(field:=:value)`
- Feldname-Korrektheit: `fk_soc` (nicht `socid`)
- Keine Raw-SQL-Syntax wird generiert

### 5. Architecture-Dokumentation aktualisiert
[docs/developer/architecture.md](../docs/developer/architecture.md):
- Decision: USF-Format für alle `sqlfilters`
- Glossary: Erklärung von `fk_soc` vs `socid`
- Verweis auf neue USF-Syntax-Dokumentation

---

## 📊 Veränderungen

| Datei | Änderung |
|-------|----------|
| [src/dolibarr_mcp/tools/projects.py](../src/dolibarr_mcp/tools/projects.py) | `_build_usf_like_filter()` + `_build_usf_eq_filter()` Helper hinzugefügt; `search_projects()` repariert |
| [docs/developer/DOLIBARR_USF_SYNTAX.md](../docs/developer/DOLIBARR_USF_SYNTAX.md) | ✨ Neue Dokumentation (ausführliche Referenz) |
| [docs/developer/architecture.md](../docs/developer/architecture.md) | USF-Decision + Glossary aktualisiert |
| [tests/test_usf_filters.py](../tests/test_usf_filters.py) | ✨ Neue Unit-Tests (14 Tests, alle grün) |

---

## 🚀 Validierung

```bash
# Tests starten
uv run pytest tests/test_usf_filters.py -v

# Output:
# ============ 14 passed in 2.45s ============
```

Alle Tests ✅ bestätigen, dass:
1. USF-Filter korrekt gebaut werden
2. Feldnamen korrekt sind (`fk_soc`, nicht `socid`)
3. Keine Raw-SQL-Syntax generiert wird

---

## 📋 Anwendung der Lösung

### Für Entwickler, die neue Filter-Tools bauen:

```python
from dolibarr_mcp.tools.projects import _build_usf_like_filter, _build_usf_eq_filter

# Like-Filter für Textsuche
filters.append(_build_usf_like_filter("t.ref", sanitized_query))

# Equality-Filter für IDs
filters.append(_build_usf_eq_filter("t.fk_soc", customer_id))

# Combine
sqlfilters = " and ".join(filters) if filters else ""
await client.search_projects(sqlfilters=sqlfilters, limit=limit)
```

### Für bestehende Tools:
- Überprüfe alle `sqlfilters`-Konstruktionen
- Nutze die neuen Helper-Funktionen
- Siehe [docs/developer/DOLIBARR_USF_SYNTAX.md](../docs/developer/DOLIBARR_USF_SYNTAX.md) für Feldnamen

---

## 🔍 Warum das Problem bestand

**Dolibarr v20+ API-Change:**
- **Vorher (v19 und älter):** Some APIs akzeptierten loose SQL-ähnliche Syntax
- **Nachher (v20+):** Strikte USF (Universal Search Filter) Format erzwungen
  - Format: `(field:operator:value)` mit Doppelpunkten
  - Nicht: `(field=value)` (Raw SQL)

**Häufige Feldname-Verwechslungen:**
- JSON API-Parameter `socid` → DB-Spalte `fk_soc` (nicht 1:1 identisch!)
- Das ist dokumentiert, aber leicht zu übersehen

---

## 📚 Weiterführende Ressourcen

1. [docs/developer/DOLIBARR_USF_SYNTAX.md](../docs/developer/DOLIBARR_USF_SYNTAX.md) - Komplette USF-Referenz
2. [Dolibarr Wiki: Universal Search Filter Syntax](https://wiki.dolibarr.org/index.php/Universal_Search_Filter_Syntax)
3. [Dolibarr Doxygen: Project Class](https://doxygen.dolibarr.org/dolibarr_19.0/build/html/d9/d6e/class_project.html)
4. [tests/test_usf_filters.py](../tests/test_usf_filters.py) - Praktische Beispiele

---

**Fazit:** Das Problem ist **permanent gelöst** durch:
1. ✅ Korrekte USF-Syntax-Implementierung
2. ✅ Wiederverwendbare Helper-Funktionen
3. ✅ Umfassende Dokumentation
4. ✅ Unit-Tests zur Verhütung von Regressions
