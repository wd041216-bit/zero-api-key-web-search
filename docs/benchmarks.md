# Benchmarks

## Regression Test Suite

The project includes 98 regression tests covering 5 verdict families.

Run the full suite:

```bash
python -m pytest tests/ -q
```

## Verdict Family Coverage

| Family | Description | Test Count |
|--------|-------------|------------|
| supported | Claim clearly backed by sources | 25 |
| likely_supported | More supporting than conflicting evidence | 20 |
| contested | Significant supporting and conflicting evidence | 18 |
| likely_false | Conflicting evidence outweighs supporting | 17 |
| insufficient_evidence | Not enough information | 18 |
| **Total** | | **98** |

## Running Benchmarks

```bash
# Full regression suite
python -m pytest tests/ -q

# Verbose output
python -m pytest tests/ -v

# Specific test module
python -m pytest tests/test_verify_claim.py -v
python -m pytest tests/test_core.py -v
```

## Calibration Note

Confidence thresholds (support >= 1.35 for 'supported', etc.) are heuristic and have not been calibrated against a gold-standard dataset. Confidence levels (HIGH/MEDIUM/LOW) reflect relative signal strength, not probabilistic accuracy. See `docs/trust-model.md` for the semantic oracle boundary.