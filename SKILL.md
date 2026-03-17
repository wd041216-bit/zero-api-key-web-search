---
name: free-web-search-ultimate
version: "6.0.0"
description: >
  Zero-cost, privacy-first web search and browsing for AI agents.
  Supports both general text search and dedicated news search with time filters.
  Powered by official ddgs and Yahoo with cross-validation.
homepage: https://github.com/wd041216-bit/free-web-search-ultimate
---

# Free Web Search Ultimate v6.0 (Super Workflow Upgraded)

**Zero API Keys. High Reliability. Cross-Validated Results. News & Time Filters.**

This skill provides AI agents with reliable web search and page browsing capabilities without relying on expensive API keys or external services.

## What's New in v6.0
- **News Search Mode**: Automatically detects news-related queries and uses a dedicated news engine with timestamps.
- **Time Filtering**: Added `--timelimit` support (`d` for day, `w` for week, `m` for month, `y` for year).
- **Streamlined Engines**: Removed redundant HTML scraping, relying purely on the official `ddgs` metasearch engine and Yahoo fallback.

## Features

- **Dual Mode Search**: Automatically switches between `text` and `news` search based on query intent.
- **Time Filters**: Find the most recent information easily.
- **Cross-Validation**: Automatically groups and validates results across different engines to ensure credibility.
- **Clean Browsing**: Extracts pure text content from web pages, stripping out scripts, styles, and boilerplate.

## Quick Start

### 1. Web Search

Use `search_web.py` to search the internet. It returns cross-validated results with summaries.

```bash
# Basic usage
python scripts/search_web.py "Python 3.12 new features"

# Search for recent news (auto-detected or forced)
python scripts/search_web.py "OpenAI latest news" --type news

# Search with time limit (past week)
python scripts/search_web.py "machine learning" --timelimit w

# JSON output for agent parsing
python scripts/search_web.py "Python 3.12 new features" --json
```

### 2. Browse Page

Use `browse_page.py` to read the full content of a specific URL.

```bash
# Read a page (default max 10,000 chars)
python scripts/browse_page.py "https://docs.python.org/3/whatsnew/3.12.html"

# JSON output
python scripts/browse_page.py "https://docs.python.org/3/whatsnew/3.12.html" --json
```

## Requirements

- Python 3.8+
- `beautifulsoup4`
- `lxml`
- `ddgs`

```bash
pip install -r requirements.txt
```
