# CLI Quickstart

## Install

```bash
pip install free-web-search-ultimate
```

## Search the web

```bash
search-web "latest Python release" --type news --timelimit w
```

## Read a page

```bash
browse-page "https://docs.python.org/3/whatsnew/"
```

## Check a claim

```bash
verify-claim "Python 3.13 is the latest stable release" --json
```

## Generate an evidence report

```bash
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Unlock the free dual-provider path

```bash
./scripts/start-searxng.sh
export CROSS_VALIDATED_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
./scripts/validate-free-path.sh
```
