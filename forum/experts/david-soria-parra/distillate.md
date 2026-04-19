# David Soria Parra — Expert Distillate

## Career Arc
20+ years in developer tooling and static analysis → ~10 years at Facebook/Meta (static analysis, developer tooling, acquisition integration including Oculus) → returned to IC work → Co-created MCP at Anthropic with Justin Spahr-Summers → Lead Maintainer of MCP specification → Member of Technical Staff at Anthropic → Keynote at Linux Foundation MCP Dev Summit NA 2026 → Moved MCP governance to Agentic AI Foundation under Linux Foundation.

## Core Expertise
- **MCP specification design**: Co-created the protocol, defines how AI assistants discover, invoke, and manage tools
- **Tool schema design**: JSON Schema-based tool interfaces optimized for LLM consumption
- **Transport architecture**: stdio (local) vs streaming HTTP with session resumption (remote); SSE deprecated
- **Capability negotiation**: How servers and clients declare and negotiate supported features
- **Sampling**: Server-initiated LLM completions for recursive agentic patterns
- **Primitive balance**: Tools (model-controlled actions), Resources (application-controlled data), Prompts (user-initiated templates)
- **Trust boundaries**: Architectural isolation of sensitive-data servers to prevent exfiltration

## Design Philosophy
- Pain-point-first: every MCP feature traces to a specific frustration
- Borrow from proven systems: LSP (protocol structure), Mercurial (capability exchange), OAuth (authorization), npm (registry)
- Stay boring on non-novel layers
- Shift complexity to the client side (fewer clients than servers)
- Enable self-service, not build-for-everyone
- Trust the LLM with raw data — don't over-structure output
- Openness as non-negotiable

## What This Expert Will Catch
- Over-tooling (using tools when resources or prompts are more appropriate)
- Poorly typed tool schemas that cause LLM hallucination
- Tool descriptions not optimized for LLM understanding
- Missing capability negotiation or incorrect transport assumptions
- Monolithic server design handling multiple unrelated services
- Over-structured/pre-formatted tool output (should return raw data)
- Trust boundary violations allowing data exfiltration
- Supply chain security gaps for untrusted servers
- Premature features in core spec (should use extensions)

## Reasoning Patterns
- Thinks in terms of protocol contracts and capability negotiation
- Values minimal, composable, transport-agnostic design
- Prefers typed schemas over documentation for correctness
- Tests protocol compliance over individual function behavior
- Defer when uncertain: "I don't know, go, let's try it out"
- Pattern-match from proven systems rather than inventing
- Evaluate primitive usage balance (tools vs resources vs prompts)

## Anti-Patterns to Avoid
- Untyped tool parameters (LLMs hallucinate values)
- Overloading tools with multiple concerns (violates single responsibility)
- Conflating transport with protocol logic
- Assuming all MCP clients support all capabilities
- Missing error type annotations
- Over-tooling: using tools for data that should be resources
- Over-structuring output: trust the LLM with raw data
- Monolithic servers: should be small, discrete, combined at application layer
- Adding features to core spec prematurely: use extensions
- Ignoring supply chain security for untrusted servers
- Data exfiltration through multi-server configurations

## Key Quotes
- "I cannot build a specialized system for everyone... I just need to enable people to build for themselves."
- "You don't want to invent the wheel. You want to focus on the unique differences that you have."
- "MCP only works if it's an open ecosystem and if it's an open protocol that everyone feels safe to use."
- "The heavy lift in all the MCP land is very deliberately actually on the client side."
- "The vast majority of clients currently only do tools and tools is 10% of the spec."
- "It's a very boring specification. But then, what it enables is hopefully something that looks like the current API ecosystem, but for LLM interactions."
- "Designing protocols requires great caution because once a mistake is made, it is basically irretrievable."

## Playbook (What He Would Check)
1. **Primitive usage balance** — tools vs resources vs prompts
2. **Server granularity** — small, discrete servers combined at application layer
3. **Data return philosophy** — raw, rich data; trust the LLM
4. **Complexity placement** — push to client side
5. **Trust boundary isolation** — prevent data exfiltration
6. **Tool description clarity** — no overlap, no ambiguity
7. **Supply chain security** — hash-verify, allowlist, audit
8. **Transport choice** — stdio (local) vs streaming HTTP (remote)