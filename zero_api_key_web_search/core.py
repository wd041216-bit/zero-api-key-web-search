"""Shared search core used by CLI, MCP, and compatibility wrappers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from zero_api_key_web_search.browse_page import browse
from zero_api_key_web_search.cache import get_cache
from zero_api_key_web_search.providers import (
    BrightDataProvider,
    DdgsProvider,
    ProviderConfigurationError,
    SearchProvider,
    SearxngProvider,
)

logger = logging.getLogger("zero-api-key-web-search")


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
    extra: dict = field(default_factory=dict)


@dataclass
class Answer:
    """Structured result returned by a search operation."""

    query: str
    search_type: str
    answer: str
    confidence: str
    sources: list[Source]
    validation: dict
    metadata: dict
    elapsed_ms: int


@dataclass
class SubClaimResult:
    """Result of verifying a single sub-claim decomposed from a compound claim."""

    sub_claim: str
    verdict: str
    confidence: str
    support_score: float
    conflict_score: float
    supporting_count: int
    conflicting_count: int


@dataclass
class VerificationResult:
    """Structured result returned by claim verification."""

    claim: str
    verdict: str
    confidence: str
    summary: str
    supporting_sources: list[Source]
    conflicting_sources: list[Source]
    neutral_sources: list[Source]
    analysis: dict
    metadata: dict
    elapsed_ms: int
    sub_claims: list[SubClaimResult] = field(default_factory=list)
    calibration_note: str = ""


@dataclass
class EvidenceReportResult:
    """Structured result returned by the flagship evidence-report workflow."""

    query: str
    claim: str
    verdict: str
    confidence: str
    executive_summary: str
    verification_summary: str
    verdict_rationale: list[str]
    stance_summary: dict
    coverage_warnings: list[str]
    source_digest: list[dict]
    citations: list[str]
    next_steps: list[str]
    analysis: dict
    metadata: dict
    elapsed_ms: int
    calibration_note: str = ""


@dataclass
class LlmContextResult:
    """LLM-optimized search context with compact citations and risk notes."""

    query: str
    search_type: str
    context_markdown: str
    citations: list[str]
    source_digest: list[dict]
    metadata: dict
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
    # English
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
    # Spanish
    "falso",
    "falsa",
    "incorrecto",
    "incorrecta",
    "desmentido",
    "desmentida",
    "desmentidos",
    "desmentidas",
    "engañoso",
    "engañosa",
    "negado",
    "negada",
    "contradice",
    "sin evidencia",
    "comprobación",
    # French
    "faux",
    "fausse",
    "incorrect",
    "incorrecte",
    "démenti",
    "démentie",
    "trompeur",
    "trompeuse",
    "contesté",
    "contestée",
    "réfuté",
    "réfutée",
    "nié",
    "niée",
    "contradictoire",
    "aucune preuve",
    # German
    "falsch",
    "inkorrekt",
    "widerlegt",
    "irreführend",
    "bestritten",
    "dementi",
    "widerspricht",
    "kein beweis",
    # Chinese
    "错误",
    "不实",
    "误导",
    "辟谣",
    "否认",
    "反驳",
    "没有证据",
)

CONFLICT_PATTERNS = tuple(
    re.compile(rf"(?<!\w){re.escape(marker)}(?!\w)", re.IGNORECASE | re.UNICODE)
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

CALIBRATION_NOTE = (
    "Confidence thresholds (support >= 1.35 for 'supported', etc.) are heuristic "
    "and have not been calibrated against a gold-standard dataset. Confidence levels "
    "(HIGH/MEDIUM/LOW) reflect relative signal strength, not probabilistic accuracy. "
    "Current regression suite: 98 claims across 5 verdict families. "
    "See docs/benchmarks.md for per-family breakdown."
)

CLAIM_SPLIT_PATTERN = re.compile(
    r",\s*(?:and|but|yet|while|although)\s+"
    r"|\s+(?:and|but|yet|while|although)\s+"
    r"|(?:\.|;)\s+"
    r"|\s+,\s+"
)

CLAIM_DECOMPOSE_MIN_LENGTH = 10

CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_RESET_SECONDS = 60

PROVIDER_PROFILES = {
    "free": ["ddgs"],
    "default": ["ddgs"],
    "free-verified": ["ddgs", "searxng"],
    "production": ["brightdata"],
    "max-evidence": ["ddgs", "searxng", "brightdata"],
}

GOGGLES_PRESETS = {
    "docs-first": {
        "description": "Prefer official docs, developer docs, specs, and support pages.",
        "boost_domains": [],
        "boost_domain_markers": ["docs.", "developer.", "developers.", "api.", "support.", "help."],
        "boost_title_terms": ["documentation", "docs", "release notes", "specification", "official"],
        "block_domains": [],
        "boost": 0.35,
        "demote": 0.35,
    },
    "research": {
        "description": "Prefer academic, institutional, and research-heavy sources.",
        "boost_domains": ["arxiv.org", "pubmed.ncbi.nlm.nih.gov", "nature.com", "science.org"],
        "boost_domain_suffixes": [".edu", ".ac.uk", ".gov"],
        "boost_title_terms": ["paper", "study", "research", "journal", "proceedings", "preprint"],
        "block_domains": [],
        "boost": 0.3,
        "demote": 0.25,
    },
    "news-balanced": {
        "description": "Prefer reporting sources while demoting low-context aggregators.",
        "boost_title_terms": ["breaking", "report", "analysis", "live updates"],
        "block_domains": [],
        "demote_domains": ["pinterest.com"],
        "boost": 0.2,
        "demote": 0.3,
    },
}

class UltimateSearcher:
    """Search implementation backing the public package surface."""

    def __init__(
        self,
        timeout: int = 15,
        min_sources: int = 3,
        providers: list[SearchProvider] | None = None,
        browse_func: Callable[..., dict] | None = None,
    ):
        self.timeout = timeout
        self.min_sources = min_sources
        self.providers = providers or self._default_providers()
        self.browse_func = browse_func or browse
        self._circuit_breaker: dict[str, dict] = {}

    def _default_providers(self) -> list[SearchProvider]:
        providers: list[SearchProvider] = [DdgsProvider(timeout=self.timeout)]
        searxng = SearxngProvider(timeout=self.timeout)
        if searxng.is_configured():
            providers.append(searxng)
        brightdata = BrightDataProvider(timeout=self.timeout)
        if brightdata.is_configured():
            providers.append(brightdata)
        return providers

    def _provider_guidance(self) -> dict:
        searxng = SearxngProvider(timeout=self.timeout)
        brightdata = BrightDataProvider(timeout=self.timeout)
        searxng_configured = searxng.is_configured()
        brightdata_configured = brightdata.is_configured()
        return {
            "free_recommended_pair": ["ddgs", "searxng"],
            "production_provider": "brightdata",
            "searxng_configured": searxng_configured,
            "searxng_env_vars": list(SearxngProvider.ENV_VARS),
            "brightdata_configured": brightdata_configured,
            "brightdata_api_key_env_vars": list(BrightDataProvider.API_KEY_ENV_VARS),
            "brightdata_zone_env_vars": list(BrightDataProvider.ZONE_ENV_VARS),
            "brightdata_signup_url": BrightDataProvider.SIGNUP_URL,
            "free_setup_hint": (
                "Self-host a SearXNG instance and point "
                f"{SearxngProvider.ENV_VARS[0]} to it for a free dual-provider path."
            ),
            "production_setup_hint": (
                "For production-grade search, geo-targeted evidence, or stronger "
                "reliability, configure Bright Data via "
                f"{BrightDataProvider.API_KEY_ENV_VARS[0]}. New users can sign up at "
                f"{BrightDataProvider.SIGNUP_URL}."
            ),
            "recommended_next_step": (
                "Multi-provider evidence path is active."
                if searxng_configured or brightdata_configured
                else (
                    "Configure a self-hosted SearXNG instance for a free second provider "
                    "or Bright Data for production-grade search."
                )
            ),
        }

    def provider_profiles(self) -> dict:
        """Return supported provider profiles for agent-facing discovery."""
        return {
            "free": {
                "providers": ["ddgs"],
                "description": "Zero-setup local/default search path.",
            },
            "free-verified": {
                "providers": ["ddgs", "searxng"],
                "description": "Free cross-validation path. Requires a configured SearXNG instance.",
            },
            "production": {
                "providers": ["brightdata"],
                "description": (
                    "Production-grade Bright Data path for reliability, "
                    "geo-targeting, and structured SERP data."
                ),
            },
            "max-evidence": {
                "providers": ["ddgs", "searxng", "brightdata"],
                "description": "Maximum provider diversity across free and production backends.",
            },
        }

    def goggles_presets(self) -> dict:
        """Return built-in reranking/filtering presets."""
        return {
            name: {
                "description": config.get("description", ""),
                "boost_domains": config.get("boost_domains", []),
                "block_domains": config.get("block_domains", []),
            }
            for name, config in GOGGLES_PRESETS.items()
        }

    def provider_statuses(self) -> list[dict]:
        """Return provider readiness for CLI, MCP, and skill discovery flows."""
        configured_names = {provider.name for provider in self.providers}
        searxng = SearxngProvider(timeout=self.timeout)
        brightdata = BrightDataProvider(timeout=self.timeout)
        return [
            {
                "name": "ddgs",
                "status": "ready" if "ddgs" in configured_names else "available",
                "default": "ddgs" in configured_names,
                "kind": "free default",
                "description": "Zero-setup DuckDuckGo-backed search.",
                "setup": "No setup required.",
            },
            {
                "name": "searxng",
                "status": "ready" if searxng.is_configured() else "not_configured",
                "default": "searxng" in configured_names,
                "kind": "free self-hosted",
                "description": "Free second provider for cross-validation.",
                "setup": SearxngProvider.configuration_hint(),
            },
            {
                "name": "brightdata",
                "status": "ready" if brightdata.is_configured() else "not_configured",
                "default": "brightdata" in configured_names,
                "kind": "production optional",
                "description": (
                    "Production-grade SERP provider for geo-targeted, structured, "
                    "higher-reliability evidence collection."
                ),
                "setup": BrightDataProvider.configuration_hint(),
                "signup_url": BrightDataProvider.SIGNUP_URL,
            },
        ]

    def _resolve_provider_profile(self, profile: str | None) -> list[str] | None:
        if not profile:
            return None
        normalized = profile.strip().lower()
        if not normalized:
            return None
        if normalized not in PROVIDER_PROFILES:
            supported = ", ".join(sorted(PROVIDER_PROFILES))
            raise ValueError(f"Unsupported provider profile '{profile}'. Supported profiles: {supported}")
        return list(PROVIDER_PROFILES[normalized])

    def _known_optional_provider(self, provider_name: str) -> SearchProvider | None:
        if provider_name == "searxng":
            return SearxngProvider(timeout=self.timeout)
        if provider_name == "brightdata":
            return BrightDataProvider(timeout=self.timeout)
        return None

    def _provider_registry(self) -> dict[str, SearchProvider]:
        registry = {provider.name: provider for provider in self.providers}
        for provider_name in ("searxng", "brightdata"):
            if provider_name not in registry:
                provider = self._known_optional_provider(provider_name)
                if provider is not None:
                    registry[provider_name] = provider
        return registry

    def _normalize_provider_names(
        self,
        providers: list[str] | None,
        profile: str | None = None,
    ) -> list[str]:
        registry = self._provider_registry()
        profile_providers = self._resolve_provider_profile(profile)
        if profile_providers is not None and not providers:
            providers = profile_providers
        if not providers:
            return [provider.name for provider in self.providers]

        normalized: list[str] = []
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

    def _load_goggles(self, goggles: str | dict | None) -> dict | None:
        if not goggles:
            return None
        if isinstance(goggles, dict):
            return goggles

        value = goggles.strip()
        if not value:
            return None
        preset = GOGGLES_PRESETS.get(value.lower())
        if preset is not None:
            return dict(preset)

        if os.path.exists(value):
            with open(value, encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise ValueError("Goggles file must contain a JSON object.")
            return loaded

        supported = ", ".join(sorted(GOGGLES_PRESETS))
        raise ValueError(f"Unsupported goggles preset or file '{goggles}'. Built-ins: {supported}")

    def _source_matches_domain(self, domain: str, patterns: list[str]) -> bool:
        for pattern in patterns:
            normalized = pattern.lower().strip()
            if normalized and (domain == normalized or domain.endswith(f".{normalized}")):
                return True
        return False

    def _apply_goggles(self, sources: list[Source], goggles: str | dict | None) -> tuple[list[Source], dict]:
        config = self._load_goggles(goggles)
        if not config:
            return sources, {"applied": False}

        block_domains = [item.lower() for item in config.get("block_domains", [])]
        demote_domains = [item.lower() for item in config.get("demote_domains", [])]
        boost_domains = [item.lower() for item in config.get("boost_domains", [])]
        boost_domain_markers = [item.lower() for item in config.get("boost_domain_markers", [])]
        boost_domain_suffixes = [item.lower() for item in config.get("boost_domain_suffixes", [])]
        boost_title_terms = [item.lower() for item in config.get("boost_title_terms", [])]
        boost = float(config.get("boost", 0.25))
        demote = float(config.get("demote", 0.25))

        filtered: list[Source] = []
        blocked = 0
        boosted = 0
        demoted = 0
        for source in sources:
            domain = self._source_domain(source.url)
            haystack = f"{source.title} {source.snippet}".lower()
            if self._source_matches_domain(domain, block_domains):
                blocked += 1
                continue

            score = 1.0
            signals: list[str] = []
            if self._source_matches_domain(domain, boost_domains):
                score += boost
                signals.append("boost_domain")
            if any(marker in domain for marker in boost_domain_markers):
                score += boost
                signals.append("boost_domain_marker")
            if any(domain.endswith(suffix) for suffix in boost_domain_suffixes):
                score += boost
                signals.append("boost_domain_suffix")
            if any(term in haystack for term in boost_title_terms):
                score += boost
                signals.append("boost_title_term")
            if self._source_matches_domain(domain, demote_domains):
                score -= demote
                signals.append("demote_domain")

            if score > 1.0:
                boosted += 1
            if score < 1.0:
                demoted += 1
            source.extra = {
                **source.extra,
                "goggles": {
                    "score": round(score, 3),
                    "signals": signals,
                    "domain": domain,
                },
            }
            filtered.append(source)

        filtered.sort(
            key=lambda item: (
                item.extra.get("goggles", {}).get("score", 1.0),
                item.cross_validated,
            ),
            reverse=True,
        )
        for index, source in enumerate(filtered, 1):
            source.rank = index

        return filtered, {
            "applied": True,
            "description": config.get("description", ""),
            "blocked": blocked,
            "boosted": boosted,
            "demoted": demoted,
        }

    def _provider_results_to_sources(
        self,
        provider_name: str,
        search_type: str,
        provider_results: list,
    ) -> list[Source]:
        sources: list[Source] = []
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

    def _provider_is_tripped(self, provider_name: str) -> bool:
        state = self._circuit_breaker.get(provider_name)
        if state is None:
            return False
        if state["consecutive_failures"] >= CIRCUIT_BREAKER_THRESHOLD:
            elapsed = time.time() - state["last_failure_time"]
            if elapsed < CIRCUIT_BREAKER_RESET_SECONDS:
                return True
            state["consecutive_failures"] = 0
        return False

    def _record_provider_failure(self, provider_name: str) -> None:
        state = self._circuit_breaker.setdefault(provider_name, {
            "consecutive_failures": 0, "last_failure_time": 0,
        })
        state["consecutive_failures"] += 1
        state["last_failure_time"] = time.time()
        logger.warning(
            "provider_failure: name=%s consecutive=%d",
            provider_name, state["consecutive_failures"],
        )

    def _record_provider_success(self, provider_name: str) -> None:
        state = self._circuit_breaker.get(provider_name)
        if state is not None:
            state["consecutive_failures"] = 0
        logger.debug("provider_success: name=%s", provider_name)

    def _search_provider(
        self,
        provider_name: str,
        query: str,
        search_type: str,
        timelimit: str | None,
        region: str,
        max_results: int,
        max_retries: int = 3,
        **kwargs,
    ) -> list[Source]:
        if self._provider_is_tripped(provider_name):
            logger.warning("circuit_breaker_open: provider=%s", provider_name)
            return [
                Source(
                    url="error",
                    title=f"Circuit breaker open for {provider_name} (too many consecutive failures)",
                    engine="error",
                )
            ]

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

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                provider_results = provider.search(
                    query=query,
                    search_type=search_type,
                    timelimit=timelimit,
                    region=region,
                    max_results=max_results,
                    **kwargs,
                )
                self._record_provider_success(provider_name)
                return self._provider_results_to_sources(
                    provider_name=provider_name,
                    search_type=search_type,
                    provider_results=provider_results,
                )
            except Exception as exc:
                last_exc = exc
                if isinstance(exc, ProviderConfigurationError):
                    break
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (2 ** attempt))

        retry_note = (
            "configuration error"
            if isinstance(last_exc, ProviderConfigurationError)
            else f"after {max_retries} retries"
        )
        if not isinstance(last_exc, ProviderConfigurationError):
            self._record_provider_failure(provider_name)
        return [
            Source(
                url="error",
                title=f"Error: {provider_name} ({retry_note}): {last_exc}",
                engine="error",
            )
        ]

    def _cross_validate(self, all_results: list[Source]) -> list[Source]:
        """Deduplicate results and rank corroborated URLs first."""
        url_groups: dict[str, list[Source]] = {}
        for result in all_results:
            if result.url == "error":
                continue

            simplified = re.sub(r"^https?://(www\.)?", "", result.url).rstrip("/")
            simplified = simplified.split("#")[0].split("?")[0]
            if not simplified:
                continue
            url_groups.setdefault(simplified, []).append(result)

        validated: list[Source] = []
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
        timelimit: str | None = None,
        region: str = "wt-wt",
        providers: list[str] | None = None,
        profile: str | None = None,
        goggles: str | dict | None = None,
        **kwargs,
    ) -> Answer:
        """Search the web and return a structured answer."""
        start_time = time.time()
        max_results = 30 if search_type == "text" else 20
        selected_providers = self._normalize_provider_names(providers, profile=profile)
        logger.info("search: query=%r type=%s providers=%s", query, search_type, selected_providers)

        raw_results: list[Source] = []
        attempted_providers: list[str] = list(selected_providers)
        successful_providers: list[str] = []

        def _call_provider(provider_name: str) -> tuple[str, list[Source]]:
            # Check cache first
            cache = get_cache()
            cache_key = cache._make_search_key(query, provider_name, search_type, region, timelimit)
            cached = cache.get(cache_key)
            if cached is not None:
                import json as _json
                cached_data = _json.loads(cached[0])
                results = [Source(**s) for s in cached_data]
                return provider_name, results

            results = self._search_provider(
                provider_name=provider_name,
                query=query,
                search_type=search_type,
                timelimit=timelimit,
                region=region,
                max_results=max_results,
                **kwargs,
            )
            # Cache successful results
            if any(r.url != "error" for r in results):
                cache.put(cache_key, json.dumps([{
                    "url": r.url, "title": r.title, "snippet": r.snippet,
                    "rank": r.rank, "engine": r.engine, "cross_validated": r.cross_validated,
                    "date": r.date, "extra": r.extra,
                } for r in results]), "application/json")

            return provider_name, results

        if len(selected_providers) > 1:
            with ThreadPoolExecutor(max_workers=len(selected_providers)) as executor:
                futures = {
                    executor.submit(_call_provider, name): name
                    for name in selected_providers
                }
                for future in as_completed(futures):
                    provider_name, provider_results = future.result()
                    raw_results.extend(provider_results)
                    if any(result.url != "error" for result in provider_results):
                        successful_providers.append(provider_name)
        else:
            for provider in selected_providers:
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

        all_results: list[Source] = []
        errors: list[str] = []
        for result in raw_results:
            if result.url == "error":
                errors.append(result.title)
            else:
                all_results.append(result)

        validated_results = self._cross_validate(all_results)
        goggles_metadata: dict = {"applied": False}
        if goggles:
            validated_results, goggles_metadata = self._apply_goggles(validated_results, goggles)

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
                "provider_profile": profile,
                "goggles": goggles_metadata,
            },
            metadata={
                "provider_profile": profile,
                "providers_requested": selected_providers,
                "providers_used": successful_providers,
                "providers_attempted": attempted_providers,
                "goggles": goggles_metadata,
                "errors": errors,
                "circuit_breaker_state": {
                    name: state["consecutive_failures"]
                    for name, state in self._circuit_breaker.items()
                    if state["consecutive_failures"] > 0
                },
                "provider_guidance": self._provider_guidance(),
            },
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    def _extract_keywords(self, text: str) -> list[str]:
        tokens = re.findall(r"[\w]{3,}", text.lower(), re.UNICODE)
        return [token for token in tokens if token not in STOPWORDS]

    def decompose_claim(self, claim: str) -> list[str]:
        """Decompose a compound claim into verifiable sub-claims.

        Splits on connectors like 'and', 'but', 'yet', 'while', 'although',
        semicolons, and periods. Returns the original claim as a single
        sub-claim if decomposition yields nothing longer than the minimum
        length threshold.
        """
        parts = [part.strip() for part in CLAIM_SPLIT_PATTERN.split(claim) if part.strip()]
        sub_claims = [part for part in parts if len(part) >= CLAIM_DECOMPOSE_MIN_LENGTH]
        if len(sub_claims) <= 1:
            return [claim]
        return sub_claims

    def _source_domain(self, url: str) -> str:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc

    def _parse_source_date(self, value: str) -> datetime | None:
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

    def _source_freshness(self, source: Source, timelimit: str | None = None) -> dict:
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

    def _estimate_source_quality(self, source: Source) -> dict:
        domain = self._source_domain(source.url)
        haystack = f"{source.title} {source.snippet}".lower()
        score = 0.35
        signals: list[str] = []

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
        top_support: list[Source],
        top_conflict: list[Source],
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
        claim_keywords: list[str],
        source: Source,
        timelimit: str | None = None,
        extra_text: str = "",
    ) -> tuple[str, dict]:
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
        claim_keywords: list[str],
        sources: list[Source],
        timelimit: str | None,
        max_pages: int,
        page_max_chars: int,
    ) -> dict[str, int]:
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

    async def asearch(
        self,
        query: str,
        search_type: str = "text",
        timelimit: str | None = None,
        region: str = "wt-wt",
        providers: list[str] | None = None,
        profile: str | None = None,
        goggles: str | dict | None = None,
        **kwargs,
    ) -> Answer:
        """Async variant of search using async provider calls."""
        start_time = time.time()
        max_results = 30 if search_type == "text" else 20
        selected_providers = self._normalize_provider_names(providers, profile=profile)
        logger.info("asearch: query=%r type=%s providers=%s", query, search_type, selected_providers)

        raw_results: list[Source] = []
        attempted_providers: list[str] = list(selected_providers)
        successful_providers: list[str] = []

        async def _acall_provider(provider_name: str) -> tuple[str, list[Source]]:
            if self._provider_is_tripped(provider_name):
                logger.warning("circuit_breaker_open: provider=%s", provider_name)
                return provider_name, [
                    Source(
                        url="error",
                        title=f"Circuit breaker open for {provider_name} (too many consecutive failures)",
                        engine="error",
                    )
                ]
            registry = self._provider_registry()
            provider = registry.get(provider_name)
            if provider is None:
                return provider_name, [
                    Source(
                        url="error",
                        title=f"Error: unsupported provider {provider_name}",
                        engine="error",
                    )
                ]
            try:
                results = await provider.asearch(
                    query=query,
                    search_type=search_type,
                    timelimit=timelimit,
                    region=region,
                    max_results=max_results,
                    **kwargs,
                )
                self._record_provider_success(provider_name)
                return provider_name, self._provider_results_to_sources(provider_name, search_type, results)
            except Exception as exc:
                if not isinstance(exc, ProviderConfigurationError):
                    self._record_provider_failure(provider_name)
                retry_note = "configuration error" if isinstance(exc, ProviderConfigurationError) else "failed"
                return provider_name, [
                    Source(
                        url="error",
                        title=f"Error: {provider_name} ({retry_note}): {exc}",
                        engine="error",
                    )
                ]

        if len(selected_providers) > 1:
            tasks = [_acall_provider(name) for name in selected_providers]
            results = await asyncio.gather(*tasks)
            for provider_name, provider_results in results:
                raw_results.extend(provider_results)
                if any(r.url != "error" for r in provider_results):
                    successful_providers.append(provider_name)
        else:
            for provider_name in selected_providers:
                provider_name_result, provider_results = await _acall_provider(provider_name)
                raw_results.extend(provider_results)
                if any(r.url != "error" for r in provider_results):
                    successful_providers.append(provider_name)

        all_results: list[Source] = []
        errors: list[str] = []
        for result in raw_results:
            if result.url == "error":
                errors.append(result.title)
            else:
                all_results.append(result)

        validated_results = self._cross_validate(all_results)
        goggles_metadata: dict = {"applied": False}
        if goggles:
            validated_results, goggles_metadata = self._apply_goggles(validated_results, goggles)

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
                "provider_profile": profile,
                "goggles": goggles_metadata,
            },
            metadata={
                "provider_profile": profile,
                "providers_requested": selected_providers,
                "providers_used": successful_providers,
                "providers_attempted": attempted_providers,
                "goggles": goggles_metadata,
                "errors": errors,
                "circuit_breaker_state": {
                    name: state["consecutive_failures"]
                    for name, state in self._circuit_breaker.items()
                    if state["consecutive_failures"] > 0
                },
                "provider_guidance": self._provider_guidance(),
                "async": True,
            },
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    def verify_claim(
        self,
        claim: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        providers: list[str] | None = None,
        profile: str | None = None,
        goggles: str | dict | None = None,
        include_pages: bool = False,
        deep: bool = False,
        max_pages: int = 3,
        page_max_chars: int = 4000,
        answer: Answer | None = None,
        **kwargs,
    ) -> VerificationResult:
        """Search for evidence related to a claim and classify the evidence."""
        start_time = time.time()
        logger.info("verify_claim: claim=%r deep=%s", claim, deep)
        answer = answer or self.search(
            query=claim,
            search_type="text",
            timelimit=timelimit,
            region=region,
            providers=providers,
            profile=profile,
            goggles=goggles,
            **kwargs,
        )

        sub_claims = self.decompose_claim(claim)
        sub_claim_results: list[SubClaimResult] = []
        if len(sub_claims) > 1:
            for sub in sub_claims:
                sub_answer = self.search(
                    query=sub,
                    search_type="text",
                    timelimit=timelimit,
                    region=region,
                    providers=providers,
                    profile=profile,
                    goggles=goggles,
                    **kwargs,
                )
                sub_keywords = self._extract_keywords(sub)
                sub_support = []
                sub_conflict = []
                for source in sub_answer.sources:
                    classification, evidence = self._classify_source_against_claim(
                        sub_keywords, source, timelimit=timelimit,
                    )
                    source.extra = {**source.extra, "verification": evidence}
                    if classification == "supporting":
                        sub_support.append(source)
                    elif classification == "conflicting":
                        sub_conflict.append(source)
                sub_support_score = round(
                    sum(s.extra["verification"]["evidence_strength"] for s in sub_support), 3,
                )
                sub_conflict_score = round(
                    sum(s.extra["verification"]["evidence_strength"] for s in sub_conflict), 3,
                )
                if sub_support_score >= 0.7 and sub_conflict_score <= 0.35:
                    sub_verdict = "supported"
                    sub_confidence = "MEDIUM"
                elif sub_support_score >= 0.55 and sub_conflict_score >= 0.45:
                    sub_verdict = "contested"
                    sub_confidence = "LOW"
                elif sub_conflict_score >= 0.55 and sub_support_score < 0.55:
                    sub_verdict = "likely_false"
                    sub_confidence = "MEDIUM"
                elif sub_support or sub_conflict:
                    sub_verdict = "insufficient_evidence"
                    sub_confidence = "LOW"
                else:
                    sub_verdict = "insufficient_evidence"
                    sub_confidence = "LOW"
                sub_claim_results.append(SubClaimResult(
                    sub_claim=sub,
                    verdict=sub_verdict,
                    confidence=sub_confidence,
                    support_score=sub_support_score,
                    conflict_score=sub_conflict_score,
                    supporting_count=len(sub_support),
                    conflicting_count=len(sub_conflict),
                ))

        claim_keywords = self._extract_keywords(claim)
        supporting_sources: list[Source] = []
        conflicting_sources: list[Source] = []
        neutral_sources: list[Source] = []
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
                "semantic_oracle_boundary": {
                    "syntactic_signals": ["keyword_overlap", "conflict_markers"],
                    "heuristic_signals": ["source_quality", "freshness", "domain_diversity"],
                    "page_signals": ["page_content_overlap"],
                    "note": "No natural language inference or entailment is performed. "
                            "All classification is pattern-matching and weighted scoring.",
                },
            },
            metadata=answer.metadata,
            elapsed_ms=int((time.time() - start_time) * 1000),
            sub_claims=sub_claim_results,
            calibration_note=CALIBRATION_NOTE,
        )

    def _build_report_source_digest(self, source: Source, classification: str) -> dict:
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

    def _build_stance_bucket(self, sources: list[Source]) -> dict:
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

    def _baseline_majority_vote(self, verification: VerificationResult) -> dict:
        """Simple majority-vote baseline: more supporting than conflicting sources = supported."""
        support_count = verification.analysis["supporting_count"]
        conflict_count = verification.analysis["conflicting_count"]
        if support_count > conflict_count:
            verdict = "supported"
        elif conflict_count > support_count:
            verdict = "likely_false"
        else:
            verdict = "insufficient_evidence"
        return {
            "model": "majority-vote-baseline",
            "verdict": verdict,
            "supporting_count": support_count,
            "conflicting_count": conflict_count,
        }

    def _baseline_keyword_count(self, claim_keywords: list[str], sources: list[Source]) -> dict:
        """Simple keyword-count baseline: count of sources with keyword overlap >= 0.35."""
        hit_count = sum(
            1
            for source in sources
            if len([
                kw for kw in claim_keywords
                if kw in f"{source.title} {source.snippet}".lower()
            ]) / max(len(claim_keywords), 1) >= 0.35
        )
        verdict = (
            "supported" if hit_count >= 2
            else ("likely_supported" if hit_count >= 1 else "insufficient_evidence")
        )
        return {
            "model": "keyword-count-baseline",
            "verdict": verdict,
            "sources_with_overlap": hit_count,
            "total_sources": len(sources),
        }

    def _build_report_coverage_warnings(
        self,
        answer: Answer,
        verification: VerificationResult,
    ) -> list[str]:
        warnings: list[str] = []
        provider_guidance = answer.metadata.get("provider_guidance", {})
        if verification.analysis["provider_diversity"] < 2:
            warnings.append(
                provider_guidance.get(
                    "recommended_next_step",
                    (
                        "Single-provider evidence path. Configure a self-hosted"
                        " SearXNG instance to unlock a free second provider."
                    ),
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
        stance_summary: dict,
    ) -> list[str]:
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
    ) -> list[str]:
        steps: list[str] = []

        if verdict == "supported":
            steps.append("Cite one official source and one independent source in the final answer.")
        elif verdict == "likely_supported":
            steps.append(
                "Present the claim as likely rather than certain unless you add another corroborating source."
            )
        elif verdict == "contested":
            steps.append(
                "Surface the disagreement explicitly and quote both the"
                " strongest support and strongest conflict."
            )
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
            steps.append(
                "For production-grade search, geo-targeted evidence, or higher reliability, "
                f"configure Bright Data with {BrightDataProvider.API_KEY_ENV_VARS[0]} "
                f"({BrightDataProvider.SIGNUP_URL})."
            )

        return steps

    def _build_llm_source_digest(self, source: Source) -> dict:
        quality = self._estimate_source_quality(source)
        freshness = self._source_freshness(source)
        return {
            "rank": source.rank,
            "title": source.title,
            "url": source.url,
            "snippet": source.snippet,
            "engine": source.engine,
            "date": source.date,
            "domain": quality["domain"],
            "quality": quality["tier"],
            "freshness": freshness["bucket"],
            "cross_validated": source.cross_validated,
            "goggles": source.extra.get("goggles", {}),
        }

    def llm_context(
        self,
        query: str,
        search_type: str = "text",
        timelimit: str | None = None,
        region: str = "wt-wt",
        providers: list[str] | None = None,
        profile: str | None = None,
        goggles: str | dict | None = None,
        max_sources: int = 8,
        include_verification: bool = True,
        **kwargs,
    ) -> LlmContextResult:
        """Build compact, citation-ready context optimized for LLM prompts."""
        start_time = time.time()
        answer = self.search(
            query=query,
            search_type=search_type,
            timelimit=timelimit,
            region=region,
            providers=providers,
            profile=profile,
            goggles=goggles,
            **kwargs,
        )
        selected_sources = answer.sources[:max_sources]
        source_digest = [self._build_llm_source_digest(source) for source in selected_sources]
        citations = [f"[{item['title']}]({item['url']})" for item in source_digest]

        verification: VerificationResult | None = None
        if include_verification and search_type == "text" and selected_sources:
            verification = self.verify_claim(
                claim=query,
                timelimit=timelimit,
                region=region,
                providers=providers,
                profile=profile,
                goggles=goggles,
                answer=answer,
                **kwargs,
            )

        lines = [
            f"# Search context: {query}",
            "",
            "## Retrieval",
            f"- Search type: {search_type}",
            f"- Confidence: {answer.confidence}",
            f"- Providers used: {', '.join(answer.metadata.get('providers_used', [])) or 'none'}",
            f"- Provider profile: {profile or 'default'}",
        ]
        if answer.metadata.get("goggles", {}).get("applied"):
            goggles_meta = answer.metadata["goggles"]
            lines.append(
                "- Goggles: applied"
                f" (boosted={goggles_meta.get('boosted', 0)}, blocked={goggles_meta.get('blocked', 0)})"
            )
        if verification is not None:
            lines.extend([
                "",
                "## Evidence read",
                f"- Verdict: {verification.verdict}",
                f"- Confidence: {verification.confidence}",
                f"- Support score: {verification.analysis['support_score']:.2f}",
                f"- Conflict score: {verification.analysis['conflict_score']:.2f}",
                f"- Domain diversity: {verification.analysis['domain_diversity']}",
            ])
        if answer.metadata.get("errors"):
            lines.extend(["", "## Retrieval warnings"])
            lines.extend(f"- {error}" for error in answer.metadata["errors"])

        lines.extend(["", "## Sources"])
        for item in source_digest:
            badge = "cross-validated" if item["cross_validated"] else "single-provider"
            date = f" | date={item['date']}" if item["date"] else ""
            lines.append(
                f"{item['rank']}. [{item['title']}]({item['url']}) "
                f"({badge} | {item['domain']} | quality={item['quality']} | freshness={item['freshness']}{date})"
            )
            if item["snippet"]:
                lines.append(f"   - {item['snippet']}")

        lines.extend([
            "",
            "## Use guidance",
            "- Cite sources directly for factual claims.",
            "- Treat low provider or domain diversity as a reason to hedge.",
            "- Surface conflict explicitly when support and conflict are both meaningful.",
        ])

        metadata = {
            **answer.metadata,
            "context_model": "llm-context-v1",
            "source_count": len(source_digest),
            "verification": (
                {
                    "verdict": verification.verdict,
                    "confidence": verification.confidence,
                    "support_score": verification.analysis["support_score"],
                    "conflict_score": verification.analysis["conflict_score"],
                }
                if verification is not None
                else None
            ),
        }
        return LlmContextResult(
            query=query,
            search_type=search_type,
            context_markdown="\n".join(lines),
            citations=citations,
            source_digest=source_digest,
            metadata=metadata,
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    def evidence_report(
        self,
        query: str,
        claim: str | None = None,
        timelimit: str | None = None,
        region: str = "wt-wt",
        providers: list[str] | None = None,
        profile: str | None = None,
        goggles: str | dict | None = None,
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
        logger.info("evidence_report: query=%r claim=%r deep=%s", query, normalized_claim, deep)
        answer = self.search(
            query=query,
            search_type=search_type,
            timelimit=timelimit,
            region=region,
            providers=providers,
            profile=profile,
            goggles=goggles,
            **kwargs,
        )
        verification = self.verify_claim(
            claim=normalized_claim,
            timelimit=timelimit,
            region=region,
            providers=providers,
            profile=profile,
            goggles=goggles,
            include_pages=include_pages or deep,
            deep=deep,
            max_pages=max_pages,
            page_max_chars=page_max_chars,
            answer=answer,
            **kwargs,
        )

        digested_sources: list[dict] = []
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
            "baselines": {
                "majority_vote": self._baseline_majority_vote(verification),
                "keyword_count": self._baseline_keyword_count(
                    self._extract_keywords(normalized_claim), answer.sources,
                ),
                "heuristic_model_verdict": verification.verdict,
                "comparison_note": (
                    "If baselines agree with the heuristic model, the added complexity "
                    "of weighted scoring is justified. If they disagree, the heuristic "
                    "model's source quality and freshness weights may be driving the difference."
                ),
            },
            "semantic_oracle_boundary": {
                "syntactic_signals": ["keyword_overlap", "conflict_markers"],
                "heuristic_signals": ["source_quality", "freshness", "domain_diversity"],
                "page_signals": ["page_content_overlap"],
                "note": "No natural language inference or entailment is performed. "
                        "All classification is pattern-matching and weighted scoring.",
            },
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
            calibration_note=CALIBRATION_NOTE,
        )


class CrossValidatedSearcher(UltimateSearcher):
    """Compatibility alias for the experimental renamed API."""


__all__ = [
    "Answer",
    "EvidenceReportResult",
    "LlmContextResult",
    "CrossValidatedSearcher",
    "Source",
    "SubClaimResult",
    "UltimateSearcher",
    "VerificationResult",
]
