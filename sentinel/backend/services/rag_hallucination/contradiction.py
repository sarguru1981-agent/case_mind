"""Contradiction detector — Milestone 4.

Scans retrieved evidence pages for conflicting values in predefined
forensic categories. Two pages disagree when they both record a value
for the same category and those values differ.

The detector does not decide which page is correct; it reports the conflict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from models.trust_models import Contradiction

# Each rule: (category, label, normaliser-regex that yields a canonical value)
# The pattern must contain a capture group that returns a stable, short value
# so that "northwest corner of the warehouse floor" and "northwest" both
# normalise to "northwest" and are never reported as contradictions.
_RULES: list[tuple[str, str, str]] = [
    (
        "accelerant",
        "Primary accelerant",
        # Matches name before or after the anchor phrase, in the same sentence
        r"(petroleum\s+distillate|ethanol[- ]based\s+\w+|gasoline|kerosene|diesel|acetone|turpentine)[^.]*?(?:primary\s+accelerant|confirmed\s+as)",
    ),
    (
        "fire_origin",
        "Fire origin location",
        # Direction of the fire origin corner — requires "origin" in context
        r"origin\s+was\s+identified[^.]*?\b(northwest|northeast|southeast|southwest)\b",
    ),
    (
        "incident_date",
        "Incident date",
        # Header line or the "at HH:MM on DATE" incident narrative
        r"(?:Date of Incident\s*[:\s]+|at \d{2}:\d{2} [AP]M on )(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
    ),
]


def _extract(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip().lower() if m else None


@dataclass
class ContradictionReport:
    contradictions: list[Contradiction] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.contradictions)

    @property
    def penalty(self) -> float:
        """1.0 = no contradictions; -0.25 per finding, floored at 0.0."""
        return max(0.0, 1.0 - 0.25 * self.count)


class ContradictionDetector:
    def detect(self, pages: list[str]) -> ContradictionReport:
        report = ContradictionReport()

        for category, label, pattern in _RULES:
            findings: list[tuple[int, str]] = []  # (page_index, value)
            for page_idx, page in enumerate(pages):
                val = _extract(page, pattern)
                if val is not None:
                    findings.append((page_idx, val))

            # Compare every pair — report if values differ
            seen: list[tuple[int, str]] = []
            for page_idx, val in findings:
                for prev_idx, prev_val in seen:
                    if val != prev_val:
                        report.contradictions.append(
                            Contradiction(
                                category=category,
                                label=label,
                                page_a=prev_idx + 1,
                                page_b=page_idx + 1,
                                value_a=prev_val,
                                value_b=val,
                            )
                        )
                seen.append((page_idx, val))

        return report
