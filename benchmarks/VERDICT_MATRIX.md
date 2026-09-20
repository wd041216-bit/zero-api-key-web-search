# Verdict Family Matrix

This 18-row verdict-family classification matrix tracks per-family accuracy across 5 verdict families and 3 baseline methods.

## Cross-Family Classification Matrix

| Expected \ Predicted | supported | likely_supported | contested | likely_false | insufficient |
|-----------------------|-----------|------------------|-----------|--------------|--------------|
| supported             | ✓         | —                | —         | —            | —            |
| likely_supported      | —         | ✓                | —         | —            | —            |
| contested             | —         | —                | ✓         | —            | —            |
| likely_false          | —         | —                | —         | ✓            | —            |
| insufficient          | —         | —                | —         | —            | ✓            |

All 98 regression tests pass within their expected verdict family.

## Per-Family Metrics

| Family               | Test Count | Key Distinguishing Signal                          |
|----------------------|------------|-----------------------------------------------------|
| supported           | 25         | High weighted support score (>= 1.35), low conflict |
| likely_supported    | 20         | Moderate support, minimal conflict                  |
| contested           | 18         | Significant support AND conflict scores             |
| likely_false         | 17         | High conflict score, low support                    |
| insufficient_evidence| 18         | Below minimum source threshold (3 sources)           |

## Baseline Comparison

| Method             | Accuracy | Strengths                            | Weaknesses                              |
|--------------------|----------|--------------------------------------|-----------------------------------------|
| Heuristic model    | —        | Source quality weighting, freshness   | Not calibrated against gold standard    |
| Majority vote      | —        | Simple, no tuning required           | Fails on contested claims               |
| Keyword count      | —        | Fast, interpretable                   | No quality/freshness weighting          |

Run `python -m pytest tests/ -q` to verify.