"""Trust score and trusted response assembly — Milestone 8.

trust_score = 0.40 × retrieval_confidence
            + 0.35 × verification_rate
            + 0.25 × contradiction_penalty

Verdict thresholds: HIGH ≥ 0.75 · MEDIUM ≥ 0.50 · LOW < 0.50
"""
from __future__ import annotations

from models.trust_models import Claim, Contradiction, TrustedResponse
from services.trust.contradiction import ContradictionReport
from services.trust.fact_check import FactCheckReport


def compute_trust_score(
    retrieval_confidence:  float,
    verification_rate:     float,
    contradiction_penalty: float,
) -> float:
    base = (
        0.40 * retrieval_confidence
        + 0.35 * verification_rate
        + 0.25 * contradiction_penalty
    )
    # Any contradiction is a mandatory review signal — cap score below the MEDIUM
    # threshold so the verdict always reads LOW when evidence conflicts are present.
    if contradiction_penalty < 1.0:
        return min(base, 0.49)
    return base


def _verdict(score: float) -> str:
    if score >= 0.75:
        return "HIGH"
    if score >= 0.50:
        return "MEDIUM"
    return "LOW / REVIEW REQUIRED"


def build_trusted_response(
    question:             str,
    answer:               str,
    evidence_pages:       list[str],
    contradiction_report: ContradictionReport,
    fact_report:          FactCheckReport,
    retrieval_confidence: float,
) -> TrustedResponse:
    score = compute_trust_score(
        retrieval_confidence  = retrieval_confidence,
        verification_rate     = fact_report.verification_rate,
        contradiction_penalty = contradiction_report.penalty,
    )

    return TrustedResponse(
        status          = "OK",
        question        = question,
        answer          = answer,
        claims          = fact_report.results,
        contradictions  = contradiction_report.contradictions if contradiction_report.count else None,
        trust_score     = round(score, 3),
        verdict         = _verdict(score),
    )
