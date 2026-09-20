# Use Cases

Zero-API-Key Web Search is strongest when an agent needs evidence, not just links.

## Best-fit workflows

### 1. Claim checking before answering

Use `zero-verify` or `zero-report` when the model is about to answer a factual question that might be stale, contested, or expensive to get wrong.

Good examples:

- release status and version questions
- “is X still true?” checks
- current-event or policy claims
- anything where the agent should show why it believes the answer

### 2. Research workflows that need citations

Use `zero-search` to collect sources, then `zero-report` to compress them into a reviewable artifact with supporting and conflicting evidence.

Good examples:

- analyst notes
- briefings
- ecosystem reviews
- “should we trust this claim?” questions

### 3. Agent runtime toolchains

Use the MCP surface or bundled skill files when a runtime needs a reusable verification layer instead of a one-off script.

Good examples:

- Gemini-compatible skills
- Claude Code local skills
- OpenClaw / Manus workflow skills
- MCP-native clients

## When not to use it

This project is less compelling when all you need is:

- raw search results with no verification layer
- full-document RAG over a private corpus
- formal proof-level factual correctness

For that tradeoff discussion, see [why-not-just-search.md](./why-not-just-search.md).
