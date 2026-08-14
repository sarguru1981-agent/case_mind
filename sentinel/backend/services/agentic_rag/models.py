"""Data models for Agentic RAG investigation state.

These models capture the full investigation lifecycle so that the future
police investigation UI can render each step: plan, search, evidence,
lead, decision, and final archive-level conclusion.

Crucially, no hidden chain-of-thought is stored here.  Every field
contains information that is safe and useful to show the detective.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Controlled event vocabulary
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    PLAN_CREATED             = "PLAN_CREATED"
    SEARCH_STARTED           = "SEARCH_STARTED"
    EVIDENCE_FOUND           = "EVIDENCE_FOUND"
    LEAD_DISCOVERED          = "LEAD_DISCOVERED"
    SEARCH_UPDATED           = "SEARCH_UPDATED"
    ARCHIVE_BOUNDARY_REACHED = "ARCHIVE_BOUNDARY_REACHED"
    INVESTIGATION_COMPLETE   = "INVESTIGATION_COMPLETE"


class InvestigationStatus(str, Enum):
    PLANNING         = "PLANNING"
    SEARCHING        = "SEARCHING"
    ARCHIVE_BOUNDARY = "ARCHIVE_BOUNDARY"
    COMPLETE         = "COMPLETE"


# ---------------------------------------------------------------------------
# Evidence and leads
# ---------------------------------------------------------------------------

class EvidenceHit(BaseModel):
    """A single piece of retrieved evidence, attributed to its source."""
    case_id:     str    # e.g. "MCR-2025-0101"
    source_file: str    # filename, e.g. "robbery-001-hawthorne-jewellers.txt"
    text:        str    # retrieved evidence chunk
    confidence:  float  # TF-IDF retrieval confidence for this file
    hop:         int    # which search iteration (1-indexed) produced this hit


class Lead(BaseModel):
    """A cross-case clue that the investigation decided to pursue next.

    label          — short identifier shown in the UI timeline
    context        — user-facing explanation of why this is a lead
    cases_found_in — which case IDs surfaced this entity
    search_query   — the concrete archive query generated from this lead
    """
    label:         str
    context:       str
    cases_found_in: list[str]
    search_query:  str


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

class InvestigationPlan(BaseModel):
    """Retrieval-focused investigation plan.

    Agentic RAG planning is about deciding what archive evidence to search
    for first and what relationships to pursue — not autonomous task
    decomposition across arbitrary goals.
    """
    objective:      str
    initial_query:  str
    planned_angles: list[str]
    max_hops:       int


# ---------------------------------------------------------------------------
# Timeline events (user-facing, no raw model reasoning)
# ---------------------------------------------------------------------------

class InvestigationEvent(BaseModel):
    type:    EventType
    summary: str            # what happened, in plain language
    hop:     Optional[int]  = None
    query:   Optional[str]  = None


# ---------------------------------------------------------------------------
# Final result — structured for the future UI
# ---------------------------------------------------------------------------

class InvestigationResult(BaseModel):
    """Complete Agentic RAG investigation result.

    Designed to allow the UI to render:
      PLAN → SEARCH → EVIDENCE → LEAD → DECISION → NEXT SEARCH → … → BOUNDARY
    """
    objective:                       str
    status:                          InvestigationStatus
    plan:                            InvestigationPlan
    timeline:                        list[InvestigationEvent]
    searches_performed:              int
    evidence_hits:                   list[EvidenceHit]
    leads_discovered:                list[Lead]
    archive_sources:                 list[str]   # case files that were searched
    archive_level_conclusion:        Optional[str] = None
    stopping_reason:                 str
    requires_external_investigation: list[str]   # open questions the archive cannot answer
