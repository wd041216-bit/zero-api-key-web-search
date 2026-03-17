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

## Installation

1. Clone this repository to your agent's workspace.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

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

## Why Use This Skill?

Many web search skills rely on paid APIs (like Brave, Google, or Bing API) or use single engines that often get blocked. 

**Free Web Search Ultimate** solves this by:
1. Not requiring any API keys.
2. Using the official `ddgs` library as the primary engine for extreme stability.
3. Using parallel fallback requests to Yahoo if the API fails.
4. Automatically decoding redirect links so agents can actually browse the results.

## License

MIT License
