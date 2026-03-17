<div align="center">
  <h1>🔍 Free Web Search Ultimate</h1>
  <p><strong>Zero-cost, privacy-first web search and browsing skill for AI agents.</strong></p>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
  [![CLI-Anything](https://img.shields.io/badge/CLI--Anything-Compatible-success.svg)](https://github.com/HKUDS/CLI-Anything)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-orange.svg)](https://github.com/openclaw/awesome-openclaw)
</div>

<br/>

This skill provides AI agents with reliable web search and page browsing capabilities without relying on expensive API keys, third-party MCP servers, or fragile HTML scrapers.

## 🏆 Why Choose This Skill? (See [Competitor Analysis](COMPETITOR_ANALYSIS.md))

- **Zero Cost & Privacy First**: No API keys required. No routing to third-party servers.
- **CLI-Anything Architecture**: Fully standard Python package with `entry_points` and REPL mode.
- **Multi-Modal**: Native support for `text`, `news`, `images`, `books`, and `videos` search.
- **Search + Browse**: Built-in `browse-page` command to extract clean text from any URL.
- **Agent Friendly**: Token-efficient JSON output designed specifically for LLM parsing.

## 🚀 What's New in v10.0

- **CLI-Anything Standard**: Fully refactored to match the CLI-Anything methodology. The project is now a standard Python package with `entry_points`.
- **PATH Execution**: After `pip install -e .`, agents can directly run `search-web` and `browse-page` from anywhere in the terminal, without needing the exact script path.
- **REPL Mode**: Running `search-web` without arguments now enters an interactive REPL mode, allowing continuous searching without re-initializing the environment.
- **Auto-Discoverable SKILL**: `SKILL.md` is now packaged inside the Python module via `package_data`. When agents install this tool, the skill definition is automatically discoverable.

## 📦 Installation

Install directly as a standard Python package (CLI-Anything Harness):

```bash
# Install directly from GitHub
pip install git+https://github.com/wd041216-bit/free-web-search-ultimate.git

# Or clone and install from source
git clone https://github.com/wd041216-bit/free-web-search-ultimate.git
cd free-web-search-ultimate
pip install -e .
```

## 💻 Usage

### 1. Web Search (`search-web`)

Use `search-web` to search the internet. It returns cross-validated results with summaries.

```bash
# Basic usage (defaults to text search)
search-web "Python 3.12 new features"

# Search for recent news
search-web "OpenAI" --type news

# Search for images (with advanced filters)
search-web "Python logo" --type images --size Large --color Blue

# Search for books/academic materials
search-web "machine learning" --type books

# Search for videos
search-web "how to tie a tie" --type videos

# Search with region and time limit (Chinese results from past week)
search-web "人工智能" --region zh-cn --timelimit w

# JSON output for agent parsing
search-web "Python 3.12 new features" --json
```

**🤖 Agent Best Practices:**
- Use default `--type text` for technical documentation, tutorials, and general knowledge.
- Use `--type news` ONLY when searching for current events, breaking news, or recent company updates.
- Use `--type images` when the user explicitly asks for pictures, photos, logos, or diagrams.
- Use `--type books` when looking for in-depth knowledge, authors, or publication years.
- Always use `--region` when searching in languages other than English (e.g., `--region zh-cn` for Chinese).

### 2. Browse Page (`browse-page`)

Use `browse-page` to read the full, clean text content of a specific URL.

```bash
# Read a page (default max 10,000 chars)
browse-page "https://docs.python.org/3/whatsnew/3.12.html"

# JSON output
browse-page "https://docs.python.org/3/whatsnew/3.12.html" --json
```

## 📄 License

MIT License
