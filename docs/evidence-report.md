# Evidence Report

`evidence-report` is the flagship reviewer-facing workflow in this repository.

It combines:

- live search
- claim verification
- optional page-aware rescoring
- citation-ready source digests
- verdict rationale and coverage warnings

## Why it exists

Platform reviewers and agent runtimes often do not want raw search results or only a verdict.

They need one compact artifact that answers:

- what claim was evaluated
- what the verdict was
- why the verdict was reached
- which sources are worth citing
- what uncertainty still remains

## Output shape

The structured result includes:

- `executive_summary`
- `verification_summary`
- `verdict_rationale`
- `stance_summary`
- `coverage_warnings`
- `source_digest`
- `citations`
- `next_steps`

## When to use it

- when a platform indexer wants to evaluate the repo quickly
- when an agent needs a compact evidence package instead of raw search output
- when a claim is important enough to justify explicit uncertainty handling

## Current limits

- it still depends on heuristic verification, not proof-level reasoning
- default provider diversity is limited unless a second provider is configured, with self-hosted `searxng` as the recommended free path
- page-aware verification helps, but it is still not full-document entailment
