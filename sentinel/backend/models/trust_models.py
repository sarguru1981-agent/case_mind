"""Permanent API contract for CaseMind Sentinel.

Milestone 1: HealthResponse, VersionResponse, InvestigationRequest, TrustedResponse.
Later milestones populate the Optional fields on TrustedResponse.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Infrastructure responses
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    application: str
    version: str


class VersionResponse(BaseModel):
    application: str
    version: str
    subtitle: str


# ---------------------------------------------------------------------------
# Investigation request
# ---------------------------------------------------------------------------

class InvestigationRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The detective's investigation question")
    case_file: Optional[str] = Field(None, description="Case file name to query against")


# ---------------------------------------------------------------------------
# Trust layer models — populated in Milestones 4-8
# ---------------------------------------------------------------------------

class Claim(BaseModel):
    text: str
    cited_page: Optional[int] = None
    confidence: float = 1.0
    verified: Optional[bool] = None


class Contradiction(BaseModel):
    category: str
    label: str
    page_a: int
    page_b: int
    value_a: str
    value_b: str


# ---------------------------------------------------------------------------
# Primary response — permanent contract
# ---------------------------------------------------------------------------

class TrustedResponse(BaseModel):
    """POST /api/query response contract.

    status values (controlled vocabulary):
      OK                 — pipeline completed; answer and trust fields populated
      INJECTION_DETECTED — query rejected by prompt injection guard; no LLM call made
      ERROR              — pipeline exception; message contains the reason

    verdict values (when status is OK):
      HIGH               — trust_score >= 0.75; answer is reliable
      MEDIUM             — trust_score >= 0.50; review recommended
      LOW / REVIEW REQUIRED — trust_score < 0.50 or contradictions detected
    """

    status: str
    message: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    claims: Optional[list[Claim]] = None
    contradictions: Optional[list[Contradiction]] = None
    trust_score: Optional[float] = None
    verdict: Optional[str] = None
