#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.searxng.yml"
DEFAULT_URL="http://127.0.0.1:8080"
SEARXNG_URL="${CROSS_VALIDATED_SEARCH_SEARXNG_URL:-$DEFAULT_URL}"
WAIT_SECONDS="${SEARXNG_WAIT_SECONDS:-90}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Docker Compose is required. Install Docker Desktop or docker-compose first." >&2
  exit 1
fi

echo "Starting self-hosted SearXNG with: ${COMPOSE_CMD[*]} -f $COMPOSE_FILE up -d"
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d

echo "Waiting for SearXNG readiness at: $SEARXNG_URL"
python3 - "$SEARXNG_URL" "$WAIT_SECONDS" <<'PY'
import json
import sys
import time
import urllib.error
import urllib.request

url = sys.argv[1].rstrip("/") + "/search?q=python&format=json"
deadline = time.time() + int(sys.argv[2])
last_error = "unknown"

while time.time() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, dict) and "results" in payload:
            print("SearXNG is ready.")
            sys.exit(0)
        last_error = "response_missing_results"
    except Exception as exc:  # noqa: BLE001
        last_error = str(exc)
    time.sleep(3)

print(f"SearXNG did not become ready in time: {last_error}", file=sys.stderr)
sys.exit(1)
PY

cat <<EOF

SearXNG bootstrap complete.

Recommended environment variable:
  export CROSS_VALIDATED_SEARCH_SEARXNG_URL="$SEARXNG_URL"

Next steps:
  1. export CROSS_VALIDATED_SEARCH_SEARXNG_URL="$SEARXNG_URL"
  2. "$ROOT_DIR/scripts/validate-free-path.sh"
  3. optionally copy values from "$ROOT_DIR/.env.searxng.example"

Stop the local instance later with:
  ${COMPOSE_CMD[*]} -f "$COMPOSE_FILE" down
EOF
