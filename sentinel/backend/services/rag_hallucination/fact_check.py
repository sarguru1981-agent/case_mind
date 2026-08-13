"""Claim extraction and fact checking — Milestones 5 & 6.

extract_claims  : breaks an LLM answer into discrete factual assertions.
verify_claims   : checks each claim against the retrieved evidence pages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from models.trust_models import Claim

# Sentence-ending punctuation followed by space or end-of-string
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Prefixes that add no factual content
_META_PREFIXES = re.compile(
    r"^(based on|according to|the evidence (suggests|indicates|shows)|"
    r"it (appears|seems)|overall|in summary|to summarize)[,:\s]+",
    re.IGNORECASE,
)

_DISCLAIMER_PATTERNS = re.compile(
    r"(cannot|could not|unable to|no (further|additional)|insufficient|limited)\s+\w+",
    re.IGNORECASE,
)

# Patterns that suggest factual substance
_CLAIM_VERBS = re.compile(
    r"\b(confirmed|identified|recovered|found|determined|concluded|"
    r"indicated|recorded|located|detected|established)\b",
    re.IGNORECASE,
)

_PAGE_CITE = re.compile(r"\[page\s*(\d+)\]", re.IGNORECASE)

_STOP_WORDS = frozenset(
    "a an the is was were be been being have has had do does did will would "
    "could should may might shall of in on at to for with by from as into "
    "through during before after above below between among this that these "
    "those which who whom what when where why how and or but not no nor so".split()
)


def _significant_words(text: str) -> set[str]:
    return {
        w.lower()
        for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)
        if w.lower() not in _STOP_WORDS
    }


def _claim_confidence(sentence: str) -> float:
    score = 0.5
    if _CLAIM_VERBS.search(sentence):
        score += 0.2
    if _PAGE_CITE.search(sentence):
        score += 0.2
    if re.search(r"\d", sentence):
        score += 0.1
    return min(score, 1.0)


def extract_claims(answer: str) -> list[Claim]:
    sentences = _SENT_SPLIT.split(answer.strip())
    claims: list[Claim] = []

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20:
            continue
        if _DISCLAIMER_PATTERNS.search(sent):
            continue

        cleaned = _META_PREFIXES.sub("", sent).strip()
        cite_m  = _PAGE_CITE.search(cleaned)
        cited   = int(cite_m.group(1)) if cite_m else None

        claims.append(
            Claim(
                text       = cleaned,
                cited_page = cited,
                confidence = _claim_confidence(cleaned),
            )
        )

    return claims


@dataclass
class FactCheckReport:
    results:           list[Claim]
    verified_count:    int
    total_count:       int

    @property
    def verification_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.verified_count / self.total_count


_VERIFY_THRESHOLD = 0.40


def verify_claims(claims: list[Claim], pages: list[str]) -> FactCheckReport:
    """Check each claim against its cited page (or best-matching page)."""
    verified: list[Claim] = []
    verified_count = 0

    for claim in claims:
        claim_words = _significant_words(claim.text)
        if not claim_words:
            verified.append(Claim(
                text=claim.text, cited_page=claim.cited_page,
                confidence=claim.confidence, verified=False,
            ))
            continue

        # Choose the page to check against
        if claim.cited_page and 1 <= claim.cited_page <= len(pages):
            target = pages[claim.cited_page - 1]
        else:
            # Fall back to page with highest word overlap
            best_idx = max(
                range(len(pages)),
                key=lambda i: len(claim_words & _significant_words(pages[i])),
            )
            target = pages[best_idx]

        page_words = _significant_words(target)
        overlap    = len(claim_words & page_words) / len(claim_words)
        is_verified = overlap >= _VERIFY_THRESHOLD

        if is_verified:
            verified_count += 1

        verified.append(Claim(
            text       = claim.text,
            cited_page = claim.cited_page,
            confidence = claim.confidence,
            verified   = is_verified,
        ))

    return FactCheckReport(
        results        = verified,
        verified_count = verified_count,
        total_count    = len(claims),
    )
