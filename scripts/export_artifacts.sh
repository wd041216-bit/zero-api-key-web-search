#!/usr/bin/env bash
# Export all verification artifacts into a single traceable JSON bundle.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="${1:-${REPO_ROOT}/artifacts_bundle.json}"

python3 -c "
import json, sys, pathlib

repo = pathlib.Path('$REPO_ROOT')
bundle = {}

# Claim ledger
ledger = repo / 'docs' / 'claim-ledger.md'
if ledger.exists():
    bundle['claim_ledger'] = ledger.read_text()

# Verification model
vm = repo / 'docs' / 'verification-model.md'
if vm.exists():
    bundle['verification_model'] = vm.read_text()

# Trust model (semantic oracle boundary)
tm = repo / 'docs' / 'trust-model.md'
if tm.exists():
    bundle['trust_model'] = tm.read_text()

# Evaluation
ev = repo / 'docs' / 'evaluation.md'
if ev.exists():
    bundle['evaluation'] = ev.read_text()

# Benchmarks
bm = repo / 'docs' / 'benchmarks.md'
if bm.exists():
    bundle['benchmarks'] = bm.read_text()

# Test results
import subprocess
result = subprocess.run(
    ['python3', '-m', 'pytest', 'tests/', '-q', '--tb=no'],
    capture_output=True, text=True, cwd=str(repo)
)
bundle['test_results'] = {
    'stdout': result.stdout,
    'returncode': result.returncode
}

# Version
init_file = repo / 'zero_api_key_web_search' / '__init__.py'
if init_file.exists():
    bundle['version_source'] = init_file.read_text()

json.dump(bundle, sys.stdout, indent=2)
" > "$OUTPUT"

echo "Artifacts bundle written to $OUTPUT"