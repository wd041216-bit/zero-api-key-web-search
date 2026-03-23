---
name: cross-validated-search
description: >
  Claude Code skill for source-backed web search, page reading, and evidence-aware claim checking.
  Designed to reduce hallucination risk by surfacing corroborating and conflicting sources.
version: "15.0.0"
user-invocable: true
allowed-tools: "Bash"
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: |
            if echo "$CLAUDE_USER_PROMPT" | grep -qiE 'search|find|lookup|what is|who is|when did|where is|how many|latest|recent|最新|搜索|查询|查找'; then
              echo '[cross-validated-search] Factual query detected. Consider using search-web, browse-page, or verify-claim.'
            fi
---

# Cross-Validated Search for Claude Code

Use this skill when Claude Code needs current facts, supporting sources, or a quick support/conflict read on a claim.

## Install

```bash
pip install free-web-search-ultimate
```

## Core Commands

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --json
browse-page "https://docs.python.org/3/whatsnew/"
```

## Guidance

- Use `search-web` before answering factual or recent questions.
- Use `browse-page` when snippets are not enough to justify a claim.
- Use `verify-claim` when the user explicitly asks whether a claim looks supported.
- If support and conflict both appear, present the disagreement instead of pretending certainty.

## Limits

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- TLS verification is on by default; insecure mode is opt-in only.

## License

MIT License.
