"""Tests for the optional Laya neural sieve (filter + stance) with a stub agent.

These tests never import torch or the real laya package: a scripted fake
agent stands in for ``laya.load`` so the routing, threshold and fallback
logic can be validated in a plain environment.
"""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from zerosieve import laya_filter
from zerosieve.core import Answer, Source, UltimateSearcher
from zerosieve.laya_filter import (
    LayaBackend,
    LayaUnavailableError,
    blend_strength,
    classify_stance,
    filter_sources,
)


class FakeLayaAgent:
    """Scripted stand-in: maps question ids to canned yes-probabilities.

    ``script`` maps question id -> float, or a list of floats popped in call
    order (for per-source sequences). Missing ids answer 0.0. A ``boom_on``
    set of question ids raises, to exercise the per-source error fallback.
    """

    def __init__(self, script: dict[str, float | list[float]], boom_on: set[str] | None = None):
        self.script = {k: (list(v) if isinstance(v, list) else v) for k, v in script.items()}
        self.boom_on = boom_on or set()
        self.calls: list[tuple[object, tuple]] = []

    def predict(self, state, questions):
        self.calls.append((state, tuple(questions)))
        answers = {}
        for qid, qdef in questions.items():
            if qid in self.boom_on:
                raise RuntimeError("simulated inference failure")
            value = self.script.get(qid, 0.0)
            prob = float(value.pop(0)) if isinstance(value, list) else float(value)
            answers[qid] = {
                "type": qdef.get("type", "noul"),
                "noul": prob,
                "confidence": max(prob, 1.0 - prob),
            }
        return {"model": "fake-laya", "answers": answers, "usage": {}}


def make_backend(agent: FakeLayaAgent) -> LayaBackend:
    backend = LayaBackend(model_id="fake/laya")
    backend._agent = agent
    return backend


def fake_answer(sources: list[Source]) -> Answer:
    return Answer(
        query="q",
        search_type="text",
        answer="Top Sources",
        confidence="MEDIUM",
        sources=sources,
        validation={"total_results": len(sources)},
        metadata={"providers_used": ["ddgs"], "errors": []},
        elapsed_ms=1,
    )


class TestFilterSources(unittest.TestCase):
    def test_threshold_keeps_and_drops(self):
        sources = [
            Source(url="https://a.com/1", title="relevant", snippet="on topic"),
            Source(url="https://b.com/2", title="noise", snippet="unrelated"),
        ]
        backend = make_backend(FakeLayaAgent({"relevant": [0.93, 0.05]}))
        kept, meta = filter_sources("query text", sources, backend, threshold=0.5)
        self.assertEqual([s.url for s in kept], ["https://a.com/1"])
        self.assertEqual(meta["dropped"], 1)
        self.assertEqual(meta["kept"], 1)
        self.assertTrue(meta["enabled"])
        self.assertEqual(sources[0].extra["laya"]["relevant"], 0.93)

    def test_backend_error_keeps_source(self):
        sources = [Source(url="https://a.com/1", title="t", snippet="s")]
        backend = make_backend(FakeLayaAgent({}, boom_on={"relevant"}))
        kept, meta = filter_sources("q", sources, backend)
        self.assertEqual(len(kept), 1)
        self.assertEqual(meta["errors"], 1)
        # a broken sieve must never silently empty the funnel
        self.assertNotIn("laya", kept[0].extra)


class TestClassifyStance(unittest.TestCase):
    def test_support_conflict_and_neutral(self):
        backend = make_backend(FakeLayaAgent({"support": 0.9, "conflict": 0.1}))
        classification, evidence = classify_stance("claim text", Source(url="https://a.com", title="t"), backend)
        self.assertEqual(classification, "supporting")
        self.assertEqual(evidence["laya_stance"]["p_support"], 0.9)

        backend = make_backend(FakeLayaAgent({"support": 0.2, "conflict": 0.85}))
        classification, evidence = classify_stance("claim text", Source(url="https://a.com", title="t"), backend)
        self.assertEqual(classification, "conflicting")

        backend = make_backend(FakeLayaAgent({"support": 0.4, "conflict": 0.4}))
        classification, evidence = classify_stance("claim text", Source(url="https://a.com", title="t"), backend)
        self.assertEqual(classification, "neutral")

    def test_inference_error_degrades_to_neutral(self):
        backend = make_backend(FakeLayaAgent({}, boom_on={"support"}))
        classification, evidence = classify_stance("claim", Source(url="https://a.com", title="t"), backend)
        self.assertEqual(classification, "neutral")
        self.assertEqual(evidence["laya_stance"]["status"], "error")


class TestBlendStrength(unittest.TestCase):
    def test_weights_and_clamp(self):
        self.assertEqual(blend_strength(1.0, 1.0, 1.0), 1.0)
        self.assertEqual(blend_strength(0.0, 0.0, 0.0), 0.0)
        # stance dominates: 0.55 * 1.0 + 0.35 * 0 + 0.10 * 0
        self.assertEqual(blend_strength(1.0, 0.0, 0.0), 0.55)


