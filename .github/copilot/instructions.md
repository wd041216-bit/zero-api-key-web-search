# Cross-Validated Search for GitHub Copilot

Use Cross-Validated Search when Copilot needs live search results, source-backed verification, or page-level reading.

## Install

```bash
pip install cross-validated-search
```

## Commands

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --json
browse-page "https://docs.python.org/3/whatsnew/"
```

## Guidance

- Search before answering factual or recent questions.
- Use `browse-page` when snippets are too thin.
- Use `verify-claim` for support/conflict classification.
- Cite URLs and keep uncertainty visible.

## Limits

- `verify-claim` is heuristic and evidence-aware.
- The default provider path is `ddgs`.
- Conflicts are surfaced, not automatically resolved.

## License

MIT License.
