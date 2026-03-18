# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [12.0.0] - 2026-03-18

### Added
- Published to PyPI: `pip install free-web-search-ultimate`
- SKILL.md updated to use PyPI installation (eliminates supply-chain risk from git-based install)
- Python 3.10+ requirement enforced in CI and package metadata

### Changed
- Installation method changed from `pip install git+...` to `pip install free-web-search-ultimate`

## [11.0.0] - 2025-03-17

### Added
- Universal Search-First Knowledge Acquisition Plugin for LLMs
- Full MCP (Model Context Protocol) server support
- CLI-Anything standard compliance with PATH-accessible entry points
- REPL interactive mode for continuous search sessions
- `SKILL.md` auto-discovery bundled with Python package

### Changed
- Removed suspicious language from `SKILL.md`, replaced with guideline-based approach
- Improved security posture: no hardcoded credentials, no third-party routing

### Fixed
- Removed dead Yahoo engine
- Fixed thread safety issues in concurrent search

## [10.0.0] - 2025-02-01

### Added
- CLI-Anything Harness: standard package with `entry_points`
- REPL mode for interactive search
- Auto-discoverable `SKILL.md` installed alongside Python package
- Global PATH callable commands: `search-web`, `browse-page`, `free-web-search-mcp`

### Changed
- Upgraded to `ddgs` official library for stable DDG JSON API access
- Improved JSON output structure for LLM consumption

## [9.0.0] - 2025-01-15

### Added
- Image search support
- Un-truncated URL output
- Optimized network usage with connection pooling

### Changed
- `answer` field simplified to minimal summary to reduce token usage

## [8.0.0] - 2024-12-20

### Added
- Books search support
- Videos search support

### Fixed
- Thread safety issues
- Removed dead Yahoo search engine

## [7.0.0] - 2024-12-01

### Added
- Super Workflow Round 3 upgrade
- Cross-engine validation for higher confidence results
- News search with timestamps

## [1.0.0] - 2024-10-01

### Added
- Initial release
- DuckDuckGo web search via `ddgs` library
- Basic text and news search
- JSON output format
- MIT License
