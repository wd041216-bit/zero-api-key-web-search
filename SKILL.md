---
name: free-web-search-ultimate
version: "7.0.0"
description: >
  Zero-cost, privacy-first web search and browsing for AI agents.
  Supports precise intent control (text vs news), region targeting, and time filters.
  Powered by official ddgs and Yahoo with cross-validation and fault tolerance.
homepage: https://github.com/wd041216-bit/free-web-search-ultimate
---

# Free Web Search Ultimate v7.0 (Super Workflow Upgraded)

**Zero API Keys. High Reliability. Cross-Validated Results. Region & Intent Control.**

This skill provides AI agents with reliable web search and page browsing capabilities without relying on expensive API keys or external services.

## What's New in v7.0
- **Removed Auto-Intent Anti-Pattern**: Agents now explicitly choose between `text` and `news` modes, preventing technical queries containing words like "latest" from failing.
- **Region Support**: Added `--region` parameter (e.g., `zh-cn`, `en-us`) for localized search results.
- **Enhanced Fault Tolerance**: Reuses the underlying network client and gracefully handles timeouts, ensuring results are returned even under poor network conditions.
- **Improved Page Parsing**: Fixed title extraction bugs in `browse_page.py` for complex HTML structures.

## Features

- **Precise Intent Control**: Explicitly choose `text` for general knowledge or `news` for recent events with timestamps.
- **Region Targeting**: Get results tailored to specific languages and locations.
- **Time Filters**: Find the most recent information easily.
- **Cross-Validation**: Automatically groups and validates results across different engines to ensure credibility.
- **Clean Browsing**: Extracts pure text content from web pages, stripping out scripts, styles, and boilerplate.

## Quick Start

### 1. Web Search

Use `search_web.py` to search the internet. It returns cross-validated results with summaries.

```bash
# Basic usage (defaults to text search)
python scripts/search_web.py "Python 3.12 new features"

# Search for recent news (explicitly)
python scripts/search_web.py "OpenAI" --type news

# Search with region and time limit (Chinese results from past week)
python scripts/search_web.py "人工智能" --region zh-cn --timelimit w

# JSON output for agent parsing
python scripts/search_web.py "Python 3.12 new features" --json
```

**Agent Best Practices:**
- Use default `--type text` for technical documentation, tutorials, and general knowledge.
- Use `--type news` ONLY when searching for current events, breaking news, or recent company updates.
- Always use `--region` when searching in languages other than English (e.g., `--region zh-cn` for Chinese).

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
