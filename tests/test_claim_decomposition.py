"""Tests for claim decomposition logic."""

from __future__ import annotations

import unittest

from cross_validated_search.core import UltimateSearcher


class TestClaimDecomposition(unittest.TestCase):
    def setUp(self):
        self.searcher = UltimateSearcher(timeout=5)

    def test_simple_claim_not_decomposed(self):
        sub = self.searcher.decompose_claim("Python 3.13 is the latest stable release")
        self.assertEqual(len(sub), 1)
        self.assertEqual(sub[0], "Python 3.13 is the latest stable release")

    def test_compound_claim_with_and(self):
        sub = self.searcher.decompose_claim(
            "Python 3.13 is the latest stable release and Rust 1.76 was released in February"
        )
        self.assertEqual(len(sub), 2)
        self.assertTrue(any("Python" in s for s in sub))
        self.assertTrue(any("Rust" in s for s in sub))

    def test_compound_claim_with_but(self):
        sub = self.searcher.decompose_claim(
            "The economy grew by 3% but unemployment rose to 5%"
        )
        self.assertEqual(len(sub), 2)

    def test_compound_claim_with_semicolon(self):
        sub = self.searcher.decompose_claim(
            "GDP grew by 3 percent; inflation remained steady at 2 percent"
        )
        self.assertEqual(len(sub), 2)

    def test_compound_claim_with_period(self):
        sub = self.searcher.decompose_claim(
            "The project was completed on time. The budget was under the limit."
        )
        self.assertEqual(len(sub), 2)

    def test_short_fragments_filtered_out(self):
        sub = self.searcher.decompose_claim(
            "The sky is blue and it is nice but rain falls"
        )
        # "it is nice" is 10 chars, "rain falls" is 10 chars - both too short to be useful sub-claims on their own
        # but "The sky is blue" (15) and "rain falls" could pass; what matters is the decomposition works
        self.assertGreaterEqual(len(sub), 1)
        for s in sub:
            self.assertGreaterEqual(len(s), 10)

    def test_triple_compound_claim(self):
        sub = self.searcher.decompose_claim(
            "Python 3.13 is the latest stable release, and Rust 1.76 was released in February, while Go 1.22 shipped in February"
        )
        self.assertGreaterEqual(len(sub), 2)

    def test_sub_claims_in_verification_result(self):
        from cross_validated_search.core import Source
        from unittest.mock import patch

        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Python 3.13 stable",
                snippet="Python 3.13 is the latest stable release and Rust 1.76 was released.",
                engine="DDG-Text",
                date="2026-03-20",
            ),
        ]
        with patch.object(self.searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Python 3.13 is the latest stable release and Rust 1.76 was released",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "MEDIUM",
                    "sources": fake_sources,
                    "validation": {"total_results": 1, "unique_results": 1, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()

            result = self.searcher.verify_claim(
                "Python 3.13 is the latest stable release and Rust 1.76 was released"
            )

        self.assertIsInstance(result.sub_claims, list)
        self.assertGreater(len(result.sub_claims), 0)
        for sc in result.sub_claims:
            self.assertTrue(hasattr(sc, "sub_claim"))
            self.assertTrue(hasattr(sc, "verdict"))
            self.assertTrue(hasattr(sc, "confidence"))


if __name__ == "__main__":
    unittest.main()