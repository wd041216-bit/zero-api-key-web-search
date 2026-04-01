"""Shared search core used by CLI, MCP, and compatibility wrappers."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

from cross_validated_search.browse_page import browse
from cross_validated_search.providers import DdgsProvider, SearchProvider, SearxngProvider, TavilyProvider


@dataclass
class Source:
    """A single search result source."""

    url: str
    title: str
    snippet: str = ""
    rank: int = 0
    engine: str = ""
    cross_validated: bool = False
    date: str = ""
    extra: Dict | None = None

    def __post_init__(self) -> None:
        if self.extra is None:
            self.extra = {}


@dataclass
class Answer:
    """Structured result returned by a search operation."""

    query: str
    search_type: str
    answer: str
    confidence: str
    sources: List[Source]
    validation: Dict
    metadata: Dict
    elapsed_ms: int


@dataclass
class VerificationResult:
    """Structured result returned by claim verification."""

    claim: str
    verdict: str
    confidence: str
    summary: str
    supporting_sources: List[Source]
    conflicting_sources: List[Source]
    neutral_sources: List[Source]
    analysis: Dict
    metadata: Dict
    elapsed_ms: int


@dataclass
class EvidenceReportResult:
    """Structured result returned by the flagship evidence-report workflow."""

    query: str
    claim: str
    verdict: str
    confidence: str
    executive_summary: str
    verification_summary: str
    verdict_rationale: List[str]
    stance_summary: Dict
    coverage_warnings: List[str]
    source_digest: List[Dict]
    citations: List[str]
    next_steps: List[str]
    analysis: Dict
    metadata: Dict
    elapsed_ms: int


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}

CONFLICT_MARKERS = (
    "not",
    "false",
    "incorrect",
    "misleading",
    "disputed",
    "debunked",
    "denied",
    "deny",
    "contradict",
    "contrary",
    "no evidence",
    "fact check",
)

CONFLICT_PATTERNS = tuple(
    re.compile(rf"\b{re.escape(marker)}\b", re.IGNORECASE)
    for marker in CONFLICT_MARKERS
)

HIGH_TRUST_SUFFIXES = (".gov", ".edu", ".ac.uk", ".mil")
MEDIUM_TRUST_SUFFIXES = (".org", ".int")
OFFICIAL_DOMAIN_MARKERS = (
    "docs.",
    "developer.",
    "developers.",
    "api.",
    "official",
    "support.",
    "help.",
    "standards",
    "spec",
    "release",
)
QUALITY_TEXT_MARKERS = (
    "official",
    "documentation",
    "release notes",
    "press release",
    "research",
    "study",
    "report",
)
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%b %d, %Y",
    "%B %d, %Y",
)

class UltimateSearcher:
    """Search implementation backing the public package surface."""

    def __init__(
        self,
        timeout: int = 15,
        min_sources: int = 3,
        providers: Optional[List[SearchProvider]] = None,
        browse_func: Optional[Callable[..., dict]] = None,
    ):
        self.timeout = timeout
        self.min_sources = min_sources
        self.providers = providers or self._default_providers()
        self.browse_func = browse_func or browse

    def _default_providers(self) -> List[SearchProvider]:
        providers: List[SearchProvider] = [DdgsProvider(timeout=self.timeout)]
        searxng = SearxngProvider(timeout=self.timeout)
        if searxng.is_configured():
            providers.append(searxng)
        tavily = TavilyProvider(timeout=self.timeout)
        if tavily.is_configured():
            providers.append(tavily)
        return providers

    def _provider_guidance(self) -> Dict:
        searxng = SearxngProvider(timeout=self.timeout)
        configured = searxng.is_configured()
        tavily_configured = TavilyProvider.is_configured()
        return {
            "free_recommended_pair": ["ddgs", "searxng"],
            "paid_option": "tavily",
            "searxng_configured": configured,
            "tavily_configured": tavily_configured,
            "searxng_env_vars": list(SearxngProvider.ENV_VARS),
            "tavily_env_vars": ["TAVILY_API_KEY"],
            "free_setup_hint": (
                "Self-host a SearXNG instance and point "
                f"{SearxngProvider.ENV_VARS[0]} to it for a free dual-provider path."
            ),
            "tavily_setup_hint": (
                "Set TAVILY_API_KEY to enable Tavily as a paid provider option "
                "(1,000 free API credits/month)."
            ),
            "recommended_next_step": (
                "Free dual-provider path is active."
                if configured
                else (
                    "Configure a self-hosted SearXNG instance via "
                    f"{SearxngProvider.ENV_VARS[0]} to unlock a free second provider, "
                    "or set TAVILY_API_KEY for a paid option."
                )
            ),
        }

    def _provider_registry(self) -> Dict[str, SearchProvider]:
        return {provider.name: provider for provider in self.providers}

    def _normalize_provider_names(self, providers: Optional[List[str]]) -> List[str]:
        registry = self._provider_registry()
        if not providers:
            return list(registry.keys())

        normalized: List[str] = []
        for provider in providers:
            value = (provider or "").strip().lower()
            if not value or value in normalized:
                continue
            if value not in registry:
                supported = ", ".join(sorted(registry.keys()))
                raise ValueError(
                    f"Unsupported provider '{provider}'. Supported providers: {supported}"
                )
            normalized.append(value)

        return normalized or list(registry.keys())

    def _provider_results_to_sources(
        self,
        provider_name: str,
        search_type: str,
        provider_results: List,
    ) -> List[Source]:
        sources: List[Source] = []
        for result in provider_results:
            if not result.url:
                continue
            sources.append(
                Source(
                    url=result.url,
                    title=result.title,
                    snippet=result.snippet,
                    rank=0,
                    engine=f"{provider_name.upper()}-{search_type.capitalize()}",
                    date=result.date,
                    extra=dict(result.metadata or {}),
                )
            )
        return sources

    def _search_provider(
        self,
        provider_name: str,
        query: str,
        search_type: str,
        timelimit: Optional[str],
        region: str,
        max_results: int,
        **kwargs,
    ) -> List[Source]:
        registry = self._provider_registry()
        provider = registry.get(provider_name)
        if provider is None:
            return [
                Source(
                    url="error",
                    title=f"Error: unsupported provider {provider_name}",
                    engine="error",
                )
            ]

        try:
            provider_results = provider.search(
                query=query,
                search_type=search_type,
                timelimit=timelimit,
                region=region,
                max_results=max_results,
                **kwargs,
            )
        except Exception as exc:
            return [
                Source(
                    url="error",
                    title=f"Error: {provider_name}: {exc}",
                    engine="error",
                )
            ]

        return self._provider_results_to_sources(
            provider_name=provider_name,
            search_type=search_type,
            provider_results=provider_results,
        )

    def _cross_validate(self, all_results: List[Source]) -> List[Source]:
        """Deduplicate results and rank corroborated URLs first."""
        url_groups: Dict[str, List[Source]] = {}
        for result in all_results:
            if result.url == "error":
                continue

            simplified = re.sub(r"^https?://(www\.)?", "", result.url).rstrip("/")
            simplified = simplified.split("#")[0].split("?")[0]
            if not simplified:
                continue
            url_groups.setdefault(simplified, []).append(result)

        validated: List[Source] = []
        for group in url_groups.values():
            best_source = group[0]
            if len(group) >= 2:
                best_source.cross_validated = True
                best_source.engine = f"{best_source.engine} (x{len(group)})"

            valid_snippets = [item.snippet for item in group if len(item.snippet) > 20]
            if valid_snippets:
                best_source.snippet = max(valid_snippets, key=len)

            validated.append(best_source)

        validated.sort(key=lambda item: item.cross_validated, reverse=True)
        for index, source in enumerate(validated, 1):
            source.rank = index

        return validated

    def search(
        self,
        query: str,
        search_type: str = "text",
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        providers: Optional[List[str]] = None,
        **kwargs,
    ) -> Answer:
        """Search the web and return a structured answer."""
        start_time = time.time()
        max_results = 30 if search_type == "text" else 20
        selected_providers = self._normalize_provider_names(providers)

        raw_results: List[Source] = []
        attempted_providers: List[str] = []
        successful_providers: List[str] = []
        for provider in selected_providers:
            attempted_providers.append(provider)
            provider_results = self._search_provider(
                provider_name=provider,
                query=query,
                search_type=search_type,
                timelimit=timelimit,
                region=region,
                max_results=max_results,
                **kwargs,
            )
            raw_results.extend(provider_results)
            if any(result.url != "error" for result in provider_results):
                successful_providers.append(provider)

        all_results: List[Source] = []
        errors: List[str] = []
        for result in raw_results:
            if result.url == "error":
                errors.append(result.title)
            else:
                all_results.append(result)

        validated_results = self._cross_validate(all_results)

        if validated_results:
            answer_parts = []
            for index, source in enumerate(validated_results[:5], 1):
                badge = "✓" if source.cross_validated else "○"
                answer_parts.append(f"{index}. {badge} [{source.title}]({source.url})")
            answer_text = "Top Sources:\n" + "\n".join(answer_parts)
        else:
            error_detail = f" (Errors: {'; '.join(errors)})" if errors else ""
            answer_text = (
                "No results found. The search engine may be rate-limited."
                f"{error_detail}"
            )

        cross_count = sum(1 for source in validated_results if source.cross_validated)
        confidence = "HIGH" if cross_count >= 2 else ("MEDIUM" if validated_results else "LOW")

        return Answer(
            query=query,
            search_type=search_type,
            answer=answer_text,
            confidence=confidence,
            sources=validated_results[:max_results],
            validation={
                "total_results": len(all_results),
                "unique_results": len(validated_results),
                "cross_validated": cross_count,
                "min_sources_target": self.min_sources,
                "providers_requested": selected_providers,
            },
            metadata={
                "providers_requested": selected_providers,
                "providers_used": successful_providers,
                "providers_attempted": attempted_providers,
                "errors": errors,
                "provider_guidance": self._provider_guidance(),
            },
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    def _extract_keywords(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
        return [token for token in tokens if token not in STOPWORDS]

    def _source_domain(self, url: str) -> str:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc

    def _parse_source_date(self, value: str) -> Optional[datetime]:
        cleaned = (value or "").strip()
        if not cleaned:
            return None

        iso_candidate = cleaned.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(iso_candidate)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

        for fmt in DATE_FORMATS:
            try:
                parsed = datetime.strptime(cleaned, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    def _source_freshness(self, source: Source, timelimit: Optional[str] = None) -> Dict:
        parsed = self._parse_source_date(source.date)
        if parsed is None:
            return {
                "score": 0.45 if timelimit else 0.5,
                "bucket": "unknown",
                "parsed": None,
            }

        age_days = max((datetime.now(timezone.utc) - parsed).days, 0)
        if age_days <= 30:
            score = 1.0
            bucket = "last_30_days"
        elif age_days <= 180:
            score = 0.8
            bucket = "last_6_months"
        elif age_days <= 365:
            score = 0.65
            bucket = "last_year"
        elif age_days <= 1095:
            score = 0.45
            bucket = "last_3_years"
        else:
            score = 0.3
            bucket = "older"

        return {
            "score": score,
            "bucket": bucket,
            "parsed": parsed.date().isoformat(),
            "age_days": age_days,
        }

    def _estimate_source_quality(self, source: Source) -> Dict:
        domain = self._source_domain(source.url)
        haystack = f"{source.title} {source.snippet}".lower()
        score = 0.35
        signals: List[str] = []

        if domain.endswith(HIGH_TRUST_SUFFIXES):
            score += 0.35
            signals.append("institutional_domain")
        elif domain.endswith(MEDIUM_TRUST_SUFFIXES):
            score += 0.2
            signals.append("nonprofit_or_international_domain")

        if any(marker in domain for marker in OFFICIAL_DOMAIN_MARKERS):
            score += 0.2
            signals.append("official_or_documentation_domain")

        if any(marker in haystack for marker in QUALITY_TEXT_MARKERS):
            score += 0.1
            signals.append("high_signal_language")

        if source.cross_validated:
            score += 0.15
            signals.append("cross_validated_url")

        if len(source.snippet) >= 120:
            score += 0.05
            signals.append("rich_snippet")

        score = max(0.2, min(round(score, 3), 1.0))
        if score >= 0.8:
            tier = "high"
        elif score >= 0.55:
            tier = "medium"
        else:
            tier = "low"

        return {
            "score": score,
            "tier": tier,
            "signals": signals,
            "domain": domain,
        }

    def _evidence_strength(self, overlap: float, quality_score: float, freshness_score: float) -> float:
        score = (overlap * 0.45) + (quality_score * 0.4) + (freshness_score * 0.1) + 0.05
        return round(min(score, 1.0), 3)

    def _build_claim_summary(
        self,
        verdict: str,
        support_score: float,
        conflict_score: float,
        domain_diversity: int,
        top_support: List[Source],
        top_conflict: List[Source],
    ) -> str:
        base = (
            f"Verdict: {verdict}. "
            f"Weighted support: {support_score:.2f}. "
            f"Weighted conflict: {conflict_score:.2f}. "
            f"Independent domains: {domain_diversity}."
        )
        if verdict != "contested":
            return base

        support_titles = ", ".join(
            source.extra["verification"]["domain"] for source in top_support[:2]
        ) or "none"
        conflict_titles = ", ".join(
            source.extra["verification"]["domain"] for source in top_conflict[:2]
        ) or "none"
        return (
            f"{base} "
            f"Supporting evidence is led by domains: {support_titles}. "
            f"Conflicting evidence is led by domains: {conflict_titles}."
        )

    def _classify_source_against_claim(
        self,
        claim_keywords: List[str],
        source: Source,
        timelimit: Optional[str] = None,
        extra_text: str = "",
    ) -> tuple[str, Dict]:
        haystack = f"{source.title} {source.snippet} {extra_text}".lower()
        matched_keywords = [keyword for keyword in claim_keywords if keyword in haystack]
        overlap = len(matched_keywords) / max(len(claim_keywords), 1)
        conflict_hit = any(pattern.search(haystack) for pattern in CONFLICT_PATTERNS)
        quality = self._estimate_source_quality(source)
        freshness = self._source_freshness(source, timelimit=timelimit)
        evidence_strength = self._evidence_strength(
            overlap=overlap,
            quality_score=quality["score"],
            freshness_score=freshness["score"],
        )

        if overlap >= 0.35 and conflict_hit:
            classification = "conflicting"
        elif overlap >= 0.35:
            classification = "supporting"
        elif overlap >= 0.2 and conflict_hit:
            classification = "conflicting"
        else:
            classification = "neutral"

        return classification, {
            "matched_keywords": matched_keywords,
            "keyword_overlap": round(overlap, 3),
            "domain": quality["domain"],
            "conflict_markers_detected": conflict_hit,
            "source_quality": quality,
            "freshness": freshness,
            "evidence_strength": evidence_strength,
            "classification": classification,
        }

    def _augment_with_pages(
        self,
        claim_keywords: List[str],
        sources: List[Source],
        timelimit: Optional[str],
        max_pages: int,
        page_max_chars: int,
    ) -> Dict[str, int]:
        attempted = 0
        succeeded = 0
        for source in sources[:max_pages]:
            attempted += 1
            page = self.browse_func(source.url, max_chars=page_max_chars)
            source.extra = {**source.extra, "page_fetch": page}
            if page.get("status") != "success":
                verification = source.extra.get("verification", {})
                verification["page_evidence"] = {
                    "status": "error",
                    "error": page.get("error", "unknown"),
                }
                source.extra["verification"] = verification
                continue

            succeeded += 1
            page_excerpt = page.get("content", "")
            classification, evidence = self._classify_source_against_claim(
                claim_keywords,
                source,
                timelimit=timelimit,
                extra_text=page_excerpt,
            )
            evidence["page_aware"] = True
            evidence["page_excerpt_chars"] = len(page_excerpt)
            evidence["page_evidence"] = {
                "status": "success",
                "title": page.get("title", ""),
                "classification": classification,
                "truncated": page.get("truncated", False),
                "total_length": page.get("total_length", 0),
            }
            source.extra["verification"] = evidence
            source.extra["page_fetch"] = {
                "status": "success",
                "title": page.get("title", ""),
                "truncated": page.get("truncated", False),
                "total_length": page.get("total_length", 0),
            }

        return {
            "attempted": attempted,
            "succeeded": succeeded,
        }

    def verify_claim(
        self,
        claim: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        providers: Optional[List[str]] = None,
        include_pages: bool = False,
        deep: bool = False,
        max_pages: int = 3,
        page_max_chars: int = 4000,
        answer: Optional[Answer] = None,
        **kwargs,
    ) -> VerificationResult:
        """Search for evidence related to a claim and classify the evidence."""
        start_time = time.time()
        answer = answer or self.search(
            query=claim,
            search_type="text",
            timelimit=timelimit,
            region=region,
            providers=providers,
            **kwargs,
        )

        claim_keywords = self._extract_keywords(claim)
        supporting_sources: List[Source] = []
        conflicting_sources: List[Source] = []
        neutral_sources: List[Source] = []
        domain_set = set()

        for source in answer.sources:
            classification, evidence = self._classify_source_against_claim(
                claim_keywords,
                source,
                timelimit=timelimit,
            )
            source.extra = {**source.extra, "verification": evidence}
            domain_set.add(evidence["domain"])
            if classification == "supporting":
                supporting_sources.append(source)
            elif classification == "conflicting":
                conflicting_sources.append(source)
            else:
                neutral_sources.append(source)

        page_fetch_stats = {
            "attempted": 0,
            "succeeded": 0,
        }
        page_aware = include_pages or deep
        if page_aware and answer.sources:
            page_fetch_stats = self._augment_with_pages(
                claim_keywords=claim_keywords,
                sources=answer.sources,
                timelimit=timelimit,
                max_pages=max_pages,
                page_max_chars=page_max_chars,
            )

            supporting_sources = []
            conflicting_sources = []
            neutral_sources = []
            domain_set = set()
            for source in answer.sources:
                evidence = source.extra.get("verification")
                if not evidence:
                    classification, evidence = self._classify_source_against_claim(
                        claim_keywords,
                        source,
                        timelimit=timelimit,
                    )
                    source.extra = {**source.extra, "verification": evidence}
                domain_set.add(evidence["domain"])
                classification = evidence["classification"]
                if classification == "supporting":
                    supporting_sources.append(source)
                elif classification == "conflicting":
                    conflicting_sources.append(source)
                else:
                    neutral_sources.append(source)

        support_count = len(supporting_sources)
        conflict_count = len(conflicting_sources)
        domain_diversity = len([domain for domain in domain_set if domain])
        support_score = round(
            sum(source.extra["verification"]["evidence_strength"] for source in supporting_sources),
            3,
        )
        conflict_score = round(
            sum(source.extra["verification"]["evidence_strength"] for source in conflicting_sources),
            3,
        )
        neutral_score = round(
            sum(source.extra["verification"]["evidence_strength"] for source in neutral_sources),
            3,
        )
        top_support = sorted(
            supporting_sources,
            key=lambda source: source.extra["verification"]["evidence_strength"],
            reverse=True,
        )
        top_conflict = sorted(
            conflicting_sources,
            key=lambda source: source.extra["verification"]["evidence_strength"],
            reverse=True,
        )
        quality_breakdown = {
            "high_quality_sources": sum(
                1
                for source in answer.sources
                if source.extra["verification"]["source_quality"]["tier"] == "high"
            ),
            "medium_quality_sources": sum(
                1
                for source in answer.sources
                if source.extra["verification"]["source_quality"]["tier"] == "medium"
            ),
            "low_quality_sources": sum(
                1
                for source in answer.sources
                if source.extra["verification"]["source_quality"]["tier"] == "low"
            ),
        }

        if support_score >= 1.35 and conflict_score <= 0.2 and domain_diversity >= 2:
            verdict = "supported"
            confidence = "HIGH"
        elif support_score >= 0.7 and conflict_score <= 0.35:
            verdict = "likely_supported"
            confidence = "MEDIUM"
        elif support_score >= 0.55 and conflict_score >= 0.45:
            verdict = "contested"
            confidence = "MEDIUM"
        elif conflict_score >= 0.55 and support_score < 0.55:
            verdict = "likely_false"
            confidence = "MEDIUM"
        elif conflict_count >= 1 or support_count >= 1:
            verdict = "insufficient_evidence"
            confidence = "LOW"
        else:
            verdict = "insufficient_evidence"
            confidence = "LOW"

        summary = self._build_claim_summary(
            verdict=verdict,
            support_score=support_score,
            conflict_score=conflict_score,
            domain_diversity=domain_diversity,
            top_support=top_support,
            top_conflict=top_conflict,
        )

        return VerificationResult(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            summary=summary,
            supporting_sources=supporting_sources,
            conflicting_sources=conflicting_sources,
            neutral_sources=neutral_sources,
            analysis={
                "claim_keywords": claim_keywords,
                "supporting_count": support_count,
                "conflicting_count": conflict_count,
                "neutral_count": len(neutral_sources),
                "domain_diversity": domain_diversity,
                "provider_diversity": len(set(answer.metadata.get("providers_used", []))),
                "page_fetches_attempted": page_fetch_stats["attempted"],
                "page_fetches_succeeded": page_fetch_stats["succeeded"],
                "page_aware": page_aware,
                "support_score": support_score,
                "conflict_score": conflict_score,
                "neutral_score": neutral_score,
                "net_signal": round(support_score - conflict_score, 3),
                "quality_breakdown": quality_breakdown,
                "contested_summary": {
                    "supporting_titles": [source.title for source in top_support[:3]],
                    "supporting_domains": [
                        source.extra["verification"]["domain"] for source in top_support[:3]
                    ],
                    "conflicting_titles": [source.title for source in top_conflict[:3]],
                    "conflicting_domains": [
                        source.extra["verification"]["domain"] for source in top_conflict[:3]
                    ],
                },
                "verification_model": {
                    "name": "evidence-aware-heuristic-v3",
                    "score_breakdown": {
                        "keyword_overlap_weight": 0.45,
                        "source_quality_weight": 0.4,
                        "source_freshness_weight": 0.1,
                        "base_signal_weight": 0.05,
                    },
                    "signals": [
                        "keyword_overlap",
                        "conflict_markers",
                        "source_quality",
                        "source_freshness",
                        "domain_diversity",
                        "optional_page_content",
                        "provider_diversity",
                    ],
                    "limitations": [
                        "heuristic_classification",
                        "no_fact_level_parsing",
                        "result_quality_depends_on_returned_search_snippets",
                        "provider_diversity_depends_on_configured_backends",
                    ],
                },
                "min_sources_target": self.min_sources,
            },
            metadata=answer.metadata,
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    def _build_report_source_digest(self, source: Source, classification: str) -> Dict:
        evidence = source.extra.get("verification", {})
        quality = evidence.get("source_quality", {})
        freshness = evidence.get("freshness", {})
        page_evidence = evidence.get("page_evidence", {})
        citation = f"[{source.title}]({source.url})"

        return {
            "title": source.title,
            "url": source.url,
            "citation": citation,
            "classification": classification,
            "engine": source.engine,
            "snippet": source.snippet,
            "domain": evidence.get("domain", ""),
            "evidence_strength": evidence.get("evidence_strength", 0),
            "keyword_overlap": evidence.get("keyword_overlap", 0),
            "source_quality_tier": quality.get("tier", "unknown"),
            "freshness_bucket": freshness.get("bucket", "unknown"),
            "page_evidence_status": page_evidence.get("status", "not_requested"),
        }

    def _build_stance_bucket(self, sources: List[Source]) -> Dict:
        if not sources:
            return {
                "count": 0,
                "score": 0.0,
                "top_domains": [],
                "top_titles": [],
            }

        ranked = sorted(
            sources,
            key=lambda source: source.extra.get("verification", {}).get("evidence_strength", 0),
            reverse=True,
        )
        return {
            "count": len(sources),
            "score": round(
                sum(
                    source.extra.get("verification", {}).get("evidence_strength", 0)
                    for source in sources
                ),
                3,
            ),
            "top_domains": [
                source.extra.get("verification", {}).get("domain", "")
                for source in ranked[:3]
                if source.extra.get("verification", {}).get("domain", "")
            ],
            "top_titles": [source.title for source in ranked[:3]],
        }

    def _build_report_coverage_warnings(
        self,
        answer: Answer,
        verification: VerificationResult,
    ) -> List[str]:
        warnings: List[str] = []
        provider_guidance = answer.metadata.get("provider_guidance", {})
        if verification.analysis["provider_diversity"] < 2:
            warnings.append(
                provider_guidance.get(
                    "recommended_next_step",
                    "Single-provider evidence path. Configure a self-hosted SearXNG instance to unlock a free second provider.",
                )
            )
        if not verification.analysis["page_aware"]:
            warnings.append("Snippet-only verification. Re-run with --deep for higher-stakes claims.")
        if verification.analysis["domain_diversity"] < 2:
            warnings.append("Low domain diversity. A second independent domain would strengthen the report.")
        if len(answer.sources) < self.min_sources:
            warnings.append(
                f"Only {len(answer.sources)} source(s) returned; target coverage is {self.min_sources}+."
            )
        if verification.verdict == "contested":
            warnings.append("Meaningful support and conflict both exist. Do not collapse the disagreement.")
        if verification.verdict == "insufficient_evidence":
            warnings.append("Available evidence is too weak for a stronger conclusion.")
        return warnings

    def _build_report_verdict_rationale(
        self,
        verification: VerificationResult,
        stance_summary: Dict,
    ) -> List[str]:
        rationale = [
            (
                f"Support score is {verification.analysis['support_score']:.2f} and "
                f"conflict score is {verification.analysis['conflict_score']:.2f}."
            ),
            (
                f"Evidence spans {verification.analysis['domain_diversity']} domain(s) and "
                f"{verification.analysis['provider_diversity']} provider(s)."
            ),
        ]

        if stance_summary["supporting"]["top_domains"]:
            rationale.append(
                "Strongest supporting domains: "
                + ", ".join(stance_summary["supporting"]["top_domains"][:2])
                + "."
            )
        if stance_summary["conflicting"]["top_domains"]:
            rationale.append(
                "Strongest conflicting domains: "
                + ", ".join(stance_summary["conflicting"]["top_domains"][:2])
                + "."
            )
        if verification.analysis["page_aware"]:
            rationale.append(
                f"Page-aware verification ran on {verification.analysis['page_fetches_succeeded']}/"
                f"{verification.analysis['page_fetches_attempted']} fetched page(s)."
            )
        return rationale

    def _build_report_next_steps(
        self,
        verdict: str,
        page_aware: bool,
        provider_diversity: int,
    ) -> List[str]:
        steps: List[str] = []

        if verdict == "supported":
            steps.append("Cite one official source and one independent source in the final answer.")
        elif verdict == "likely_supported":
            steps.append("Present the claim as likely rather than certain unless you add another corroborating source.")
        elif verdict == "contested":
            steps.append("Surface the disagreement explicitly and quote both the strongest support and strongest conflict.")
        elif verdict == "likely_false":
            steps.append("Avoid restating the claim as fact unless new counter-evidence appears.")
        else:
            steps.append("State that the available evidence is insufficient rather than forcing a firmer verdict.")

        if not page_aware:
            steps.append("Re-run with --deep or --with-pages if the top snippets look too thin.")

        if provider_diversity < 2:
            steps.append(
                "Configure a self-hosted SearXNG instance and set "
                f"{SearxngProvider.ENV_VARS[0]} to unlock a free second provider."
            )

        return steps

    def evidence_report(
        self,
        query: str,
        claim: Optional[str] = None,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        providers: Optional[List[str]] = None,
        include_pages: bool = False,
        deep: bool = False,
        max_pages: int = 3,
        page_max_chars: int = 4000,
        max_sources: int = 5,
        search_type: str = "text",
        **kwargs,
    ) -> EvidenceReportResult:
        """Produce a high-level evidence report that combines search and verification."""
        start_time = time.time()
        normalized_claim = claim or query
        answer = self.search(
            query=query,
            search_type=search_type,
            timelimit=timelimit,
            region=region,
            providers=providers,
            **kwargs,
        )
        verification = self.verify_claim(
            claim=normalized_claim,
            timelimit=timelimit,
            region=region,
            providers=providers,
            include_pages=include_pages or deep,
            deep=deep,
            max_pages=max_pages,
            page_max_chars=page_max_chars,
            answer=answer,
            **kwargs,
        )

        digested_sources: List[Dict] = []
        classified_sources = (
            [("supporting", source) for source in verification.supporting_sources]
            + [("conflicting", source) for source in verification.conflicting_sources]
            + [("neutral", source) for source in verification.neutral_sources]
        )
        classified_sources.sort(
            key=lambda item: item[1].extra.get("verification", {}).get("evidence_strength", 0),
            reverse=True,
        )

        for classification, source in classified_sources[:max_sources]:
            digested_sources.append(self._build_report_source_digest(source, classification))

        stance_summary = {
            "supporting": self._build_stance_bucket(verification.supporting_sources),
            "conflicting": self._build_stance_bucket(verification.conflicting_sources),
            "neutral": self._build_stance_bucket(verification.neutral_sources),
        }
        verdict_rationale = self._build_report_verdict_rationale(
            verification=verification,
            stance_summary=stance_summary,
        )
        coverage_warnings = self._build_report_coverage_warnings(
            answer=answer,
            verification=verification,
        )
        citations = [item["citation"] for item in digested_sources]
        executive_summary = (
            f"Evidence report for '{normalized_claim}': {verification.verdict} "
            f"with {verification.confidence.lower()} confidence. "
            f"Used {len(answer.sources)} source(s) across "
            f"{verification.analysis['provider_diversity']} provider(s) and "
            f"{verification.analysis['domain_diversity']} domain(s). "
            f"Support={verification.analysis['support_score']:.2f}, "
            f"conflict={verification.analysis['conflict_score']:.2f}."
        )
        analysis = {
            "report_model": "evidence-report-v2",
            "query_search_type": search_type,
            "query_source_count": len(answer.sources),
            "top_sources_returned": len(digested_sources),
            "search_confidence": answer.confidence,
            "page_aware": verification.analysis["page_aware"],
            "provider_diversity": verification.analysis["provider_diversity"],
            "domain_diversity": verification.analysis["domain_diversity"],
            "support_score": verification.analysis["support_score"],
            "conflict_score": verification.analysis["conflict_score"],
            "page_fetches_attempted": verification.analysis["page_fetches_attempted"],
            "page_fetches_succeeded": verification.analysis["page_fetches_succeeded"],
            "supporting_count": verification.analysis["supporting_count"],
            "conflicting_count": verification.analysis["conflicting_count"],
            "neutral_count": verification.analysis["neutral_count"],
            "stance_summary": stance_summary,
            "coverage_warning_count": len(coverage_warnings),
            "free_provider_path": answer.metadata.get("provider_guidance", {}),
        }
        metadata = {
            **answer.metadata,
            "report_model": "evidence-report-v2",
            "query": query,
            "claim": normalized_claim,
            "search_elapsed_ms": answer.elapsed_ms,
            "verification_elapsed_ms": verification.elapsed_ms,
        }

        return EvidenceReportResult(
            query=query,
            claim=normalized_claim,
            verdict=verification.verdict,
            confidence=verification.confidence,
            executive_summary=executive_summary,
            verification_summary=verification.summary,
            verdict_rationale=verdict_rationale,
            stance_summary=stance_summary,
            coverage_warnings=coverage_warnings,
            source_digest=digested_sources,
            citations=citations,
            next_steps=self._build_report_next_steps(
                verdict=verification.verdict,
                page_aware=verification.analysis["page_aware"],
                provider_diversity=verification.analysis["provider_diversity"],
            ),
            analysis=analysis,
            metadata=metadata,
            elapsed_ms=int((time.time() - start_time) * 1000),
        )


class CrossValidatedSearcher(UltimateSearcher):
    """Compatibility alias for the experimental renamed API."""


__all__ = [
    "Answer",
    "EvidenceReportResult",
    "CrossValidatedSearcher",
    "Source",
    "UltimateSearcher",
    "VerificationResult",
]
