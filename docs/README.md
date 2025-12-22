# 📚 Dokumentationsstruktur & Index

Willkommen in der **professionellen Architekturdokumentation** des **Dolibarr MCP Servers**.

Diese Struktur folgt bewährten Richtlinien wie **arc42**, **C4 Model** und **DDD**.

---

## 📖 Dokumentations-Übersicht

### **Kapitel 1: Architektur-Überblick** (`02_architecture/`)

Ein umfassendes Verständnis des Systems, seiner Komponenten und Entscheidungen.

| Dokument | Fokus | Lese-Dauer |
|----------|-------|-----------|
| [00_intro_goals.md](02_architecture/00_intro_goals.md) | **Intro & Ziele**: Projektübersicht, Design-Philosophie, Stakeholder | 10 min |
| [01_context_scope.md](02_architecture/01_context_scope.md) | **Kontext & Scope**: Externe Systeme, Nutzerrollen, Out of Scope, C4 Level 1 | 12 min |
| [02_building_blocks.md](02_architecture/02_building_blocks.md) | **Bausteinsicht**: C4 Level 2, Komponenten, Schichten, Datenfluss | 15 min |
| [03_project_structure.md](02_architecture/03_project_structure.md) | **Projektstruktur**: Ordner-Layout, Verantwortlichkeiten | 12 min |
| [04_decisions.md](02_architecture/04_decisions.md) | **Architekturentscheidungen**: ADRs mit Alternativen | 20 min |
| [05_implementation.md](02_architecture/05_implementation.md) | **Implementierungsplan**: Tasks, Module, Tests | 18 min |
| [06_risks.md](02_architecture/06_risks.md) | **Risiken & offene Punkte**: Mitigation-Strategien | 10 min |

### **Kapitel 2: Praktische Guides** (`04_guides/`)

| Dokument | Zielgruppe |
|----------|-----------|
| [quickstart.md](04_guides/quickstart.md) | Anfänger, Deployment |
| [configuration.md](04_guides/configuration.md) | Sysadmins, DevOps |
| [development.md](04_guides/development.md) | Entwickler |
| [api-reference.md](04_guides/api-reference.md) | Tool-Nutzer |

---

## 🎯 Schnell-Einstieg nach Rolle

### 👨‍💻 **Entwickler** → [02_building_blocks.md](02_architecture/02_building_blocks.md) + [development.md](04_guides/development.md)
### 🏗️ **Architekt** → [00_intro_goals.md](02_architecture/00_intro_goals.md) + [04_decisions.md](02_architecture/04_decisions.md)
### ⚙️ **DevOps** → [quickstart.md](04_guides/quickstart.md) + [configuration.md](04_guides/configuration.md)
### 🔌 **Claude/Client** → [api-reference.md](04_guides/api-reference.md)

---

**Status:** ✅ Production Ready (v1.1.0)  
**Letzte Aktualisierung:** 2025-12-22
