# Dolibarr MCP Server 🚀

Ein professioneller **Model Context Protocol (MCP) Server** für Dolibarr ERP-Integration. Ermöglicht LLMs vollständige CRUD-Operationen für alle Dolibarr-Module über eine standardisierte API.

## ✨ Features

### 🔧 Vollständige CRUD-Unterstützung für alle Dolibarr-Module:
- **👥 User Management** - Benutzer verwalten, erstellen, aktualisieren, löschen
- **🏢 Customer/Third Party Management** - Kunden und Drittparteien vollständig verwalten  
- **📦 Product Management** - Produkte mit Preisen, Lager und Details
- **🧾 Invoice Management** - Rechnungen mit Zeilen, Steuer und Status
- **📋 Order Management** - Bestellungen und Aufträge verfolgen
- **📞 Contact Management** - Kontakte und Ansprechpartner
- **🔌 Raw API Access** - Direkter Zugriff auf beliebige Dolibarr-Endpunkte

### 🛠️ Technische Features:
- ✅ **Professionelle Fehlerbehandlung** mit detaillierten API-Error-Messages
- ✅ **Async/await Architektur** für optimale Performance
- ✅ **Pydantic Validation** für Typ-Sicherheit und Datenvalidierung
- ✅ **Umfassendes Logging** mit konfigurierbaren Log-Levels
- ✅ **Docker Support** mit Multi-Stage Builds
- ✅ **Windows + Linux Support** mit platform-spezifischen Setup-Scripts
- ✅ **Automatische API-Key Validation** und Connection Testing
- ✅ **MCP 1.0 Compliant** - kompatibel mit Claude, anderen LLMs

## 🚀 Quick Start

### Windows Setup (Empfohlen für Setup-Probleme)

Wenn Sie Probleme mit dem regulären Setup haben (besonders pywin32 Fehler), nutzen Sie das verbesserte Setup:

```cmd
# 1. Repository klonen
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp

# 2. Verbessertes Windows Setup (umgeht pywin32 Probleme)
.\setup_windows_fix.bat

# 3. .env Datei konfigurieren
copy .env.example .env
# Bearbeiten Sie .env mit Ihren Dolibarr-Credentials

# 4. Server starten
.\start_server.bat
```

### Linux/macOS Setup

```bash
# 1. Repository klonen
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp

# 2. Setup ausführen
chmod +x setup.sh
./setup.sh

# 3. .env konfigurieren
cp .env.example .env
# .env mit Ihren Dolibarr-Details bearbeiten

# 4. Server starten
python -m src.dolibarr_mcp
```

### Docker Setup

```bash
# Mit docker-compose (empfohlen)
cp .env.example .env
# .env konfigurieren, dann:
docker-compose up -d

# Oder direkt mit Docker
docker build -t dolibarr-mcp .
docker run -d --env-file .env -p 8080:8080 dolibarr-mcp
```

## ⚙️ Konfiguration

### Dolibarr API Setup

1. **Dolibarr Admin Login**
2. **Module aktivieren**: Home → Setup → Modules → "Web Services API REST (developer)" aktivieren
3. **API Key erstellen**: Home → Setup → API/Web services → Neuen API Key generieren
4. **API URL**: Normalerweise `https://ihre-dolibarr-instanz.com/api/index.php`

### .env Datei

```env
# Dolibarr API Configuration
DOLIBARR_URL=https://ihre-dolibarr-instanz.com/api/index.php  
DOLIBARR_API_KEY=ihr_dolibarr_api_schluessel

# Logging Configuration  
LOG_LEVEL=INFO
```

## 📋 Verfügbare Tools

Der Server stellt folgende MCP-Tools zur Verfügung:

### System & Status
- `test_connection` - API-Verbindung testen
- `get_status` - Dolibarr System-Status und Version

### User Management
- `get_users` - Benutzer auflisten (mit Pagination)
- `get_user_by_id` - Benutzer nach ID abrufen
- `create_user` - Neuen Benutzer erstellen
- `update_user` - Benutzer aktualisieren
- `delete_user` - Benutzer löschen

### Customer Management  
- `get_customers` - Kunden/Drittparteien auflisten
- `get_customer_by_id` - Kunde nach ID
- `create_customer` - Neuen Kunden erstellen
- `update_customer` - Kunde aktualisieren
- `delete_customer` - Kunde löschen

