# Architektur-Dokumentation Index

Diese Ordner enthält die **offizielle Systemarchitektur-Dokumentation** für den Dolibarr MCP Server.

Die Struktur folgt **arc42**, **C4 Model** und bewährten Praktiken.

---

## 📋 Kapitel-Übersicht

| # | Datei | arc42 Ref | Fokus |
|----|-------|-----------|-------|
| 0 | [00_intro_goals.md](00_intro_goals.md) | Kap. 1-2 | Intro, Ziele, Randbedingungen |
| 1 | [01_context_scope.md](01_context_scope.md) | Kap. 3 | Systemkontext, Scope, Out-of-Scope |
| 2 | [02_building_blocks.md](02_building_blocks.md) | Kap. 4 | Bausteinsicht, C4 Level 2 |
| 3 | [03_project_structure.md](03_project_structure.md) | Kap. 4.3 | Projektstruktur, Code-Layout |
| 4 | [04_decisions.md](04_decisions.md) | Kap. 5 | Architektur-Entscheidungen (ADRs) |
| 5 | [05_implementation.md](05_implementation.md) | Kap. 6-7 | Implementierungsplan, Tasks |
| 6 | [06_risks.md](06_risks.md) | Kap. 8 | Risiken, offene Punkte |

---

## 🚀 Schnell-Start

### Ich bin neuer Entwickler
```
1. Lese 00_intro_goals.md          (5 min) – Was ist dieses Projekt?
2. Lese 02_building_blocks.md      (10 min) – Wie ist es aufgebaut?
3. Lese 03_project_structure.md    (8 min) – Wo ist welcher Code?
4. Gehe zu ../04_guides/development.md  – Setup & Testing
```

### Ich muss ein Risiko evaluieren
```
1. Gehe zu 06_risks.md
2. Suche das Risiko (RISIKO-NNN)
3. Lese Description, Mitigation, Related Issues
```

### Ich möchte eine neue Architecture-Entscheidung dokumentieren
```
1. Lese 04_decisions.md (Format verstehen)
2. Erstelle neue ADR mit:
   - Status (✅ Akzeptiert, 🔄 Draft, ❌ Verworfen)
   - Entscheidung
   - Rationale
   - Alternativen
   - Pro/Contra
3. Link in 04_decisions.md einfügen
```

---

## 📖 Empfohlene Lese-Reihenfolge

**Für alle (20 min):**
1. 00_intro_goals.md
2. 01_context_scope.md
3. 02_building_blocks.md (bis C4 Level 2 Diagramm)

**Für Entwickler (zusätzlich 20 min):**
4. 03_project_structure.md
5. 05_implementation.md (Testing-Teil)

**Für Architekten (zusätzlich 30 min):**
4. 03_project_structure.md
5. 04_decisions.md
6. 06_risks.md

**Für DevOps/Deployment:**
- 00_intro_goals.md (Überblick)
- 06_risks.md (Limitations)
- Dann zu ../04_guides/

---

## 🔄 Versioning & Status

| Dokument | Version | Status | Review-Zyklus |
|----------|---------|--------|---------------|
| 00_intro_goals.md | 1.1.0 | ✅ Production | Nach Major Release |
| 01_context_scope.md | 1.1.0 | ✅ Production | Nach Major Release |
| 02_building_blocks.md | 1.1.0 | ✅ Production | Nach Major Release |
| 03_project_structure.md | 1.1.0 | ✅ Production | Nach Code Refactor |
| 04_decisions.md | 1.1.0 | ✅ Production | Nach ADR akzeptiert |
| 05_implementation.md | 1.1.0 | ✅ Production | Nach Release |
| 06_risks.md | 1.1.0 | ✅ Production | Quarterly |

---

## 📝 Bearbeitung & Wartung

### Wer darf ändern?
- ✅ Core Team: Alle Dateien
- ✅ Contributors: Via Pull Request
- ✅ Community: Via Issues & Discussions

### Update-Checklist
- [ ] Inhalt überprüft & korrekt?
- [ ] Alle Links sind gültig (relative Pfade)?
- [ ] Status & Version updated?
- [ ] "Letzte Aktualisierung" Datum aktuell?
- [ ] Verwandte Dateien gecrosslinckt?
- [ ] Code-Beispiele auf Aktualität überprüft?

### Review-Prozess
1. Branch erstellen: `docs/update-architecture`
2. Datei(en) bearbeiten
3. PR öffnen mit `docs:` Prefix
4. Mindestens 1x Core Team Review
5. Merge & Commit-Message mit Änderungen-Summary

---

## 🎯 Typische Use-Cases

### "Ich muss verstehen, warum wir async nutzen"
→ [04_decisions.md → ADR-002](04_decisions.md#adr-002-async-only-architecture-kein-sync-code)

### "Wie teste ich einen neuen Tool?"
→ [05_implementation.md → 5. Test-Strategie](05_implementation.md#5-test-strategie)

### "Was ist das Risiko von großen Datenmengen?"
→ [06_risks.md → RISIKO-003](06_risks.md#-risiko-003-performance--timeout-bei-großen-datenmengen)

### "Wie registriere ich ein neues Dolibarr-Modul?"
→ [02_building_blocks.md → Tools Layer](02_building_blocks.md#23-domain-tools-layer-toolspy)

### "Welche Komponenten gibt es?"
→ [02_building_blocks.md → C4 Level 2](02_building_blocks.md#1-c4-level-2--hauptkomponenten)

### "Wo ist der Test-Code?"
→ [03_project_structure.md → Folder Layout](03_project_structure.md#1-ordner-layout)

---

## 🔗 Wichtige Externe Links

- **GitHub Repo:** https://github.com/latinogino/dolibarr-mcp
- **MCP Protokoll:** https://modelcontextprotocol.io/
- **Dolibarr API:** https://wiki.dolibarr.org/index.php/API
- **arc42:** https://arc42.de/

---

## ❓ Häufig gestellte Fragen

**F: Warum arc42?**  
A: Bewährte Template für IT-Architektur-Dokumentation, weit verbreitet, professionell, skalierbar.

**F: Wer ist der Owner dieser Docs?**  
A: @dolibarr-mcp-team, mit Community-Contributions willkommen.

**F: Wie oft wird aktualisiert?**  
A: Nach Major Releases, oder wenn signifikante Änderungen vorgenommen werden.

**F: Kann ich Verbesserungen vorschlagen?**  
A: Ja! Issues oder Pull Requests sind willkommen.

---

**Autor:** Dolibarr MCP Team  
**Letzte Aktualisierung:** 2025-12-22  
**Version:** 1.1.0  
**Status:** ✅ Production Ready

Viel Erfolg mit der Dokumentation! 📚
