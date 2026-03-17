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

## Why Use This Skill?

Many web search skills rely on paid APIs (like Brave, Google, or Bing API) or use single engines that often get blocked. 

**Free Web Search Ultimate** solves this by:
1. Not requiring any API keys.
2. Using the official `ddgs` library as the primary engine for extreme stability.
3. Using parallel fallback requests to Yahoo if the API fails.
4. Automatically decoding redirect links so agents can actually browse the results.

## License

MIT License
