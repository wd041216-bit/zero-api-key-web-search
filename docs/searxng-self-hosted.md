# Self-Hosted SearXNG

The recommended free multi-provider path for this repository is:

- `ddgs` for zero-config search
- self-hosted `SearXNG` for a second independent provider

## Why this path

- no paid API dependency
- open source and self-controlled
- compatible with the current provider abstraction
- improves `provider_diversity` for `verify-claim` and `evidence-report`

## Quick start with Docker

The lowest-friction path in this repo is:

```bash
cp .env.searxng.example .env
./scripts/start-searxng.sh
export CROSS_VALIDATED_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
./scripts/validate-free-path.sh
```

## Compose template

This repo ships a ready-to-run compose file:

```bash
cp .env.searxng.example .env
docker compose -f docker-compose.searxng.yml up -d
```

## Manual Docker command

Run a local SearXNG instance:

```bash
docker run --rm -d \
  --name cross-validated-searxng \
  -p 8080:8080 \
  searxng/searxng:latest
```

Point Cross-Validated Search at it:

```bash
export CROSS_VALIDATED_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
```

Supported aliases:

- `CROSS_VALIDATED_SEARCH_SEARXNG_URL`
- `FREE_WEB_SEARCH_SEARXNG_URL`
- `SEARXNG_URL`

## Validate the setup

The repo ships a validation helper:

```bash
./scripts/validate-free-path.sh
```

Or run the commands manually:

```bash
search-web "Python 3.13 release" --provider ddgs --provider searxng --json
verify-claim "Python 3.13 is the latest stable release" --provider ddgs --provider searxng --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --provider ddgs --provider searxng --deep --json
```

Healthy output should show:

- `providers_used` includes both `ddgs` and `searxng`
- `provider_diversity` is `2`
- `coverage_warnings` no longer complain about a single-provider path

## Troubleshooting

- If bootstrap stalls, run `docker compose -f docker-compose.searxng.yml logs searxng`.
- If port `8080` is busy, change `SEARXNG_PORT` in `.env` and export a matching `CROSS_VALIDATED_SEARCH_SEARXNG_URL`.
- If validation fails on the preflight step, verify `http://127.0.0.1:8080/search?q=python&format=json` returns JSON from your instance.

## Notes

- Public SearXNG instances can work for experimentation, but they are not the recommended production path.
- Some public instances disable JSON output or apply stricter rate limits.
- For stable agent workflows, self-hosting is the better free option.
