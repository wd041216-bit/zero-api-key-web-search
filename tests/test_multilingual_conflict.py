"""Tests for multilingual conflict detection markers."""

from __future__ import annotations

import unittest

from cross_validated_search.core import Source, UltimateSearcher, CONFLICT_MARKERS


class TestMultilingualConflictMarkers(unittest.TestCase):
    def setUp(self):
        self.searcher = UltimateSearcher(timeout=5)

    def test_english_markers_exist(self):
        english_markers = ["false", "incorrect", "disputed", "debunked"]
        for marker in english_markers:
            self.assertIn(marker, CONFLICT_MARKERS)

    def test_spanish_markers_exist(self):
        spanish_markers = ["falso", "desmentido", "engañoso"]
        for marker in spanish_markers:
            self.assertIn(marker, CONFLICT_MARKERS)

    def test_french_markers_exist(self):
        french_markers = ["faux", "démenti", "contesté"]
        for marker in french_markers:
            self.assertIn(marker, CONFLICT_MARKERS)

    def test_german_markers_exist(self):
        german_markers = ["falsch", "widerlegt", "bestritten"]
        for marker in german_markers:
            self.assertIn(marker, CONFLICT_MARKERS)

    def test_chinese_markers_exist(self):
        chinese_markers = ["错误", "不实", "辟谣"]
        for marker in chinese_markers:
            self.assertIn(marker, CONFLICT_MARKERS)

    def test_spanish_conflict_detected(self):
        source = Source(
            url="https://example.es/factcheck",
            title="Verificación: la afirmación es falsa",
            snippet="La afirmación de que la luna es de queso ha sido desmentida por científicos.",
            engine="DDG-Text",
            date="2026-03-20",
        )
        classification, evidence = self.searcher._classify_source_against_claim(
            ["afirmación", "luna", "queso"],
            source,
        )
        self.assertTrue(evidence["conflict_markers_detected"])

    def test_french_conflict_detected(self):
        source = Source(
            url="https://example.fr/factcheck",
            title="Vérification: la déclaration est fausse",
            snippet="La déclaration a été démentie par des experts et est trompeuse.",
            engine="DDG-Text",
            date="2026-03-20",
        )
        classification, evidence = self.searcher._classify_source_against_claim(
            ["déclaration", "experts"],
            source,
        )
        self.assertTrue(evidence["conflict_markers_detected"])

    def test_german_conflict_detected(self):
        source = Source(
            url="https://example.de/faktencheck",
            title="Faktencheck: Die Behauptung ist falsch",
            snippet="Die Behauptung wurde widerlegt und ist irreführend.",
            engine="DDG-Text",
            date="2026-03-20",
        )
        classification, evidence = self.searcher._classify_source_against_claim(
            ["behauptung", "widerlegt"],
            source,
        )
        self.assertTrue(evidence["conflict_markers_detected"])

    def test_chinese_conflict_detected(self):
        source = Source(
            url="https://example.cn/factcheck",
            title="辟谣：该说法错误",
            snippet="该说法已被辟谣，属于不实信息，没有证据支持。",
            engine="DDG-Text",
            date="2026-03-20",
        )
        classification, evidence = self.searcher._classify_source_against_claim(
            ["说法", "辟谣"],
            source,
        )
        self.assertTrue(evidence["conflict_markers_detected"])

    def test_english_conflict_still_works(self):
        source = Source(
            url="https://example.com/factcheck",
            title="Fact check says false",
            snippet="A fact check claims Python 3.13 is not the latest stable release and says the statement is false.",
            engine="DDG-Text",
            date="2026-03-20",
        )
        classification, evidence = self.searcher._classify_source_against_claim(
            ["python", "stable", "release"],
            source,
        )
        self.assertTrue(evidence["conflict_markers_detected"])


if __name__ == "__main__":
    unittest.main()