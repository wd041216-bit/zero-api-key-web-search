# Claude Code Setup

`zerosieve` can be used from Claude Code in two complementary ways:

1. install the Python package so the CLI and MCP surfaces are available
2. place or symlink the bundled skill from `.claude/skills/zerosieve/SKILL.md`

## Install the package

```bash
pip install zerosieve
```

## Use the bundled Claude skill

From the repository root, copy or symlink:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/.claude/skills/zerosieve" ~/.claude/skills/zerosieve
```

If you prefer not to symlink, copy the `zerosieve` folder into your Claude skill directory.

## Recommended workflow

Use the skill when Claude Code should:

- search before answering a factual or time-sensitive question
- show supporting and conflicting evidence explicitly
- browse a full page when snippets are not enough
- generate one compact report with verdict, citations, and next steps

Typical flow:

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --deep --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Free stronger setup

For the strongest free path, pair `ddgs` with self-hosted SearXNG:

```bash
./scripts/start-searxng.sh
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
```

Then rerun `verify-claim` or `evidence-report` with `--deep`.
