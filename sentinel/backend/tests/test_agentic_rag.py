"""Validation tests for the Agentic RAG investigation loop.

These tests validate the 12 requirements from the Build 3 specification
and confirm that the existing Project 002 RAG capability is unaffected.

Run from sentinel/backend/:
    PYTHONPATH=. pytest tests/test_agentic_rag.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure backend package is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CASE_DIR   = Path(__file__).resolve().parent.parent.parent / "data" / "case-files" / "serial-robbery"
GT_FILE    = Path(__file__).resolve().parent.parent.parent / "data" / "operation-nightfall-ground-truth.json"
TOOL_DIR   = Path(__file__).resolve().parent.parent.parent / "data" / "tool-data"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def result():
    """Run the full investigation once; share across all tests."""
    from services.agentic_rag import investigate
    return investigate(
        objective = (
            "Are the four Operation Nightfall robberies connected? "
            "Identify the strongest shared leads using only the police case archive."
        ),
        case_dir  = str(CASE_DIR),
        max_hops  = 5,
    )


@pytest.fixture(scope="module")
def ground_truth():
    with open(GT_FILE) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Test 1 — Multi-file retrieval covers all four case files
# ---------------------------------------------------------------------------

def test_all_four_case_files_searched(result):
    """Multi-file retrieval must search all four Operation Nightfall case files."""
    source_files = {hit.source_file for hit in result.evidence_hits}
    assert "robbery-001-hawthorne-jewellers.txt" in source_files
    assert "robbery-002-millbrook-gallery.txt"   in source_files
    assert "robbery-003-bellweather-electronics.txt" in source_files
    assert "robbery-004-kingsley-watches.txt"    in source_files


# ---------------------------------------------------------------------------
# Test 2 — Source attribution preserved
# ---------------------------------------------------------------------------

def test_source_attribution_preserved(result):
    """Every evidence hit must carry case_id and source_file."""
    for hit in result.evidence_hits:
        assert hit.case_id,     f"Missing case_id on hit: {hit.text[:60]}"
        assert hit.source_file, f"Missing source_file on hit: {hit.text[:60]}"


# ---------------------------------------------------------------------------
# Test 3 — Northstar Facilities discovered across multiple cases
# ---------------------------------------------------------------------------

def test_northstar_discovered_across_cases(result):
    """Northstar Facilities must surface as a cross-case lead (2+ case files)."""
    northstar_lead = next(
        (l for l in result.leads_discovered if l.label == "northstar_facilities"),
        None,
    )
    assert northstar_lead is not None, "northstar_facilities lead not discovered"
    assert len(northstar_lead.cases_found_in) >= 2, (
        f"Northstar found in only {len(northstar_lead.cases_found_in)} case(s)"
    )


# ---------------------------------------------------------------------------
# Test 4 — Daniel Mercer discovered from archive
# ---------------------------------------------------------------------------

def test_daniel_mercer_discovered(result):
    """Daniel Mercer / D. MERCER must be surfaced as a lead from the archive."""
    mercer_lead = next(
        (l for l in result.leads_discovered if l.label == "daniel_mercer"),
        None,
    )
    assert mercer_lead is not None, "daniel_mercer lead not discovered from archive"


# ---------------------------------------------------------------------------
# Test 5 — Dark blue Ford Transit discovered
# ---------------------------------------------------------------------------

def test_dark_blue_transit_discovered(result):
    """A dark blue Ford Transit / van must appear as a lead."""
    transit_lead = next(
        (l for l in result.leads_discovered if l.label == "dark_blue_transit"),
        None,
    )
    assert transit_lead is not None, "dark_blue_transit lead not discovered"


# ---------------------------------------------------------------------------
# Test 6 — Tool-data directory not accessed
# ---------------------------------------------------------------------------

def test_tool_data_not_accessed(result):
    """No evidence hit may originate from the tool-data directory."""
    forbidden = str(TOOL_DIR)
    for hit in result.evidence_hits:
        assert forbidden not in hit.source_file, (
            f"Evidence hit sourced from tool-data: {hit.source_file}"
        )


# ---------------------------------------------------------------------------
# Test 7 — Marcus Vale NOT discovered from archive
# ---------------------------------------------------------------------------

def test_marcus_vale_not_in_archive(result):
    """Marcus Vale must not appear in any archive evidence hit or lead."""
    vale_in_evidence = any(
        "Marcus Vale" in hit.text or "marcus vale" in hit.text.lower()
        for hit in result.evidence_hits
    )
    vale_in_leads = any(
        "marcus_vale" in lead.label or "Marcus Vale" in lead.context
        for lead in result.leads_discovered
    )
    assert not vale_in_evidence, "Marcus Vale found in archive evidence — boundary violation"
    assert not vale_in_leads,    "Marcus Vale found in leads — boundary violation"


# ---------------------------------------------------------------------------
# Test 8 — MBK-4172 ownership NOT discovered from archive
# ---------------------------------------------------------------------------

def test_mbk4172_ownership_not_in_archive(result):
    """MBK-4172 registration ownership must not appear in archive evidence."""
    for hit in result.evidence_hits:
        assert "MBK-4172" not in hit.text, (
            "MBK-4172 found in archive evidence — this is a tool-only fact"
        )


# ---------------------------------------------------------------------------
# Test 9 — Investigation reaches ARCHIVE_BOUNDARY_REACHED
# ---------------------------------------------------------------------------

def test_archive_boundary_reached(result):
    """The timeline must contain an ARCHIVE_BOUNDARY_REACHED event."""
    from services.agentic_rag import EventType
    boundary_events = [
        e for e in result.timeline
        if e.type == EventType.ARCHIVE_BOUNDARY_REACHED
    ]
    assert boundary_events, "ARCHIVE_BOUNDARY_REACHED event not emitted"


# ---------------------------------------------------------------------------
# Test 10 — Multiple search hops performed
# ---------------------------------------------------------------------------

def test_multiple_search_hops(result):
    """Agentic RAG must perform more than one search iteration."""
    assert result.searches_performed >= 2, (
        f"Only {result.searches_performed} search(es) performed — "
        "Agentic RAG must iterate"
    )


# ---------------------------------------------------------------------------
# Test 11 — Next-search decisions change based on evidence
# ---------------------------------------------------------------------------

def test_search_queries_evolve(result):
    """Each SEARCH_UPDATED event must produce a different query from the previous."""
    from services.agentic_rag import EventType
    search_queries = [
        e.query for e in result.timeline
        if e.type == EventType.SEARCH_STARTED and e.query
    ]
    assert len(search_queries) >= 2, "Need at least 2 search queries to verify evolution"
    # Consecutive queries must differ
    for i in range(1, len(search_queries)):
        assert search_queries[i] != search_queries[i - 1], (
            f"Query at hop {i+1} is identical to hop {i} — dynamic retrieval not working"
        )


# ---------------------------------------------------------------------------
# Test 12 — Existing Project 002 RAG unaffected
# ---------------------------------------------------------------------------

def test_existing_rag_imports_unchanged():
    """Project 002 RAG must import and return results without modification."""
    from services.rag.retrieval import retrieve_evidence
    arson_file = (
        Path(__file__).resolve().parent.parent.parent
        / "data" / "case-files" / "millbrook_arson_2019.txt"
    )
    pages, confidence = retrieve_evidence("accelerant used in the fire", str(arson_file))
    assert pages,      "retrieve_evidence returned no pages for arson file"
    assert confidence >= 0.0, "retrieve_evidence returned negative confidence"


# ---------------------------------------------------------------------------
# Bonus — Existing RAG Hallucination modules import
# ---------------------------------------------------------------------------

def test_rag_hallucination_imports():
    """Trust Layer modules must remain importable after Agentic RAG addition."""
    from services.rag_hallucination.guardrail   import check_injection
    from services.rag_hallucination.contradiction import ContradictionDetector
    from services.rag_hallucination.fact_check  import extract_claims
    from services.rag_hallucination.trust_score import build_trusted_response
    assert callable(check_injection)


# ---------------------------------------------------------------------------
# Bonus — Ground truth validation questions
# ---------------------------------------------------------------------------

def test_ground_truth_vq01_northstar(result, ground_truth):
    """VQ-01: Northstar Facilities maintenance visit pattern must be discoverable."""
    northstar_lead = next(
        (l for l in result.leads_discovered if l.label == "northstar_facilities"),
        None,
    )
    assert northstar_lead is not None


def test_ground_truth_vq05_alarm_vendor_difference(result):
    """VQ-05: Safeguard Pro Series (different vendor) must be retrievable from archive."""
    from services.rag.retrieval import retrieve_evidence
    case_003 = str(CASE_DIR / "robbery-003-bellweather-electronics.txt")
    pages, _ = retrieve_evidence("Safeguard Pro Series alarm vendor", case_003)
    vendor_hit = any("Safeguard" in p or "different vendor" in p for p in pages)
    assert vendor_hit, "Safeguard Pro Series vendor difference not retrievable from archive"
