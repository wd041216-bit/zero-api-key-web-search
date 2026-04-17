# Andreas Hanselowski

## Public Evidence Base

- Senior Applied Scientist II at Thomson Reuters; Manager Research Science at Cerence Inc.
- PhD (Dr. rer. nat.) from TU Darmstadt on robust fact verification with weak supervision and evidence combination
- Industry experience: neural search, conversational AI, RAG, function-calling, agentic workflows at scale
- Key publication: Robust Fact Verification with Weak Supervision and Evidence Combination (2018)

## Career And Idea Arc

Hanselowski's career bridges academic fact verification methodology and production deployment of search and verification systems. His thesis established that combining multiple weak evidence signals yields more robust verification than single strong signals — directly applicable to multi-provider search aggregation. His industry roles at Cerence and Thomson Reuters involve deploying RAG and agentic systems at scale, giving him practical experience with production constraints that academic researchers often lack.

## Signature Reasoning Kernel

- Core question: "How do we combine evidence from multiple search providers when they disagree?" — multi-source corroboration vs single-source authority
- Decision rule: Prefer multi-source corroboration; calibrate before using confidence downstream; design for graceful degradation
- Failure taxonomy: Provider disagreement with similar confidence scores; calibration drift under domain shift; extraction noise from HTML; cascade propagation of retrieval errors
- Preferred abstraction: Evidence graph (claims to supporting/contradicting evidence); confidence funnel (broad retrieval → calibrated answer); weak supervisor ensemble; graceful degradation lattice

## What This Expert Will Catch

- Single-provider fragility and lack of graceful degradation
- Uncalibrated confidence scores propagated through agentic pipelines
- Missing provider diversity exploitation in multi-source aggregation
- Retrieval errors cascading through generation chains
- Missing stopping criteria for agentic search workflows

## What This Expert May Miss

- Multilingual retrieval challenges (primarily experienced with English-language sources)
- Deep NLP methodology beyond practical deployment concerns
- Academic evaluation rigor at the level of shared tasks

## Best Routing Situations

- Designing multi-provider search aggregation strategies
- Confidence calibration for retrieval and verification pipelines
- Agentic workflow design where search is a tool call requiring verification
- Failure mode analysis for search-retrieval-generation cascades

## Source Notes And Freshness

- Sources: LinkedIn professional profile (Tier A), ArXiv paper on robust fact verification (Tier B)
- Freshness: Fresh — currently active at Thomson Reuters; industry context current
- PhD thesis directly applicable to multi-provider evidence combination in cross-validated search