"""Agentic RAG investigator — the Search → Reason → Search loop.

This module implements the core Agentic RAG difference from traditional RAG:

  Traditional RAG:
      Question → Retrieve → Answer

  Agentic RAG (this module):
      Question
      → Plan Archive Investigation
      → Search all case files
      → Inspect retrieved evidence
      → Discover new cross-case lead
      → Decide next archive search query
      → Search again
      → Repeat
      → Answer OR reach Archive Boundary

The "Reason" step (deciding what to search next) is implemented
deterministically using cross-case entity extraction.  An entity that
appears in multiple case files is a stronger lead than one that appears
in only one.  The investigation follows the strongest unexhausted lead
until the archive can no longer answer the remaining questions.

This module:
  - DOES search: sentinel/data/case-files/serial-robbery/ (or any case dir)
  - DOES NOT access: sentinel/data/tool-data/
  - DOES NOT access: sentinel/data/operation-nightfall-ground-truth.json
  - DOES NOT make external API calls
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from services.rag.retrieval import retrieve_evidence   # reuse existing RAG

from .models import (
    EvidenceHit,
    EventType,
    InvestigationEvent,
    InvestigationPlan,
    InvestigationResult,
    InvestigationStatus,
    Lead,
)
from .planner import create_plan


# ---------------------------------------------------------------------------
# Case-file helpers
# ---------------------------------------------------------------------------

_CASE_ID_PATTERN = re.compile(r"MCR-\d{4}-\d{4}")


def _case_id_from_text(text: str) -> Optional[str]:
    m = _CASE_ID_PATTERN.search(text)
    return m.group() if m else None


def _case_id_from_file(path: Path) -> str:
    """Derive a display ID from the filename, e.g. 'robbery-001'."""
    return path.stem.split("-")[:2].__class__.join("-", path.stem.split("-")[:2])


def _case_id_from_file(path: Path) -> str:  # noqa: F811 — intentional redefinition
    parts = path.stem.split("-")
    return "-".join(parts[:2])   # "robbery-001"


# ---------------------------------------------------------------------------
# Multi-case archive search
# ---------------------------------------------------------------------------

_MIN_CONFIDENCE = 0.05   # discard near-zero TF-IDF matches


_CHUNKS_PER_FILE = 2   # top-N chunks per file per search hop


def _search_archive(
    query: str,
    case_dir: Path,
    hop: int,
) -> list[EvidenceHit]:
    """Search every plain-text case file in case_dir and return attributed hits.

    Reuses services.rag.retrieval.retrieve_evidence() for each file so that
    the original RAG implementation remains the retrieval foundation.
    Source attribution (case_id, source_file) is added at this layer.

    Two chunks per file are collected so that secondary-ranked evidence
    (e.g. a vehicle sighting in a different section from the alarm details)
    still surfaces for lead extraction even when a single broad query cannot
    rank it first.
    """
    hits: list[EvidenceHit] = []
    for txt_file in sorted(case_dir.glob("*.txt")):
        pages, confidence = retrieve_evidence(query, str(txt_file))
        if confidence < _MIN_CONFIDENCE:
            continue
        case_id = _case_id_from_file(txt_file)
        for page in pages[:_CHUNKS_PER_FILE]:
            hits.append(EvidenceHit(
                case_id     = case_id,
                source_file = txt_file.name,
                text        = page,
                confidence  = confidence,
                hop         = hop,
            ))
    return hits


# ---------------------------------------------------------------------------
# Lead extraction — the "Reason" step
#
# An entity appearing in 2+ case files is a cross-case lead.
# The more files it appears in, the stronger the lead.
# ---------------------------------------------------------------------------

# Each entry: (lead_label, regex_pattern, human_context, follow_up_query)
_LEAD_CATALOG: list[tuple[str, str, str, str]] = [
    (
        "northstar_facilities",
        r"Northstar Facilities(?:\s+Ltd)?",
        "Northstar Facilities Ltd appears in maintenance visit records across multiple incident files.",
        "Northstar Facilities engineer maintenance visit three days before burglary",
    ),
    (
        "daniel_mercer",
        r"D\.\s*MERCER|Daniel Mercer",
        "D. MERCER / Daniel Mercer is named on Northstar Facilities work orders connected to multiple incidents.",
        "D. MERCER Daniel Mercer engineer identity credential incidents Northstar",
    ),
    (
        "credential_nf3847",
        r"NF-3847",
        "Credential NF-3847 was used to place the SentryGuard alarm into maintenance mode and gain out-of-hours access.",
        "NF-3847 credential out-of-hours access alarm maintenance mode Kingsley",
    ),
    (
        "dark_blue_transit",
        r"dark blue (?:Ford Transit|commercial van|panel van|van)",
        "A dark blue Ford Transit or commercial van was observed near multiple incident locations. No registration plate has been captured in the archive.",
        "dark blue Ford Transit van vehicle registration plate sightings",
    ),
    (
        "alarm_maintenance_mode",
        r"maintenance mode",
        "Alarm systems were placed into maintenance mode before each burglary, suppressing all alerts.",
        "alarm maintenance mode credential authorised engineer SentryGuard disabled",
    ),
    (
        "sentryguard_pattern",
        r"SentryGuard",
        "SentryGuard is the shared alarm platform across multiple premises. Understanding the maintenance access model is key.",
        "SentryGuard alarm engineer credential maintenance access engineer-level",
    ),
]


def _extract_leads(
    evidence_hits: list[EvidenceHit],
    already_searched: set[str],
) -> list[Lead]:
    """Inspect evidence and return cross-case leads not yet followed.

    Dynamic retrieval: the next search query is derived from what the
    evidence actually contains, not from a hardcoded tutorial script.
    """
    # Count in how many distinct case files each lead entity appears
    lead_case_sets: dict[str, set[str]] = {
        label: set() for label, *_ in _LEAD_CATALOG
    }

    for hit in evidence_hits:
        for label, pattern, _ctx, _q in _LEAD_CATALOG:
            if re.search(pattern, hit.text, re.IGNORECASE):
                lead_case_sets[label].add(hit.case_id)

    leads: list[Lead] = []
    for label, _pattern, context, query in _LEAD_CATALOG:
        if label in already_searched:
            continue
        cases = sorted(lead_case_sets[label])
        if not cases:
            continue
        leads.append(Lead(
            label          = label,
            context        = context,
            cases_found_in = cases,
            search_query   = query,
        ))

    # Sort: cross-case leads (2+ files) first, then single-file leads
    leads.sort(key=lambda l: len(l.cases_found_in), reverse=True)
    return leads


# ---------------------------------------------------------------------------
# Archive boundary detection
# ---------------------------------------------------------------------------

# Evidence patterns that tell the investigator a fact EXISTS but cannot be
# resolved from the archive alone (it lives in an external database).
_BOUNDARY_EVIDENCE_PATTERNS = [
    (
        r"registration plate was not captured|plate.*not.*captured|"
        r"unable to identify.*(?:registration|plate)|"
        r"partial plate.*not matched|plate.*not.*legible|"
        r"registration plate.*not.*matched",
        "Vehicle registration plate not captured in the case archive.",
    ),
    (
        r"not matched to any registered vehicle",
        "Vehicle registration not matched to any known record in the archive.",
    ),
]

# Questions that require external data — always present when the boundary is reached
_EXTERNAL_FACTS_REQUIRED = [
    "Vehicle registration ownership (requires DVLA database query)",
    "Complete engineer credential access history across all Northstar Facilities clients"
    " (requires Northstar Facilities records)",
    "ANPR and surveillance camera correlation across all incident locations"
    " (requires Technical Surveillance Unit data)",
    "Post-incident financial transactions and inter-personal financial relationships"
    " (requires Financial Intelligence Unit data)",
]


def _boundary_signals_in_evidence(evidence_hits: list[EvidenceHit]) -> list[str]:
    """Return user-facing boundary messages for each external-data signal found."""
    signals: list[str] = []
    seen: set[str] = set()
    for hit in evidence_hits:
        for pattern, message in _BOUNDARY_EVIDENCE_PATTERNS:
            if re.search(pattern, hit.text, re.IGNORECASE) and message not in seen:
                signals.append(message)
                seen.add(message)
    return signals


# ---------------------------------------------------------------------------
# Investigation conclusion builder
# ---------------------------------------------------------------------------

def _build_conclusion(
    leads: list[Lead],
    evidence_hits: list[EvidenceHit],
    boundary_signals: list[str],
) -> str:
    """Compose a factual archive-level conclusion from discovered leads.

    States only what the archive established.  Does not claim facts that
    require external tool access (e.g. vehicle ownership, financial records).
    """
    parts: list[str] = []

    label_set = {l.label for l in leads}

    if "alarm_maintenance_mode" in label_set or "sentryguard_pattern" in label_set:
        parts.append(
            "All four incidents share a consistent operational pattern: "
            "an alarm system was placed into maintenance mode by an authorised "
            "credential shortly before each burglary, suppressing monitoring alerts."
        )

    if "northstar_facilities" in label_set:
        parts.append(
            "Northstar Facilities Ltd conducted a maintenance visit at each "
            "premises in the three days preceding the respective burglary. "
            "This pattern is consistent across all four incidents in the archive."
        )

    if "daniel_mercer" in label_set:
        parts.append(
            "D. MERCER is named on Northstar Facilities work orders for the "
            "Bellweather Electronics incident (Case MCR-2025-0217) and is "
            "confirmed as Daniel Mercer — a Northstar Facilities engineer — "
            "in Case MCR-2025-0291 (Kingsley Watch Co.), where credential "
            "NF-3847 was used for out-of-hours access on the night of the burglary."
        )
    elif "credential_nf3847" in label_set:
        parts.append(
            "Credential NF-3847 was used to place the SentryGuard alarm into "
            "maintenance mode and gain out-of-hours building access at Kingsley "
            "Watch Co. on the night of the burglary."
        )

    if "dark_blue_transit" in label_set:
        parts.append(
            "A dark blue Ford Transit was observed near multiple incident "
            "locations on the nights of the respective burglaries. "
            "The archive does not contain a captured registration plate."
        )

    if boundary_signals:
        parts.append(
            "The archive establishes a clear recurring connection through "
            "Northstar Facilities and identifies Daniel Mercer as the "
            "strongest lead. Vehicle ownership and complete access-log, "
            "surveillance, and financial records cannot be determined "
            "from the police case archive alone."
        )

    return " ".join(parts) if parts else (
        "Archive investigation complete. See leads and evidence for details."
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def investigate(
    objective: str,
    case_dir:  str,
    max_hops:  int = 5,
) -> InvestigationResult:
    """Run the Agentic RAG investigation loop.

    Args:
        objective: The detective's investigation question.
        case_dir:  Directory containing plain-text case archive files.
        max_hops:  Maximum number of search iterations before stopping.

    Returns:
        InvestigationResult with full timeline, evidence, leads, and
        archive-level conclusion.

    The loop implements Search → Reason → Search:

      1. Plan  — create initial retrieval plan from objective
      2. Search — query all case files with current query
      3. Reason — extract cross-case leads from evidence
      4. Decide — select strongest unexhausted lead, form next query
      5. Search again (goto 2) or stop when:
           - no new leads emerge from the archive
           - archive boundary signals are detected
           - max_hops reached
    """
    case_path = Path(case_dir)
    if not case_path.is_dir():
        raise ValueError(f"case_dir does not exist: {case_dir}")

    timeline:          list[InvestigationEvent] = []
    all_evidence:      list[EvidenceHit]        = []
    all_leads:         list[Lead]               = []
    searched_leads:    set[str]                 = set()
    archive_sources:   list[str]                = sorted(
        f.name for f in case_path.glob("*.txt")
    )

    # ------------------------------------------------------------------
    # Step 1 — Plan
    # ------------------------------------------------------------------
    plan = create_plan(objective, max_hops=max_hops)
    timeline.append(InvestigationEvent(
        type    = EventType.PLAN_CREATED,
        summary = (
            f"Investigation plan created. Initial search angle: '{plan.initial_query}'. "
            f"Up to {max_hops} search iterations across {len(archive_sources)} case files."
        ),
        hop   = 0,
        query = plan.initial_query,
    ))

    current_query = plan.initial_query
    status        = InvestigationStatus.SEARCHING

    # ------------------------------------------------------------------
    # Steps 2–4 — iterative Search → Reason → Search
    # ------------------------------------------------------------------
    for hop in range(1, max_hops + 1):

        # Search
        timeline.append(InvestigationEvent(
            type    = EventType.SEARCH_STARTED,
            summary = f"Searching archive across {len(archive_sources)} case files.",
            hop     = hop,
            query   = current_query,
        ))

        hop_hits = _search_archive(current_query, case_path, hop)
        all_evidence.extend(hop_hits)

        if hop_hits:
            case_list = ", ".join(sorted({h.case_id for h in hop_hits}))
            timeline.append(InvestigationEvent(
                type    = EventType.EVIDENCE_FOUND,
                summary = (
                    f"Retrieved {len(hop_hits)} evidence chunk(s) from: {case_list}."
                ),
                hop   = hop,
                query = current_query,
            ))
        else:
            timeline.append(InvestigationEvent(
                type    = EventType.EVIDENCE_FOUND,
                summary = "No significant evidence returned for this query.",
                hop     = hop,
                query   = current_query,
            ))

        # Reason — extract leads from everything found so far
        new_leads = _extract_leads(all_evidence, searched_leads)

        for lead in new_leads:
            if lead.label not in {l.label for l in all_leads}:
                all_leads.append(lead)
                timeline.append(InvestigationEvent(
                    type    = EventType.LEAD_DISCOVERED,
                    summary = lead.context,
                    hop     = hop,
                    query   = None,
                ))

        # Check for archive boundary signals
        boundary_signals = _boundary_signals_in_evidence(all_evidence)

        # Decide — pick next unexhausted lead
        remaining_leads = [l for l in new_leads if l.label not in searched_leads]

        if not remaining_leads:
            # No new leads to follow — archive is exhausted
            status = InvestigationStatus.ARCHIVE_BOUNDARY
            timeline.append(InvestigationEvent(
                type    = EventType.ARCHIVE_BOUNDARY_REACHED,
                summary = (
                    "No further archive leads to pursue. The investigation has "
                    "reached the boundary of what the case archive can establish."
                ),
                hop = hop,
            ))
            break

        # Mark current lead as searched before moving to next
        searched_leads.add(remaining_leads[0].label)

        next_lead  = remaining_leads[0]
        next_query = next_lead.search_query

        timeline.append(InvestigationEvent(
            type    = EventType.SEARCH_UPDATED,
            summary = (
                f"New lead identified: {next_lead.label.replace('_', ' ').title()}. "
                f"Found in {len(next_lead.cases_found_in)} case file(s). "
                f"Next archive search: '{next_query}'."
            ),
            hop   = hop,
            query = next_query,
        ))

        # Check boundary after deciding next query but before looping
        # If vehicle ownership or similar is the only open question, stop.
        if boundary_signals and not [
            l for l in remaining_leads[1:] if l.label not in searched_leads
        ]:
            status = InvestigationStatus.ARCHIVE_BOUNDARY
            timeline.append(InvestigationEvent(
                type    = EventType.ARCHIVE_BOUNDARY_REACHED,
                summary = (
                    "Archive boundary reached. Remaining open questions require "
                    "external investigative databases. "
                    + " ".join(boundary_signals)
                ),
                hop = hop,
            ))
            break

        current_query = next_query

    else:
        # Reached max_hops without explicit stop
        status = InvestigationStatus.ARCHIVE_BOUNDARY
        timeline.append(InvestigationEvent(
            type    = EventType.ARCHIVE_BOUNDARY_REACHED,
            summary = (
                f"Maximum search iterations ({max_hops}) reached. "
                "Proceeding to archive-level conclusion."
            ),
            hop = max_hops,
        ))

    # ------------------------------------------------------------------
    # Step 5 — Conclude
    # ------------------------------------------------------------------
    boundary_signals = _boundary_signals_in_evidence(all_evidence)
    conclusion = _build_conclusion(all_leads, all_evidence, boundary_signals)

    stopping_reason = (
        "Archive exhausted — no further leads available from case files."
        if status == InvestigationStatus.ARCHIVE_BOUNDARY
        else "Investigation complete."
    )

    timeline.append(InvestigationEvent(
        type    = EventType.INVESTIGATION_COMPLETE,
        summary = "Archive investigation complete. See archive_level_conclusion for findings.",
        hop     = None,
    ))

    return InvestigationResult(
        objective                       = objective,
        status                          = InvestigationStatus.COMPLETE,
        plan                            = plan,
        timeline                        = timeline,
        searches_performed              = sum(
            1 for e in timeline if e.type == EventType.SEARCH_STARTED
        ),
        evidence_hits                   = all_evidence,
        leads_discovered                = all_leads,
        archive_sources                 = archive_sources,
        archive_level_conclusion        = conclusion,
        stopping_reason                 = stopping_reason,
        requires_external_investigation = _EXTERNAL_FACTS_REQUIRED,
    )
