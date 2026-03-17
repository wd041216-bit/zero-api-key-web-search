# 🔍 Free Web Search v1.0

> **Simple, reliable web search for AI agents.**
> 
> No API keys. No complex setup. Just works.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Why Simple?

After analyzing 15+ competing web search skills, we learned:

- **Complex skills** = More failure points, harder maintenance
- **Simple skills** = Reliable, easy to understand, just works

**Our philosophy:**
- ✅ One primary engine (DuckDuckGo - most reliable)
- ✅ One fallback (Bing - when needed)
- ✅ Zero dependencies (just Python stdlib)
- ✅ Actually works

---

## 🚀 Quick Start

### Install

```bash
# OpenClaw
clawhub install free-web-search

# Or manual
git clone https://github.com/wd041216-bit/free-web-search.git
```

### Search

```bash
python scripts/search.py "your query"
```

### Browse

```bash
python scripts/browse.py "https://example.com"
```

### Python API

```python
from scripts.search import search_ddg, search_bing

# Search
result = search_ddg("Python tutorials")

# Browse
from scripts.browse import browse_page
content = browse_page("https://docs.python.org")
```

---

## 🎯 Features

| Feature | Status | Notes |
|---------|--------|-------|
| DuckDuckGo Search | ✅ | Primary engine, most reliable |
| Bing Fallback | ✅ | When DDG blocked |
| Page Browsing | ✅ | Extract text content |
| Zero Dependencies | ✅ | Python stdlib only |
| No API Keys | ✅ | Completely free |

---

## 📊 Comparison

| Skill | Engines | Dependencies | Complexity | Reliability |
|-------|---------|--------------|------------|-------------|
| ddg-web-search | 1 | 0 | ⭐ | ⭐⭐⭐ |
| **free-web-search** | 2 | 0 | ⭐⭐ | ⭐⭐⭐ |
| Complex skills | 5+ | Many | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**We aim for the sweet spot:** Simple enough to be reliable, robust enough for real use.

---

## 🔒 Privacy

- No API keys required
- No tracking
- No data collection
- Searches go directly to DDG/Bing

---

## 🛠️ Development

```bash
# Test search
python scripts/search.py "test query"

# Test browse
python scripts/browse.py "https://example.com"
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

**Made with ❤️ for the OpenClaw community.**
