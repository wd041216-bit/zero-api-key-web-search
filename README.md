<div align="center">
  <img src="assets/banner.png" alt="Free Web Search Ultimate" width="100%"/>
  <h1>🔍 Free Web Search Ultimate</h1>
  <p><strong>Universal Search-First Knowledge Acquisition Plugin for LLMs</strong></p>
  <p><em>One install. Every LLM. Real-time knowledge. Zero cost.</em></p>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
  [![MCP Ready](https://img.shields.io/badge/MCP-Ready-purple.svg)](https://modelcontextprotocol.io/)
  [![CLI-Anything](https://img.shields.io/badge/CLI--Anything-Compatible-success.svg)](https://github.com/HKUDS/CLI-Anything)
  [![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-orange.svg)](https://github.com/openclaw/awesome-openclaw)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![free-web-search-ultimate MCP server](https://glama.ai/mcp/servers/wd041216-bit/free-web-search-ultimate/badges/score.svg)](https://glama.ai/mcp/servers/wd041216-bit/free-web-search-ultimate)
</div>

<br/>

> **Stop letting your LLM guess. Give it the ability to search.**

By default, every LLM—Claude, GPT-4, Gemini—answers questions from training data that can be months or years out of date. This plugin introduces a **Search-First Paradigm**: the LLM is instructed to use real-time web search as its **primary knowledge source**, not a fallback.

## 🏗️ Architecture

<div align="center">
  <img src="assets/architecture.png" alt="Architecture Diagram" width="90%"/>
</div>

One plugin, every ecosystem. Whether you use Claude Desktop, Cursor, OpenClaw, or a custom LangChain agent, this plugin connects your LLM to the live web through a unified interface.

## 🌟 The "Search-First" Paradigm

| Old Paradigm (Default LLM) | New Paradigm (This Plugin) |
|---|---|
| Answers from training data | Answers from live web search |
| Knowledge cutoff date | Always up-to-date |
| May hallucinate facts | Cites verifiable sources |
| Single knowledge source | Multi-source cross-validation |

When this plugin is installed, the AI agent is instructed to:
1. **Never Guess Facts** — Use `search-web` before answering any factual, technical, or real-time question.
2. **Override Internal Knowledge** — Even if the LLM "knows" the answer, it verifies via search for topics prone to change.
3. **Deep Verification** — If search snippets are insufficient, use `browse-page` to read the full source.
4. **Cite Sources** — Always provide the source URLs in the final answer.

## 📦 Installation

```bash
pip install git+https://github.com/wd041216-bit/free-web-search-ultimate.git
```

## 🔌 Integration Guide

### Claude Desktop & Cursor (via MCP)

Add to your `claude_desktop_config.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "free-web-search": {
      "command": "free-web-search-mcp",
      "args": []
    }
  }
}
```

That's it. Claude and Cursor will now have access to `search_web` and `browse_page` tools.

### OpenClaw (via CLI-Anything)

```bash
# Install and the skill is auto-discovered
pip install git+https://github.com/wd041216-bit/free-web-search-ultimate.git
```

OpenClaw reads the bundled `SKILL.md` and automatically loads the Search-First behavioral instructions.

### LangChain / Custom Agents

```python
from langchain.tools import Tool
import subprocess, json

def search_web(query: str) -> str:
    result = subprocess.run(
        ["search-web", query, "--json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data.get("answer", "No results found.")

search_tool = Tool(
    name="search_web",
    func=search_web,
    description="Search the web for real-time information. Use this before answering any factual question."
)
```

### OpenAI Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for real-time information, news, or facts. Always call this before answering factual questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "type": {"type": "string", "enum": ["text", "news", "images", "videos", "books"], "default": "text"}
                },
                "required": ["query"]
            }
        }
    }
]
```

## 💻 CLI Usage

### `search-web` — Web Search

```bash
# General knowledge
search-web "Python 3.13 new features"

# Breaking news
search-web "OpenAI GPT-5" --type news --timelimit w

# Images
search-web "neural network diagram" --type images

# Chinese search
search-web "人工智能最新进展" --region zh-cn

# JSON output for programmatic use
search-web "quantum computing" --json
```

### `browse-page` — Deep Page Reading

```bash
# Read full page content
browse-page "https://docs.python.org/3/whatsnew/3.13.html"

# JSON output
browse-page "https://arxiv.org/abs/2303.08774" --json
```

## 🏆 Why This Over Alternatives?

| Feature | This Plugin | Tavily API | Serper API | Bing Search API |
|---|---|---|---|---|
| Cost | **Free** | $0.01/req | $0.001/req | $3/1000 req |
| API Key Required | **No** | Yes | Yes | Yes |
| Privacy | **Local** | Cloud | Cloud | Cloud |
| MCP Support | **Yes** | Partial | No | No |
| CLI-Anything | **Yes** | No | No | No |
| Image Search | **Yes** | No | Yes | Yes |
| Book Search | **Yes** | No | No | No |
| Browse Page | **Yes** | Yes | No | No |

## 📄 License

MIT License — free for personal and commercial use.
