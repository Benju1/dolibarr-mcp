# Instructions for GitHub Copilot

## Projekt-Übersicht
**dolibarr-mcp**: Professional Model Context Protocol (MCP) Server für umfassende Dolibarr ERP/CRM Verwaltung
- **Typ**: Python CLI + MCP Server
- **Hauptzweck**: Automatisierte Dolibarr-Integration via MCP Protocol
- **Status**: Beta (v1.1.0)

## Projekt-Setup
- **Dependency Management**: uv (https://github.com/astral-sh/uv)
- **Python Version**: 3.12+ (via `.python-version`)
- **Unterstützt**: 3.12 - 3.13
- **Testing**: pytest mit pytest-asyncio und pytest-cov
- **Package Manager**: setuptools (via pyproject.toml)

## Wichtige Dependencies
- **fastmcp** (2.11.3): MCP Server Framework
- **mcp** (≥1.0.0): Model Context Protocol
- **pydantic** (≥2.5.0): Data validation & settings
- **click** (≥8.1.0): CLI Framework
- **aiohttp** (≥3.9.0): Async HTTP Client

## Projekt-Struktur
```
src/dolibarr_mcp/
├── __main__.py           # CLI Entry Point
├── cli.py                # CLI Commands (click)
├── config.py             # Configuration & Settings
├── server.py             # MCP Server Implementation
├── dolibarr_client.py    # Dolibarr API Client (aiohttp)
├── models.py             # Pydantic Models
├── testing.py            # Test Utilities
└── tools/                # Domain-specific MCP Tools
    ├── contacts.py       # Contact Management
    ├── customers.py      # Customer Management
    ├── invoices.py       # Invoice Operations
    ├── orders.py         # Order Management
    ├── products.py       # Product Catalog
    ├── projects.py       # Project Management
    ├── proposals.py      # Proposal Management
    ├── system.py         # System Info Tools
    └── users.py          # User Management
```

## Test Commands
**IMMER `uv run` voranstellen!**

```bash
# Alle Tests
uv run pytest

# Specific file
uv run pytest tests/test_xyz.py -v

# Mit Coverage
uv run pytest --cov=src tests/

# Einzelner Test
uv run pytest tests/test_xyz.py::test_function_name

# Mit asyncio Debugging
uv run pytest tests/test_xyz.py -v -s
```

## Code Style

### Tooling
- **Formatter**: `uv run ruff format src/ tests/`
- **Linter**: `uv run ruff check src/ tests/`
- **Type Checker**: `uv run mypy src/ --strict`

```bash
# Format Code
uv run ruff format src/ tests/

# Lint Code
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/ --strict
```

### Guidelines
- **Docstrings**: Google Style (mandatory für public APIs)
- **Error Handling**: Keine bare `except:` – immer spezifische Exception-Types
- **Async**: Nutze `async/await` für I/O-Operations (API Calls)

### Type Hints
**Mandatory für:**
- Alle Funktionen/Methoden in `src/` (außer `_private` helper)
- Public API = exportiert, nicht mit `_` prefixed
- Async Funktionen: Rückgabe-Type explizit (z.B. `async def get_contact(...) -> Contact:`)

**Stil:**
- Nutze `X | Y` statt `Union[X, Y]`
- Type Parameter Syntax erlaubt: `def first[T](items: list[T]) -> T`
- Optional: `T | None` statt `Optional[T]`

### Logging
- **Libraries (`src/dolibarr_mcp/`)**: Nur `logging`, kein `print()`
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.debug("Message")
  logger.error("Error", exc_info=True)
  ```
- **CLI (`cli.py`, `__main__.py`)**:
  - `print()` für User-Output (Ergebnisse, Fortschritt, Status)
  - `logging` für Diagnostics (Debug, Info, Error, Exception)

### Async/Await Best Practices
- Immer `async with aiohttp.ClientSession() as session:` verwenden
- Tasks mit `asyncio.gather()` für parallele Operationen koordinieren
- `pytest-asyncio` Fixtures für Tests: `@pytest.mark.asyncio`

### Moderne Features (verfügbar in 3.12+)
Alle Features aus Python 3.12+ sind erlaubt, da wir ≥3.12 unterstützen:
- ✅ Type Parameter Syntax: `def first[T](items: list[T]) -> T`
- ✅ `type` Statement: `type Point = tuple[float, float]`
- ✅ Union Operator `|`: `str | None`
- ✅ Match Statement: `match` für Pattern Matching
- ✅ Built-in Generics: `list[int]`

## MCP Tools Development
- Alle Tools in `src/dolibarr_mcp/tools/` nach Domain organisiert
- Jedes Tool-Modul exportiert `get_tools()` Funktion
- Nutze `@server.call_tool()` Decorator für MCP Tool Registration
- Async Tools erfordern `async def` Implementierung
- Error Handling: Sprechende Error Messages für MCP Clients

## Dolibarr API Integration
- Client in `dolibarr_client.py`: `DolibarrClient` Klasse
- Base URL via `.env` oder Config: `DOLIBARR_URL`, `DOLIBARR_API_KEY`
- Alle API Calls nutzen `aiohttp` für async Operations
- Response Validation via Pydantic Models aus `models.py`

## Konfiguration
- `.env` File für lokale Development (git-ignored)
- Pydantic Settings in `config.py`
- Environment Variables: `DOLIBARR_URL`, `DOLIBARR_API_KEY`, `LOG_LEVEL`, etc.

## Git/Commit Conventions
- Feature Branches: `feature/description`
- Bugfix Branches: `fix/description`
- Commits: Prägnante, englische Messages
- Tests MÜSSEN vor Merge grün sein

