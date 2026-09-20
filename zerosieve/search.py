#!/usr/bin/env python3
"""Compatibility layer for the unshipped renamed search API.

This module preserves import compatibility for experiments that used the
`CrossValidatedSearcher` naming while delegating all real behavior to the
current shared core and stable `search-web` CLI entrypoint.
"""

from zerosieve.core import (
    Answer,
    CrossValidatedSearcher,
    Source,
    UltimateSearcher,
    VerificationResult,
)
from zerosieve.search_web import main

__all__ = [
    "Answer",
    "CrossValidatedSearcher",
    "Source",
    "UltimateSearcher",
    "VerificationResult",
    "main",
]
