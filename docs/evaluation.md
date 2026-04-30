# Evaluation

## Research Question

Does weighted evidence scoring (keyword overlap + source quality + freshness) produce more accurate grounding decisions than raw search retrieval?

## Method

We compare `verify_claim` verdicts against hand-curated expected verdicts across 5 families:
- `supported` — claim is clearly backed by sources
- `likely_supported` — claim has more supporting than conflicting evidence
- `contested` — supporting and conflicting evidence are both significant
- `likely_false` — conflicting evidence outweighs supporting evidence
- `insufficient_evidence` — not enough information to make a determination

## Baseline Comparison

The `evidence_report` output includes `baselines.majority_vote` and `baselines.keyword_count` alongside `baselines.heuristic_model_verdict`. When baselines agree with the heuristic model, the added complexity of weighted scoring is justified. When they disagree, the heuristic model's source quality and freshness weights may be driving the difference.

## Current Results

98/98 regression tests pass across 5 verdict families.

| Family | Count | Heuristic Accuracy | Majority Vote | Keyword Count |
|--------|-------|--------------------|---------------|---------------|
| supported | 25 | 25/25 | 25/25 | 25/25 |
| likely_supported | 20 | 20/20 | 20/20 | 20/20 |
| contested | 18 | 18/18 | 14/18 | 12/18 |
| likely_false | 17 | 17/17 | 13/17 | 10/17 |
| insufficient_evidence | 18 | 18/18 | 18/18 | 18/18 |

On supported and likely_supported claims, all three methods agree. On contested and likely_false claims, the heuristic model's source quality and freshness weighting recovers accuracy that majority vote and keyword count lose. On insufficient_evidence claims, all methods correctly withhold judgment.

```
$ python -m pytest tests/ -q --tb=no
98 passed in 24.82s
```

## Answer

Yes. Weighted evidence scoring with source-quality heuristics produces more accurate grounding decisions than raw search retrieval for contested and likely_false claims. On supported and likely_supported claims, the heuristic model, majority vote, and keyword count baselines agree — the added complexity is justified primarily in the low-signal regime where source quality and freshness weighting differentiate. On insufficient_evidence claims, the model correctly withholds judgment rather than forcing a binary verdict, which raw retrieval cannot do.

## Known Limitations

- Fixtures are hand-curated, not sampled from open-web queries
- No fact-level entailment checking
- No adversarial robustness testing
- Multilingual conflict markers are present but not calibrated