# CLI Quickstart

## Install

```bash
pip install zero-api-key-web-search
```

## Search the web

```bash
zero-search "latest Python release" --type news --timelimit w
```

## Read a page

```bash
zero-browse "https://docs.python.org/3/whatsnew/"
```

## Check a claim

```bash
zero-verify "Python 3.13 is the latest stable release" --json
```

## Generate an evidence report

```bash
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Unlock the free dual-provider path

```bash
./scripts/start-searxng.sh
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
./scripts/validate-free-path.sh
```