### Product Management
- `get_products` - Produkte auflisten
- `get_product_by_id` - Produkt nach ID
- `create_product` - Neues Produkt erstellen
- `update_product` - Produkt aktualisieren  
- `delete_product` - Produkt löschen

### Invoice Management
- `get_invoices` - Rechnungen auflisten (mit Status-Filter)
- `get_invoice_by_id` - Rechnung nach ID
- `create_invoice` - Neue Rechnung mit Zeilen erstellen
- `update_invoice` - Rechnung aktualisieren
- `delete_invoice` - Rechnung löschen

### Order Management
- `get_orders` - Bestellungen auflisten
- `get_order_by_id` - Bestellung nach ID
- `create_order` - Neue Bestellung erstellen
- `update_order` - Bestellung aktualisieren
- `delete_order` - Bestellung löschen

### Contact Management
- `get_contacts` - Kontakte auflisten
- `get_contact_by_id` - Kontakt nach ID
- `create_contact` - Neuen Kontakt erstellen
- `update_contact` - Kontakt aktualisieren
- `delete_contact` - Kontakt löschen

### Advanced
- `dolibarr_raw_api` - Roher API-Aufruf an beliebige Dolibarr-Endpunkte

## 🧪 Testing

```bash
# API-Verbindung testen
python test_connection.py

# Umfassende Tests
python test_dolibarr_mcp.py

# Mit Docker
docker-compose --profile test up dolibarr-mcp-test
```

## 🐳 Docker Production Deployment

```yaml
version: '3.8'
services:
  dolibarr-mcp:
    image: dolibarr-mcp:latest
    environment:
      - DOLIBARR_URL=https://ihre-dolibarr-instanz.com/api/index.php
      - DOLIBARR_API_KEY=ihr_api_schluessel
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from src.dolibarr_mcp.config import Config; Config()"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔧 Troubleshooting

### Windows Setup Probleme

**Problem**: `[WinError 5] Zugriff verweigert` beim Installieren von pywin32

**Lösung**: Nutzen Sie das verbesserte Setup-Script:
```cmd
.\setup_windows_fix.bat
```

Dieses Script:
- Verwendet `requirements-minimal.txt` ohne problematische Pakete
- Installiert Pakete einzeln bei Fehlern
- Umgeht pywin32-Berechtigungsprobleme
- Funktioniert auch ohne Admin-Rechte

### API-Verbindungsprobleme

**Symptom**: "Cannot connect to Dolibarr API"

**Checkliste**:
1. ✅ Dolibarr "Web Services API REST" Modul aktiviert?
2. ✅ API Key in Dolibarr erstellt?
3. ✅ .env Datei korrekt konfiguriert?
4. ✅ DOLIBARR_URL mit `/api/index.php` am Ende?
5. ✅ Firewall/Network-Zugang?

**Debug**:
```bash
# Verbindung direkt testen
python test_connection.py

# Detaillierte Logs
LOG_LEVEL=DEBUG python -m src.dolibarr_mcp
```

### Häufige API-Endpunkt Probleme

| Endpunkt | Häufige Probleme | Lösung |
|----------|------------------|---------|
| `/users` | 403 Forbidden | Admin API Key erforderlich |
| `/products` | Leere Liste | Produkte in Dolibarr erstellen |  
| `/thirdparties` | 500 Error | Customer/Supplier Module aktivieren |
| `/invoices` | Permission denied | Invoice Module + Rechte prüfen |

## 📚 API Dokumentation

Vollständige Dolibarr REST API Dokumentation:
- [Dolibarr REST API Wiki](https://wiki.dolibarr.org/index.php?title=Module_Web_Services_API_REST_(developer))
- [API Interfaces Guide](https://wiki.dolibarr.org/index.php?title=Interfaces_Dolibarr_toward_foreign_systems)

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen: `git checkout -b feature/neue-funktion`
3. Changes committen: `git commit -am 'Neue Funktion hinzufügen'`
4. Branch pushen: `git push origin feature/neue-funktion`  
5. Pull Request erstellen

## 📄 License

MIT License - siehe [LICENSE](LICENSE) für Details.

## 🆘 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/latinogino/dolibarr-mcp/issues)
- 📖 **Wiki**: [Project Wiki](https://github.com/latinogino/dolibarr-mcp/wiki)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/latinogino/dolibarr-mcp/discussions)

---

**⚡ Ready to integrate your Dolibarr ERP with AI? Get started in 2 minutes!**
