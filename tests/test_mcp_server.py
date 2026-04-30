"""Smoke tests for the MCP adapter surface."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from zero_api_key_web_search.core import Answer, LlmContextResult, Source
from zero_api_key_web_search.mcp_server import call_tool, list_tools


class TestMcpServer(unittest.IsolatedAsyncioTestCase):
    async def test_list_tools(self):
        tools = await list_tools()
        names = {tool.name for tool in tools}
        self.assertEqual(
            names,
            {"list_providers", "search_web", "llm_context", "browse_page", "verify_claim", "evidence_report"},
        )

    async def test_call_tool_search_web(self):
        fake_answer = Answer(
            query="python",
            search_type="text",
            answer="Top Sources:\n1. [Example](https://example.com)",
            confidence="MEDIUM",
            sources=[
                Source(
                    url="https://example.com",
                    title="Example",
                    snippet="Example snippet",
                    rank=1,
                    engine="DDG-Text",
                )
            ],
            validation={"total_results": 1, "unique_results": 1, "cross_validated": 0},
            metadata={"providers_used": ["ddgs"], "errors": []},
            elapsed_ms=5,
        )

        with patch("zero_api_key_web_search.mcp_server.searcher.search", return_value=fake_answer):
            result = await call_tool("search_web", {"query": "python"})

        self.assertEqual(len(result), 1)
        self.assertIn("Search Query: python", result[0].text)
        self.assertIn("Detailed Sources:", result[0].text)

    async def test_call_tool_llm_context(self):
        fake_context = LlmContextResult(
            query="python",
            search_type="text",
            context_markdown="# Search context: python\n\n## Sources",
            citations=[],
            source_digest=[],
            metadata={"context_model": "llm-context-v1"},
            elapsed_ms=5,
        )

        with patch("zero_api_key_web_search.mcp_server.searcher.llm_context", return_value=fake_context) as mock_context:
            result = await call_tool(
                "llm_context",
                {"query": "python", "profile": "free-verified", "goggles": "docs-first", "max_sources": 4},
            )

        self.assertEqual(len(result), 1)
        self.assertIn("# Search context: python", result[0].text)
        mock_context.assert_called_once_with(
            query="python",
            search_type="text",
            region="wt-wt",
            timelimit=None,
            providers=None,
            profile="free-verified",
            goggles="docs-first",
            max_sources=4,
            include_verification=True,
        )

    async def test_call_tool_browse_page(self):
        with patch(
            "zero_api_key_web_search.mcp_server.browse",
            return_value={
                "status": "success",
                "url": "https://example.com",
                "title": "Example",
                "content": "Hello from browse",
                "truncated": False,
                "total_length": 17,
            },
        ):
            result = await call_tool("browse_page", {"url": "https://example.com"})

        self.assertEqual(len(result), 1)
        self.assertIn("Title: Example", result[0].text)
        self.assertIn("Hello from browse", result[0].text)

    async def test_call_tool_verify_claim(self):
        fake_result = type(
            "VerificationResult",
            (),
            {
                "claim": "python",
                "verdict": "likely_supported",
                "confidence": "MEDIUM",
                "summary": "Verdict: likely_supported. Weighted support: 0.85. Weighted conflict: 0.00. Independent domains: 1.",
                "supporting_sources": [
                    Source(
                        url="https://example.com",
                        title="Example",
                        snippet="",
                        rank=1,
                        engine="DDG-Text",
                        extra={"verification": {"evidence_strength": 0.85}},
                    )
                ],
                "conflicting_sources": [],
                "analysis": {
                    "verification_model": {"name": "evidence-aware-heuristic-v3"},
                    "support_score": 0.85,
                    "conflict_score": 0.0,
                    "domain_diversity": 1,
                    "provider_diversity": 1,
                    "page_fetches_attempted": 0,
                    "page_fetches_succeeded": 0,
                },
            },
        )()

        with patch("zero_api_key_web_search.mcp_server.searcher.verify_claim", return_value=fake_result):
            result = await call_tool("verify_claim", {"claim": "python"})

        self.assertEqual(len(result), 1)
        self.assertIn("Verdict: likely_supported", result[0].text)
        self.assertIn("Evidence Model:", result[0].text)

    async def test_call_tool_verify_claim_forwards_deep_and_providers(self):
        fake_result = type(
            "VerificationResult",
            (),
            {
                "claim": "python",
                "verdict": "likely_supported",
                "confidence": "MEDIUM",
                "summary": "Verdict: likely_supported. Weighted support: 0.85. Weighted conflict: 0.00. Independent domains: 1.",
                "supporting_sources": [],
                "conflicting_sources": [],
                "analysis": {
                    "verification_model": {"name": "evidence-aware-heuristic-v3"},
                    "support_score": 0.85,
                    "conflict_score": 0.0,
                    "domain_diversity": 1,
                    "provider_diversity": 1,
                    "page_fetches_attempted": 1,
                    "page_fetches_succeeded": 1,
                },
            },
        )()

        with patch("zero_api_key_web_search.mcp_server.searcher.verify_claim", return_value=fake_result) as mock_verify:
            await call_tool(
                "verify_claim",
                {"claim": "python", "providers": ["searxng"], "deep": True, "max_pages": 1},
            )

        mock_verify.assert_called_once_with(
            claim="python",
            region="wt-wt",
            timelimit=None,
            providers=["searxng"],
            profile=None,
            goggles=None,
            include_pages=True,
            deep=True,
            max_pages=1,
        )

    async def test_call_tool_evidence_report(self):
        fake_report = type(
            "EvidenceReportResult",
            (),
            {
                "query": "python release",
                "claim": "Python 3.13 is the latest stable release",
                "verdict": "likely_supported",
                "confidence": "MEDIUM",
                "executive_summary": "Evidence report for 'Python 3.13 is the latest stable release': likely_supported with medium confidence.",
                "verification_summary": "Verdict: likely_supported. Weighted support: 0.85. Weighted conflict: 0.00. Independent domains: 1.",
                "verdict_rationale": ["Support score is 0.85 and conflict score is 0.00."],
                "stance_summary": {
                    "supporting": {"count": 1, "score": 0.85, "top_domains": ["example.com"], "top_titles": ["Example"]},
                    "conflicting": {"count": 0, "score": 0.0, "top_domains": [], "top_titles": []},
                    "neutral": {"count": 0, "score": 0.0, "top_domains": [], "top_titles": []},
                },
                "coverage_warnings": ["Single-provider evidence path. Add another provider when possible."],
                "source_digest": [
                    {
                        "title": "Example",
                        "url": "https://example.com",
                        "classification": "supporting",
                        "evidence_strength": 0.85,
                    }
                ],
                "next_steps": ["Present the claim as likely rather than certain unless you add another corroborating source."],
                "analysis": {
                    "report_model": "evidence-report-v2",
                    "search_confidence": "MEDIUM",
                    "support_score": 0.85,
                    "conflict_score": 0.0,
                    "provider_diversity": 1,
                    "page_fetches_attempted": 0,
                    "page_fetches_succeeded": 0,
                },
            },
        )()

        with patch("zero_api_key_web_search.mcp_server.searcher.evidence_report", return_value=fake_report):
            result = await call_tool("evidence_report", {"query": "python release"})

        self.assertEqual(len(result), 1)
        self.assertIn("Evidence Report Query: python release", result[0].text)
        self.assertIn("Report Model:", result[0].text)
        self.assertIn("Why this verdict:", result[0].text)
        self.assertIn("Coverage warnings:", result[0].text)
        self.assertIn("Stance summary:", result[0].text)

    async def test_call_tool_evidence_report_forwards_claim_and_deep(self):
        fake_report = type(
            "EvidenceReportResult",
            (),
            {
                "query": "python release",
                "claim": "Python 3.13 is the latest stable release",
                "verdict": "likely_supported",
                "confidence": "MEDIUM",
                "executive_summary": "summary",
                "verification_summary": "verification",
                "verdict_rationale": [],
                "stance_summary": {},
                "coverage_warnings": [],
                "source_digest": [],
                "next_steps": [],
                "analysis": {
                    "report_model": "evidence-report-v2",
                    "search_confidence": "MEDIUM",
                    "support_score": 0.85,
                    "conflict_score": 0.0,
                    "provider_diversity": 1,
                    "page_fetches_attempted": 1,
                    "page_fetches_succeeded": 1,
                },
            },
        )()

        with patch("zero_api_key_web_search.mcp_server.searcher.evidence_report", return_value=fake_report) as mock_report:
            await call_tool(
                "evidence_report",
                {
                    "query": "python release",
                    "claim": "Python 3.13 is the latest stable release",
                    "providers": ["searxng"],
                    "deep": True,
                    "max_pages": 1,
                    "max_sources": 3,
                },
            )

        mock_report.assert_called_once_with(
            query="python release",
            claim="Python 3.13 is the latest stable release",
            region="wt-wt",
            timelimit=None,
            providers=["searxng"],
            profile=None,
            goggles=None,
            include_pages=True,
            deep=True,
            max_pages=1,
            max_sources=3,
        )
