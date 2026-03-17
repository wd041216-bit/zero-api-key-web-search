# Free Web Search Ultimate v9.0 (Super Workflow Upgraded)

**Zero API Keys. Images Search Support. Un-truncated URLs. Optimized Network Usage.**

This skill provides AI agents with reliable web search and page browsing capabilities without relying on expensive API keys or external services.

## What's New in v9.0
- **New Images Search Type**: Added `--type images` support with rich filtering options (`size`, `color`, `type_image`, `license`). This is a unique capability rarely found in free search tools.
- **Un-truncated URLs**: Fixed an issue where CLI output truncated URLs (e.g., `...`), allowing agents to copy and use the full URL directly.
- **Optimized Network Usage**: Removed the redundant dual-task concurrency strategy. Replaced it with a single `max_results=30` request, saving 50% of network overhead while retrieving the same amount of data.
- **Token-Efficient Answer**: The `answer` field in JSON output is now a concise summary (Rank, Title, URL) instead of repeating full snippets, saving valuable LLM tokens.
- **Rank Field**: Replaced the ambiguous `credibility` score with a straightforward integer `rank` field.

## Features

- **Precise Intent Control**: Choose `text` (general), `news` (recent events), `images` (visuals), `books` (academic/publications), or `videos` (multimedia).
- **Region Targeting**: Get results tailored to specific languages and locations.
- **Time Filters**: Find the most recent information easily.
- **Cross-Validation**: Automatically groups and validates results to ensure credibility.
- **Clean Browsing**: Extracts pure text content from web pages, stripping out scripts and styles while preserving useful context.

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

# Search for recent news
python scripts/search_web.py "OpenAI" --type news

# Search for images (with advanced filters)
python scripts/search_web.py "Python logo" --type images --size Large --color Blue

# Search for books/academic materials
python scripts/search_web.py "machine learning" --type books

# Search for videos
python scripts/search_web.py "how to tie a tie" --type videos

# Search with region and time limit (Chinese results from past week)
python scripts/search_web.py "人工智能" --region zh-cn --timelimit w

# JSON output for agent parsing
python scripts/search_web.py "Python 3.12 new features" --json
```

**Agent Best Practices:**
- Use default `--type text` for technical documentation, tutorials, and general knowledge.
- Use `--type news` ONLY when searching for current events, breaking news, or recent company updates.
- Use `--type images` when the user explicitly asks for pictures, photos, logos, or diagrams.
- Use `--type books` when looking for in-depth knowledge, authors, or publication years.
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

Many web search skills rely on paid APIs (like Brave, Google, or Bing API) or use outdated HTML scraping methods that often get blocked. 

**Free Web Search Ultimate** solves this by:
1. Not requiring any API keys.
2. Using the official `ddgs` library as the primary engine for extreme stability.
3. Providing dedicated endpoints for text, news, images, books, and videos.
4. Outputting agent-friendly, token-efficient JSON responses.

## License

MIT License
