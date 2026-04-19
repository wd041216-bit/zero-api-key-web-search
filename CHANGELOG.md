# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [16.0.0] - 2026-03-24

### Changed
- Renamed the canonical PyPI package to `zero-api-key-web-search` and the canonical Python module to `zero_api_key_web_search`.
- Kept `free_web_search` imports and `free-web-search-mcp` available as compatibility aliases for existing integrations.
- Switched packaging, Docker, CI, and platform docs to point at the canonical v16 names.

### Fixed
- Aligned README, contributing docs, and bundled skill docs with the current published package and CLI surface.
- Corrected the repository license wording to match the actual `LICENSE` file.
- Updated the test suite to validate the active `zero_api_key_web_search.search_web` and `browse_page` implementations.
- Updated CI to fail on real test regressions instead of continuing after errors.
- Consolidated search logic into a shared core to reduce drift between `search_web.py` and `search.py`.
- Switched TLS handling to secure-by-default with explicit opt-in insecure mode for constrained environments.
- Added CLI and MCP smoke tests plus a modern `pyproject.toml` packaging source of truth.
- Tightened public docs and platform instructions so they describe the current evidence-aware implementation instead of overstating guarantees.

### Added
- Added `verify-claim`, a first-pass evidence workflow that classifies search results as supporting, conflicting, or neutral and returns a structured verdict.
- Added `evidence-report`, a higher-level workflow that combines search, verification, citation-ready source digests, and recommended next steps.
- Added MCP support for `verify_claim` so agent clients can request claim verification directly.
- Added MCP support for `evidence_report` so agent clients can request a compact evidence package directly.
- Added a self-hosted SearXNG setup guide for the recommended free dual-provider path.
- Added `docker-compose.searxng.yml`, `scripts/start-searxng.sh`, and `scripts/validate-free-path.sh` for lower-friction local SearXNG bootstrapping.
- Added trust-model, release, support, and security docs plus reproducible quickstart examples.
- Added build and wheel-install validation to CI for release-grade packaging checks.
- Added evidence-aware verification metadata such as score breakdown, provider diversity, and contention summaries.
- Added an explainable evidence model document at `docs/verification-model.md`.

### Changed
- Upgraded `verify-claim` to `evidence-aware-heuristic-v2` with source-quality, freshness, and domain-diversity scoring.
- Expanded CLI and MCP outputs to expose weighted support/conflict signals for auditability.
- Expanded the flagship CLI, MCP, README, and platform skill surfaces to expose `evidence-report` as the preferred reviewer-facing workflow.
- Improved free-path guidance so warnings and docs now point directly to self-hosted `searxng` as the recommended second provider.
- Updated README and skill surfaces to describe the current evidence model without overclaiming beyond the implementation.

## [15.0.0] - 2026-03-20

### Added
- **Universal IDE Support**: Now works with 10+ platforms out of the box
  - Claude Code: `.claude-plugin/SKILL.md` with UserPromptSubmit hooks
  - Cursor: `.cursor/rules/zero-api-key-web-search.md`
  - GitHub Copilot: `.github/copilot/instructions.md`
  - Gemini CLI: `.gemini/SKILL.md`
  - Continue: `.continue/skills/zero-api-key-web-search/SKILL.md`
  - Kiro: `.kiro/steering/zero-api-key-web-search.md`
  - OpenCode: `.opencode/instructions.md`
  - Codex: `.codex/SKILL.md`
  - OpenClaw: `free_web_search/skills/SKILL.md` (existing)
  - MCP: `free-web-search-mcp` (existing)
  - CLI: `search-web`, `browse-page` (existing)
- **Platform Detection Metadata**: Added `platforms` field to `_meta.json`
- **IDE-Specific Hooks**: Claude Code now has UserPromptSubmit hooks for automatic factual query detection
- **Comprehensive README**: Updated with all supported platforms and installation instructions

### Changed
- Version bumped to 15.0.0
- README completely rewritten to emphasize universal IDE support
- SKILL.md now lists all supported platforms in frontmatter
- Package description updated to mention universal IDE support

### Migration Guide

**No breaking changes** — all existing functionality preserved. New IDE configurations are additive.

To enable IDE-specific features:
- Claude Code: Install package, `.claude-plugin/SKILL.md` is auto-detected
- Cursor: Copy `.cursor/rules/` to your project
- Copilot: `.github/copilot/instructions.md` is auto-detected by VS Code
- Gemini: Install package, `.gemini/SKILL.md` is auto-detected

## [14.0.0] - 2026-03-19

### Changed
- Repository branding shifted toward **Zero-API-Key Web Search** and the GitHub repository moved to `wd041216-bit/zero-api-key-web-search`.
- The published compatibility surface remained stable:
  - package: `free-web-search-ultimate`
  - CLI: `search-web`, `browse-page`
  - MCP server: `free-web-search-mcp`
  - Python module: `free_web_search`

### Added
- **Anti-Hallucination Focus**: Repositioned as the primary solution for preventing LLM hallucinations
- **Confidence Scoring System**: Explicit confidence levels (✅ Verified, 🟢 Likely True, 🟡 Uncertain, 🔴 Likely False)
- **Cross-Validation Guarantees**: Every fact is verified against multiple independent sources
- **Conflict Detection**: Automatically flags conflicting information across sources
- Enhanced documentation with decision tree for agents
- New keywords: hallucination, cross-validation, verification, anti-hallucination

### Changed
- Focus shifted from "free search" to "hallucination prevention"
- All documentation updated to emphasize cross-validation and anti-hallucination
- Confidence scoring now explicit: HIGH (3+ sources), MEDIUM (2 sources), LOW (1 source)
- Repository description updated to highlight anti-hallucination capabilities

### Migration Guide

**No install or command migration was required in v14.x.**

The repository branding changed, but the supported install and command surface stayed:

```bash
pip install free-web-search-ultimate
search-web "query"
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
