# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [14.0.0] - 2026-03-19

### BREAKING CHANGE
- **Renamed from `free-web-search-ultimate` to `cross-validated-search`**
- Package name changed: `pip install cross-validated-search`
- CLI command changed: `search-web` → `cross-validate`
- MCP server changed: `free-web-search-mcp` → `cross-validated-mcp`
- Module changed: `free_web_search` → `cross_validated_search`
- GitHub repository renamed: `wd041216-bit/cross-validated-search`

### Added
- **Anti-Hallucination Focus**: Repositioned as the primary solution for preventing LLM hallucinations
- **Confidence Scoring System**: Explicit confidence levels (✅ Verified, 🟢 Likely True, 🟡 Uncertain, 🔴 Likely False)
- **Cross-Validation Guarantees**: Every fact is verified against multiple independent sources
- **Conflict Detection**: Automatically flags conflicting information across sources
- **Minimum Sources Parameter**: `CrossValidatedSearcher(min_sources=3)` for configurable verification depth
- Enhanced documentation with decision tree for agents
- New keywords: hallucination, cross-validation, verification, anti-hallucination

### Changed
- Class renamed: `UltimateSearcher` → `CrossValidatedSearcher`
- Focus shifted from "free search" to "hallucination prevention"
- All documentation updated to emphasize cross-validation and anti-hallucination
- Confidence scoring now explicit: HIGH (3+ sources), MEDIUM (2 sources), LOW (1 source)
- Repository description updated to highlight anti-hallucination capabilities

### Migration Guide

**Before (v13.x):**
```bash
pip install free-web-search-ultimate
search-web "query"
```

**After (v14.x):**
```bash
pip install cross-validated-search
cross-validate "query"
```

**Python API:**
```python
# Before
from free_web_search.search_web import UltimateSearcher
searcher = UltimateSearcher()

# After
from cross_validated_search.search import CrossValidatedSearcher
searcher = CrossValidatedSearcher()
```

## [13.0.0] - 2026-03-18

### Changed
- Fully internationalized all user-facing strings, error messages, and code comments to English for universal compatibility
- Rewrote all module, class, and function docstrings to Google style with complete `Args:`, `Returns:`, and `Example:` sections
- Expanded all multi-parameter function signatures to multi-line format per PEP 8 and Google style guide
- `UltimateSearcher.search()` docstring now documents all `timelimit` values (`d/w/m/y`) and `search_type` options
- `_cross_validate()` now uses typed `Dict[str, List[Source]]` annotation
- Error fallback message changed to English: "No results found. The search engine may be rate-limited."
- CLI output formatting improved: unified spacing, cleaner REPL prompt
- `browse_page.py` module docstring updated; all inline comments translated to English
- Version bumped to 13.0.0

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