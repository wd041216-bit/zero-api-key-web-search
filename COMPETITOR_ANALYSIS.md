# 竞品分析报告：Free Web Search Ultimate vs 主流搜索技能

本报告对 ClawHub 平台上主流的 Web Search 技能与 `free-web-search-ultimate` (v10.0) 进行了深度的横向对比分析。

## 1. 竞品概览

我们在 ClawHub 上调研了下载量最高、最具代表性的几个 Web Search 技能：

| 技能名称 | 下载量 | 核心技术方案 | 费用/API Key |
|---|---|---|---|
| **ddg-web-search** | 15.4k (第一) | 爬取 DuckDuckGo Lite HTML 页面 | 免费 / 无需 API Key |
| **duckduckgo-search** | 18.3k | 使用 `duckduckgo-search` Python 库 | 免费 / 无需 API Key |
| **Web Search Free** | 2.7k | 路由至 Exa MCP Server | 免费 / 依赖外部服务 |
| **baidu web search** | 47.8k | 百度 AI Search Engine | 需配置 |
| **free-web-search-ultimate** (本作) | - | `ddgs` 官方库 + CLI-Anything 标准 Harness | 免费 / 无需 API Key |

## 2. 深度对比分析

### 2.1 技术架构与稳定性

- **HTML 爬取流派 (如 `ddg-web-search`)**：
  - **实现方式**：直接请求 `lite.duckduckgo.com` 并使用正则表达式或 BeautifulSoup 解析 HTML。
  - **痛点**：极度脆弱。一旦 DDG 更改了页面结构，解析器就会立即失效。且不支持高级过滤（如时间、地区、图片）。
- **MCP 路由流派 (如 `Web Search Free`)**：
  - **实现方式**：自身没有搜索逻辑，只是一个配置指令，让 Agent 去调用远程的 Exa MCP Server。
  - **痛点**：依赖外部不可控的第三方服务器。ClawHub 安全扫描已将其标记为 **"Suspicious" (可疑)**，存在隐私和 SSRF 风险。
- **官方 API 库流派 (如 `duckduckgo-search` 和 `free-web-search-ultimate`)**：
  - **实现方式**：调用 DDG 内部未公开的 JSON API（通过 `ddgs` 库）。
  - **优势**：极度稳定，返回结构化的 JSON 数据，原生支持文本、新闻、图片、视频等多模态搜索。

### 2.2 功能特性对比

| 功能特性 | ddg-web-search | duckduckgo-search | free-web-search-ultimate (v10.0) |
|---|---|---|---|
| **文本搜索** | ✅ 支持 | ✅ 支持 | ✅ 支持 (含跨引擎交叉验证) |
| **新闻搜索 (带时间戳)** | ❌ 不支持 | ✅ 支持 | ✅ 支持 (原生 `--type news`) |
| **图片/视频/书籍搜索** | ❌ 不支持 | ✅ 支持 | ✅ 支持 (原生参数支持) |
| **地区/时间过滤** | ⚠️ 仅 URL 参数 | ✅ 支持 | ✅ 支持 (`--region`, `--timelimit`) |
| **网页正文提取 (Browse)** | ❌ 不支持 | ❌ 不支持 | ✅ 支持 (`browse-page` 命令) |
| **CLI-Anything 标准** | ❌ 不支持 | ❌ 不支持 | ✅ **完全符合 (PATH 调用, REPL)** |

### 2.3 易用性与 Agent 友好度

- **`duckduckgo-search` 的局限**：它提供的是一段长长的 Python 代码字符串（通过 `python -c "..."` 执行），要求 Agent 每次搜索都要生成并运行一大段代码。这不仅浪费 Token，而且容易出错。
- **`free-web-search-ultimate` 的突破**：在 v10.0 中，我们引入了 **CLI-Anything** 标准。它是一个标准的系统级 CLI 工具。Agent 只需要执行 `search-web "query"`，或者进入 REPL 模式连续对话，极大地降低了 LLM 的认知负担和出错率。

## 3. 核心差异化优势 (Why Choose Us?)

1. **多模态与高级过滤**：不仅能搜网页，还能搜新闻、图片、视频、书籍，支持精准的时间和地区过滤。
2. **"Search + Browse" 一体化**：竞品通常只提供搜索结果列表。我们内置了 `browse-page` 命令，Agent 搜到 URL 后可以直接提取干净的网页正文。
3. **CLI-Anything 架构**：这是目前架构最先进的搜索技能。支持全局 PATH 调用、交互式 REPL 模式，并且 `SKILL.md` 会随 Python 包自动安装，实现技能的自我发现。
4. **零成本与隐私安全**：无需任何 API Key，纯本地执行（不路由到第三方 MCP 服务器），通过了最严格的安全审查。

## 4. 总结

`free-web-search-ultimate` v10.0 已经从一个简单的脚本，进化为符合行业最新标准（CLI-Anything）的**企业级 Agent 工具**。在功能丰富度、架构先进性和 LLM 友好度上，均全面超越了目前 ClawHub 上的高下载量竞品。