class TestVerifyClaimWithLaya(unittest.TestCase):
    def _run(self, verifier: str, script: dict[str, float]):
        searcher = UltimateSearcher(timeout=5)
        backend = make_backend(FakeLayaAgent(script))
        searcher._laya_backend = backend
        sources = [
            Source(
                url="https://a.com/support",
                title="Supporting page",
                snippet="Reports say the claim holds.",
                engine="DDG-Text",
                date="2026-09-01",
            ),
            Source(
                url="https://b.com/conflict",
                title="Contradicting page",
                snippet="Other outlets disagree with the statement.",
                engine="DDG-Text",
                date="2026-09-02",
            ),
        ]
        with patch.object(searcher, "search", return_value=fake_answer(sources)):
            return searcher.verify_claim("some claim", verifier=verifier)

    def test_laya_verifier_classifies_by_probability(self):
        result = self._run("laya", {"support": 0.95, "conflict": 0.05})
        self.assertEqual(result.analysis["verification_model"]["name"], "laya-stance-v1")
        self.assertGreaterEqual(len(result.supporting_sources), 1)
        evidence = result.supporting_sources[0].extra["verification"]
        self.assertEqual(evidence["laya_stance"]["status"], "ok")
        # neural strength blended with quality/freshness
        self.assertGreater(evidence["evidence_strength"], 0.5)

    def test_laya_verifier_surfaces_conflict(self):
        result = self._run("laya", {"support": 0.1, "conflict": 0.9})
        self.assertGreaterEqual(len(result.conflicting_sources), 1)

    def test_heuristic_default_untouched(self):
        result = self._run("heuristic", {"support": 0.95, "conflict": 0.05})
        self.assertEqual(result.analysis["verification_model"]["name"], "evidence-aware-heuristic-v3")
        self.assertNotIn("laya_stance", result.supporting_sources[0].extra.get("verification", {}))

    def test_unknown_verifier_rejected(self):
        searcher = UltimateSearcher(timeout=5)
        with self.assertRaises(ValueError):
            with patch.object(searcher, "search", return_value=fake_answer([])):
                searcher.verify_claim("claim", verifier="oracle")


class TestSearchLayaFilter(unittest.TestCase):
    def test_filter_metadata_recorded(self):
        sources = [
            Source(url="https://a.com/1", title="keep me", snippet="relevant"),
            Source(url="https://b.com/2", title="drop me", snippet="noise"),
        ]
        searcher = UltimateSearcher(timeout=5)
        searcher._laya_backend = make_backend(FakeLayaAgent({"relevant": [0.9, 0.1]}))
        with patch.object(searcher, "_cross_validate", side_effect=lambda rs: rs), patch.object(
            searcher, "_search_provider", side_effect=lambda **kw: list(sources)
        ):
            answer = searcher.search("query", laya_filter=True)
        self.assertTrue(answer.metadata["laya_filter"]["enabled"])
        self.assertEqual(answer.metadata["laya_filter"]["dropped"], 1)
        self.assertEqual(len(answer.sources), 1)

    def test_fallback_when_laya_missing(self):
        sources = [
            Source(url="https://a.com/1", title="t1", snippet="s1"),
            Source(url="https://b.com/2", title="t2", snippet="s2"),
        ]
        searcher = UltimateSearcher(timeout=5)
        with patch.object(searcher, "_cross_validate", side_effect=lambda rs: rs), patch.object(
            searcher, "_search_provider", side_effect=lambda **kw: list(sources)
        ):
            with patch.dict(sys.modules, {"laya": None}):
                answer = searcher.search("query", laya_filter=True)
        self.assertFalse(answer.metadata["laya_filter"]["enabled"])
        self.assertIn("error", answer.metadata["laya_filter"])
        # graceful: nothing lost
        self.assertEqual(len(answer.sources), 2)


class TestLazyLoading(unittest.TestCase):
    def test_backend_lazy_until_predict(self):
        loaded = {"count": 0}

        class ExplodingLoader:
            @staticmethod
            def load(*a, **kw):
                loaded["count"] += 1
                raise RuntimeError("should not load")

        stub = types.SimpleNamespace(load=ExplodingLoader.load)
        with patch.dict(sys.modules, {"laya": stub}):
            backend = LayaBackend(model_id="fake/laya")
            # constructing and inspecting must not load the checkpoint
            self.assertEqual(backend.model_label, "fake/laya")
            self.assertEqual(loaded["count"], 0)
            with self.assertRaises(LayaUnavailableError):
                backend.warmup()
            self.assertEqual(loaded["count"], 1)

    def test_laya_importable_respects_missing_package(self):
        with patch.dict(sys.modules, {"laya": None}):
            self.assertFalse(laya_filter.laya_importable())


if __name__ == "__main__":
    unittest.main()
