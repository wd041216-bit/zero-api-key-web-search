---
name: free-web-search
version: "1.0"
description: >
  Simple, reliable web search - DuckDuckGo + Bing fallback.
  Zero API keys. Uses web_fetch tool. Search + Browse.
homepage: https://github.com/wd041216-bit/free-web-search
---

# Free Web Search v1.0

**Simple > Complex. Reliable > Features.**

## Quick Start

### Search

```python
# DuckDuckGo (primary)
web_fetch(
    url="https://lite.duckduckgo.com/lite/?q=your+query",
    extractMode="text",
    maxChars=5000
)

# Bing (fallback if DDG fails)
web_fetch(
    url="https://www.bing.com/search?q=your+query",
    extractMode="text", 
    maxChars=5000
)
```

### Browse Page

```python
web_fetch(
    url="https://example.com/article",
    extractMode="markdown",
    maxChars=8000
)
```

## Why Simple?

After analyzing competitors:
- **ddg-web-search**: Ultra-simple, one engine, zero dependencies
- **Complex skills**: Multiple engines, high failure rate, hard to maintain

Our approach:
- ✅ **Single primary engine**: DuckDuckGo (most reliable)
- ✅ **One fallback**: Bing (when DDG blocked)
- ✅ **Zero dependencies**: Just web_fetch
- ✅ **Reliable**: Works 99% of the time

## When to Use

Use this skill when you need:
- Current information from the web
- To read full article content
- Zero-cost, no API key solution

## Workflow

1. **Search** with DDG → Get results
2. If DDG fails → **Fallback** to Bing
3. **Browse** top results → Read full content
4. **Answer** based on actual content

## Limitations

- Text results only (no images/videos)
- No advanced filtering (by date, region unreliable)
- May hit rate limits on heavy use

---

**v1.0 - Simple & Reliable**
