# Changelog

All notable changes to the Dolibarr MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-26

### 🎯 Major Restructuring

This release represents a complete restructuring of the Dolibarr MCP Server to match the clean architecture of prestashop-mcp.

### Added
- Professional README.md with comprehensive documentation
- Structured test suite in `tests/` directory
- Clean configuration management
- Docker support for easy deployment
- Comprehensive CRUD operations for all Dolibarr entities

### Changed
- Complete repository restructuring to match prestashop-mcp pattern
- Simplified dependencies in requirements.txt
- Cleaned up package structure in `src/dolibarr_mcp/`
- Updated pyproject.toml with proper metadata
- Streamlined .gitignore file

### Removed
- All test scripts from root directory (moved to `tests/`)
- Multiple batch files (consolidated functionality)
- Alternative server implementations (simple_client, standalone_server, ultra_simple_server)
- Redundant requirements files (kept only requirements.txt)
- Unnecessary documentation files (CLAUDE_CONFIG.md, CONFIG_COMPATIBILITY.md, etc.)
- API directory and contents

### Technical Improvements
- Single, focused MCP server implementation
- Clean separation of concerns
- Better error handling
- Improved logging
- Async/await architecture throughout

## [0.5.0] - 2024-01-20

### Added
- Initial Dolibarr API integration
- Basic CRUD operations for customers, products, invoices
- MCP server implementation
- Docker configuration

## [0.1.0] - 2024-01-15

### Added
- Initial project setup
- Basic repository structure
- License and documentation

---

**Note**: This changelog focuses on the major restructuring in v1.0.0 to align with prestashop-mcp's clean architecture.
