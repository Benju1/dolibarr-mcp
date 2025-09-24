# 🚀 Dolibarr MCP Server - Windows Fixed!

Ein professioneller **Model Context Protocol (MCP) Server** für Dolibarr ERP-Integration mit **vollständiger Windows-Kompatibilität**.

## 🔥 Windows Setup Problem GELÖST!

**Problem**: `[WinError 5] Zugriff verweigert` beim Setup durch pywin32
**Lösung**: Standalone Implementation ohne problematische Dependencies!

## ✅ Schnellstart für Windows (EMPFOHLEN)

Wenn Sie das pywin32 Problem haben, verwenden Sie unsere **standalone Version**:

### Option 1: Standalone Setup (Windows-optimiert)
```cmd
# 1. Repository klonen
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp

# 2. Standalone Setup (KEINE pywin32 Probleme!)
.\setup_standalone.bat

# 3. Konfiguration erstellen
copy .env.example .env
# Bearbeiten Sie .env mit Ihren Dolibarr-Credentials

# 4. Server starten
.\run_standalone.bat
```

### Option 2: Standard MCP Setup (wenn Option 1 nicht funktioniert)
```cmd
# Fallback: Standard Setup
.\setup.bat
# Falls pywin32 Fehler auftreten, nutzen Sie Option 1
```

## 🎯 Was ist enthalten?

### ✅ **Vollständige CRUD-Unterstützung**
- 👥 **User Management** - Benutzer verwalten
- 🏢 **Customer Management** - Kunden und Drittparteien
- 📦 **Product Management** - Produkte mit Preisen und Lager
- 🧾 **Invoice Management** - Rechnungen mit Zeilen und Status
- 📋 **Order Management** - Bestellungen verwalten
- 📞 **Contact Management** - Kontakte und Ansprechpartner
- 🔌 **Raw API Access** - Direkter Zugriff auf alle Dolibarr-Endpunkte

### 🛠️ **Technische Features**
- ✅ **Windows-kompatibel** - Keine pywin32 Probleme mehr!
- ✅ **Standalone Mode** - Funktioniert ohne MCP-Paket
- ✅ **Interactive Testing** - Eingebaute Test-Konsole
- ✅ **Professional Error Handling** - Detaillierte Fehlermeldungen
- ✅ **Async Architecture** - Optimale Performance
- ✅ **Docker Support** - Production-ready Container

## 🔧 Dolibarr Setup

### 1. **Dolibarr API aktivieren**
1. Dolibarr Admin Login
2. **Home → Setup → Modules**
3. **"Web Services API REST (developer)"** aktivieren
4. **Home → Setup → API/Web services**
5. **Neuen API Key generieren**

### 2. **Konfiguration (.env)**
```env
DOLIBARR_URL=https://ihre-dolibarr-instanz.com/api/index.php
DOLIBARR_API_KEY=ihr_dolibarr_api_schluessel
LOG_LEVEL=INFO
```

## 🧪 Server testen

```cmd
# Nach dem Setup:
.\run_standalone.bat

# Interactive Mode startet automatisch:
dolibarr-mcp> test test_connection
dolibarr-mcp> test get_status
dolibarr-mcp> test get_users
dolibarr-mcp> list
dolibarr-mcp> exit
```

## 📋 Verfügbare Tools

| Kategorie | Tools | Beschreibung |
|-----------|-------|-------------|
| **System** | `test_connection`, `get_status` | API-Status und Verbindung |
| **Users** | `get_users`, `create_user`, `update_user`, `delete_user` | Benutzerverwaltung |
| **Customers** | `get_customers`, `create_customer`, `update_customer`, `delete_customer` | Kundenverwaltung |
| **Products** | `get_products`, `create_product`, `update_product`, `delete_product` | Produktverwaltung |
| **Invoices** | `get_invoices`, `create_invoice`, `update_invoice`, `delete_invoice` | Rechnungsverwaltung |
| **Orders** | `get_orders`, `create_order`, `update_order`, `delete_order` | Bestellverwaltung |
| **Contacts** | `get_contacts`, `create_contact`, `update_contact`, `delete_contact` | Kontaktverwaltung |
| **Advanced** | `dolibarr_raw_api` | Roher API-Zugriff |

## 🐳 Docker Support

```yaml
# docker-compose.yml
version: '3.8'
services:
  dolibarr-mcp:
    build: .
    environment:
      - DOLIBARR_URL=https://ihre-instanz.com/api/index.php
      - DOLIBARR_API_KEY=ihr_schluessel
    ports:
      - "8080:8080"
    restart: unless-stopped
```

```bash
# Starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f dolibarr-mcp
```

## 🔧 Troubleshooting

### Windows pywin32 Probleme

**Symptom**: 
```
[WinError 5] Zugriff verweigert: '...pywin32_system32\pywintypes313.dll'
```

**Lösung**:
```cmd
# Verwenden Sie die standalone Version:
.\setup_standalone.bat
.\run_standalone.bat
```

**Warum funktioniert das?**
- ❌ Standard MCP-Paket benötigt pywin32 (Windows-Berechtigungen)
- ✅ Standalone Version verwendet nur Standard-Python-Bibliotheken
- ✅ Gleiche Funktionalität, keine Windows-Probleme

### API-Verbindungsprobleme

**Checkliste**:
1. ✅ Dolibarr "Web Services API REST" Modul aktiviert?
2. ✅ API Key in Dolibarr erstellt?
3. ✅ .env Datei korrekt ausgefüllt?
4. ✅ URL endet mit `/api/index.php`?
5. ✅ Firewall/Network erlaubt Zugriff?

**Testen**:
```cmd
# Verbindung direkt testen
.\run_standalone.bat
dolibarr-mcp> test test_connection
```

### Häufige Fehlermeldungen

| Fehler | Bedeutung | Lösung |
|--------|-----------|--------|
| "Cannot connect to Dolibarr API" | API nicht erreichbar | URL und Netzwerk prüfen |
| "403 Forbidden" | API Key ungültig | Neuen API Key erstellen |
| "Module not found" | Python Umgebung Problem | `setup_standalone.bat` erneut ausführen |

## 📚 Erweiterte Nutzung

### Custom API Calls

```cmd
dolibarr-mcp> # Beispiel: Raw API Zugriff
# {"method": "GET", "endpoint": "setup/modules"}
```

### Batch Operations

```python
# Beispiel: Alle Kunden abrufen
async def get_all_customers():
    result = await server.handle_tool_call("get_customers", {"limit": 100})
    return result
```

## 🤝 Support & Contributing

- 🐛 **Issues**: [GitHub Issues](https://github.com/latinogino/dolibarr-mcp/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/latinogino/dolibarr-mcp/discussions)
- 📖 **Wiki**: [Project Wiki](https://github.com/latinogino/dolibarr-mcp/wiki)

### Contributing
1. Fork das Repository
2. Feature Branch: `git checkout -b feature/neue-funktion`
3. Commit: `git commit -am 'Neue Funktion'`
4. Push: `git push origin feature/neue-funktion`
5. Pull Request erstellen

## 📄 License

MIT License - siehe [LICENSE](LICENSE)

---

## 🎉 Erfolgreich eingerichtet?

Ihr Dolibarr MCP Server ist **production-ready** mit:

✅ **Vollständige CRUD-Operationen** für alle Dolibarr-Module
✅ **Windows-Kompatibilität** ohne pywin32-Probleme  
✅ **Professional Error Handling** und Logging
✅ **Docker Support** für Production
✅ **Interactive Testing** für einfache Entwicklung

**🚀 Bereit, Ihr Dolibarr ERP mit AI zu integrieren!**
