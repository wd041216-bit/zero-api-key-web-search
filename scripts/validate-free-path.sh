#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEARXNG_URL="${ZERO_SEARCH_SEARXNG_URL:-${FREE_WEB_SEARCH_SEARXNG_URL:-${SEARXNG_URL:-}}}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ -z "$SEARXNG_URL" ]]; then
  echo "Set ZERO_SEARCH_SEARXNG_URL (or FREE_WEB_SEARCH_SEARXNG_URL / SEARXNG_URL) first." >&2
  exit 1
fi

for cmd in zero-search zero-verify zero-report python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
done

echo "Validating free dual-provider path against: $SEARXNG_URL"
echo

python3 - "$SEARXNG_URL" <<'PY'
import json
import sys
import urllib.request

url = sys.argv[1].rstrip("/") + "/search?q=python&format=json"
with urllib.request.urlopen(url, timeout=8) as response:
    payload = json.loads(response.read().decode("utf-8"))
assert isinstance(payload, dict)
assert "results" in payload
print("PASS preflight: SearXNG JSON endpoint is reachable.")
PY

(
  cd "$ROOT_DIR"
  zero-search "Python 3.13 release" --provider ddgs --provider searxng --json > "$TMP_DIR/search.json"
  zero-verify "Python 3.13 is the latest stable release" --provider ddgs --provider searxng --deep --max-pages 2 --json > "$TMP_DIR/verify.json"
  zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --provider ddgs --provider searxng --deep --json > "$TMP_DIR/report.json"
)

python3 - "$TMP_DIR" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
search = json.loads((root / "search.json").read_text(encoding="utf-8"))
verify = json.loads((root / "verify.json").read_text(encoding="utf-8"))
report = json.loads((root / "report.json").read_text(encoding="utf-8"))

assert search["metadata"]["providers_used"] == ["ddgs", "searxng"], search["metadata"]
assert verify["analysis"]["provider_diversity"] == 2, verify["analysis"]
assert report["analysis"]["provider_diversity"] == 2, report["analysis"]
assert not any("single-provider" in item.lower() for item in report["coverage_warnings"]), report["coverage_warnings"]

print("PASS zero-search: providers_used includes ddgs + searxng.")
print("PASS zero-verify: provider_diversity is 2.")
print("PASS zero-report: provider_diversity is 2 and no single-provider warning remains.")
print("PASS summary: free dual-provider path is healthy.")
PY
