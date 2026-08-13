"""Prompt injection guard — Milestone 7.

Runs before retrieval. Rejects queries that contain known override patterns.
If injection is detected, the request never reaches the RAG pipeline or LLM.
"""
from __future__ import annotations

import re

_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(?:(?:all|previous|prior|the)\s+)+(instructions?|context|prompt)",
        r"disregard\s+(the\s+)?(evidence|instructions?|context|above)",
        r"you\s+are\s+(now\s+)?(a\s+)?(?!a\s+police|an?\s+evidence)",
        r"forget\s+(everything|all|what|the)",
        r"act\s+as\s+if",
        r"pretend\s+(you\s+are|to\s+be)",
        r"new\s+(instructions?|prompt|task|role)",
        r"override\s+(the\s+)?(system|prompt|instructions?)",
        r"bypass\s+(the\s+)?(filter|guard|safety|restrictions?)",
    ]
]


def check_injection(query: str) -> bool:
    """Returns True if a prompt injection pattern is detected."""
    return any(p.search(query) for p in _PATTERNS)
