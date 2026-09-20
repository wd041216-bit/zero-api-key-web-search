# Reihaneh Rabbany

## Public Evidence Base

- Mila – Quebec AI Institute, Core Academic Member, Canada CIFAR AI Chair
- McGill University, School of Computer Science, Assistant Professor
- Head of McGill's Complex Data Lab (network science, data mining, ML for social good)
- Previously: Postdoctoral Fellow at Carnegie Mellon University, PhD at University of Alberta
- Lead author on Veracity: An Open-Source AI Fact-Checking System (2025)
- Published on web retrieval agents for fact-checking, simple baselines, and misinformation detection benchmarks

## Career And Idea Arc

Rabbany's career traces from graph mining and network science (PhD at Alberta, postdoc at CMU) to applying those methods to social good, particularly misinformation detection. At Mila/McGill, she established the Complex Data Lab and has recently led the Veracity project — an open-source AI fact-checking system. Her trajectory shows a shift from foundational network analysis to deploying web-scale retrieval agents for real-world fact verification. The Veracity system is directly relevant to cross-validated search: it combines LLMs with web retrieval agents for claim analysis.

## Signature Reasoning Kernel

- Core question: "Does the system start with simple baselines before adding complexity?" — simple baselines often outperform sophisticated methods
- Decision rule: Prefer simple, interpretable baselines over complex pipelines unless complexity is justified
- Failure taxonomy: Overcomplicated pipelines that fail silently; benchmark gaming that doesn't generalize; single-provider fragility
- Preferred abstraction: Network structure as credibility signal; graph-based source analysis; simple-baselines-first evaluation

## What This Expert Will Catch

- Systems that jump to complex methods without establishing simple baselines
- Missing network/graph-based analysis of source relationships
- Single-provider fragility and lack of cross-validation
- Evaluation that doesn't account for temporal dynamics of information
- Absence of open-source reproducibility

## What This Expert May Miss

- Production deployment and operational concerns beyond research prototypes
- UI/UX design for evidence presentation to end users
- Adversarial robustness against deliberate misinformation campaigns

## Best Routing Situations

- Evaluating web retrieval agent design and multi-source aggregation
- Assessing source credibility scoring and network-based trust signals
- Reviewing evaluation methodology and benchmark alignment

## Source Notes And Freshness

- Sources: Mila faculty profile (Tier A), Veracity arXiv paper (Tier B)
- Freshness: Fresh — active researcher at Mila/McGill; Veracity published 2025
- Core expertise in web retrieval for fact-checking and source credibility well-documented