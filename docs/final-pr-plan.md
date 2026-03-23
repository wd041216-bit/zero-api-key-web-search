# Final PR Plan

This document packages the current work into a reviewer-friendly PR plan for the final collection-grade push.

## Recommended PR title

`feat: ship collection-grade evidence reports and turnkey free self-hosted SearXNG path`

## Recommended PR summary

This PR turns Cross-Validated Search into a stronger ecosystem-ready repository by:

- promoting `evidence-report` into a true reviewer-facing flagship workflow
- improving report explainability with rationale, stance summaries, and coverage warnings
- making the recommended free path (`ddgs + self-hosted SearXNG`) substantially easier to bootstrap
- adding deterministic tests, benchmark coverage, and release/packaging guardrails

## Reviewer walkthrough

1. Start with [README.md](../README.md).
2. Check [docs/ecosystem-readiness.md](./ecosystem-readiness.md).
3. Review [docs/evidence-report.md](./evidence-report.md) for the flagship output contract.
4. Review [docs/searxng-self-hosted.md](./searxng-self-hosted.md) and the bootstrap assets:
   - [docker-compose.searxng.yml](../docker-compose.searxng.yml)
   - [scripts/start-searxng.sh](../scripts/start-searxng.sh)
   - [scripts/validate-free-path.sh](../scripts/validate-free-path.sh)
5. Verify regression and packaging confidence:
   - [benchmarks/run_benchmark.py](../benchmarks/run_benchmark.py)
   - [tests](../tests)
   - [.github/workflows/ci.yml](../.github/workflows/ci.yml)

## Suggested PR body

### What changed

- Added a flagship `evidence-report` workflow with citation-ready digests, verdict rationale, stance summaries, coverage warnings, and next steps.
- Upgraded free-path guidance so the repo actively recommends self-hosted `SearXNG` as the no-cost second provider.
- Added turnkey local bootstrap assets for SearXNG via compose and helper scripts.
- Expanded tests, benchmark coverage, and release-facing templates.

### Why this matters

- reviewers can now audit one high-level workflow instead of stitching together raw tools
- self-hosted users can reach dual-provider verification with lower friction
- ecosystem indexers get clearer docs, stronger trust signals, and better operational guidance

### Validation

```bash
python -m unittest discover -s tests -v
python benchmarks/run_benchmark.py --json
python -m build
twine check dist/*
```

## Suggested follow-up PRs

1. add a health-check-aware SearXNG compose stack with persistence and optional rate limiting
2. improve report-level conflict summarization beyond titles/domains
3. increase benchmark realism with broader claims and provider-specific fixtures
