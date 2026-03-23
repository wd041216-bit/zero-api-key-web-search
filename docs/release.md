# Release Guide

This repository is intended to behave like a small piece of public infrastructure. Releases should keep package metadata, documentation, and behavior aligned.

## Before you tag a release

1. Update code and tests.
2. Update `CHANGELOG.md`.
3. Verify `pyproject.toml` version.
4. Reinstall locally:

```bash
pip install -e ".[dev]"
```

## Local validation

```bash
python -m unittest discover -s tests -v
python -m build
twine check dist/*
```

Optional smoke checks:

```bash
search-web "python release" --json
verify-claim "Python 3.13 is the latest stable release" --json
browse-page "https://docs.python.org/3/whatsnew/" --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --json
```

Optional free-path checks:

```bash
./scripts/start-searxng.sh
export CROSS_VALIDATED_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
./scripts/validate-free-path.sh
```

## Documentation alignment

Check these files before release:

- `README.md`
- `GEMINI.md`
- `SKILL.md`
- `cross_validated_search/skills/SKILL.md`
- `.gemini/SKILL.md`
- `.claude-plugin/SKILL.md`
- `.codex/SKILL.md`
- `.github/copilot/instructions.md`

## Packaging alignment

Keep these names consistent:

- repository: `cross-validated-search`
- package: `cross-validated-search`
- module: `cross_validated_search`
- CLI: `search-web`, `browse-page`, `verify-claim`, `evidence-report`
- MCP: `cross-validated-search-mcp`

## Release policy

- prefer small, well-documented releases
- avoid promising platform behavior that does not have a reproducible example
- document limitations before expanding claims
