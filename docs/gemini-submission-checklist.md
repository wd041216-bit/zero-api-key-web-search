# Gemini Submission Checklist

This repository is prepared for the current Gemini CLI extension-gallery path.

## What Gemini needs

- public GitHub repository
- root `gemini-extension.json`
- root `skills/` directory with at least one skill
- clear context file for Gemini users
- tagged release and installable package
- stable README with a fast verification path

## What is already done here

- Public repo: `wd041216-bit/zero-api-key-web-search`
- Extension manifest: [`gemini-extension.json`](../gemini-extension.json)
- Root skill: [`skills/zero-api-key-web-search/SKILL.md`](../skills/zero-api-key-web-search/SKILL.md)
- Gemini context: [`GEMINI.md`](../GEMINI.md) and [`.gemini/SKILL.md`](../.gemini/SKILL.md)
- Package published: [`zero-api-key-web-search` on PyPI](https://pypi.org/project/zero-api-key-web-search/)
- Tagged release: [`v20.0.0`](https://github.com/wd041216-bit/zero-api-key-web-search/releases/tag/v20.0.0)
- Fast verification path: [`README.md`](../README.md) and [`docs/ecosystem-readiness.md`](./ecosystem-readiness.md)
- Free dual-provider path: [`docs/searxng-self-hosted.md`](./searxng-self-hosted.md)

## Recommended repo metadata

- Homepage: `https://pypi.org/project/zero-api-key-web-search/`
- Topic: `gemini-cli-extension`
- Keep `gemini-cli`, `mcp`, `web-search`, and `fact-checking`

## Fast reviewer command

```bash
pip install zero-api-key-web-search
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Notes

- The package keeps legacy compatibility aliases for existing users, but all new documentation points to `zero-api-key-web-search`.
- The recommended free setup for stronger evidence reports is `ddgs + self-hosted SearXNG`.
