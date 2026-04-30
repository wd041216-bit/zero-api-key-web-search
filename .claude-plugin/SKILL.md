---
name: zero-api-key-web-search
description: >
  Claude Code skill for source-backed web search, page reading, and evidence-aware claim checking.
  Designed to reduce hallucination risk by surfacing corroborating and conflicting sources.
version: "20.0.0"
user-invocable: true
allowed-tools: "Bash"
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: |
            if echo "$CLAUDE_USER_PROMPT" | grep -qiE 'search|find|lookup|what is|who is|when did|where is|how many|latest|recent|最新|搜索|查询|查找'; then
              echo '[zero-api-key-web-search] Factual query detected. Consider using zero-search, zero-browse, or zero-verify.'
            fi
---

# Zero-API-Key Web Search for Claude Code

Use this skill when Claude Code needs current facts, supporting sources, or a quick support/conflict read on a claim. The default path is free; optional providers are discoverable for stronger coverage.

## Install

```bash
pip install zero-api-key-web-search
```

## Core Commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-search providers
zero-verify "Python 3.13 is the latest stable release" --json
zero-browse "https://docs.python.org/3/whatsnew/"
```

## Guidance

- Use `zero-search` before answering factual or recent questions.
- Use `zero-browse` when snippets are not enough to justify a claim.
- Use `zero-verify` when the user explicitly asks whether a claim looks supported.
- If support and conflict both appear, present the disagreement instead of pretending certainty.
- Use `zero-search providers` when the user asks what search backends are available.
- Use optional Bright Data only when configured or explicitly requested. New users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- Bright Data is optional and should not receive queries unless configured or requested.
- TLS verification is on by default; insecure mode is opt-in only.

## License

MIT License.
