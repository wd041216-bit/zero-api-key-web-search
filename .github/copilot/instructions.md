# Zero-API-Key Web Search for GitHub Copilot

Use Zero-API-Key Web Search when Copilot needs live search results, source-backed verification, or page-level reading.

## Install

```bash
pip install zero-api-key-web-search
```

## Commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-verify "Python 3.13 is the latest stable release" --json
zero-browse "https://docs.python.org/3/whatsnew/"
```

## Guidance

- Search before answering factual or recent questions.
- Use `zero-browse` when snippets are too thin.
- Use `zero-verify` for support/conflict classification.
- Cite URLs and keep uncertainty visible.

## Limits

- `zero-verify` is heuristic and evidence-aware.
- The default provider path is `ddgs`.
- Conflicts are surfaced, not automatically resolved.

## License

MIT License.
