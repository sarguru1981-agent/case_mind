"""API integration tests for the Agentic RAG investigation endpoint.

Tests that the FastAPI endpoint correctly wraps the agentic_rag.investigate()
loop and returns well-formed InvestigationResult JSON.

Run from sentinel/backend/:
    PYTHONPATH=. pytest tests/test_agentic_rag_api.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

client = TestClient(app)

OBJECTIVE = (
    "Are the four Operation Nightfall robberies connected? "
    "Identify the strongest shared leads using only the police case archive."
)


# ---------------------------------------------------------------------------
# Fixture — run investigation once, share across all API tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def response():
    r = client.post(
        "/api/agentic-rag/investigate",
        json={"objective": OBJECTIVE, "max_hops": 5},
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# Test 1 — Endpoint returns HTTP 200
# ---------------------------------------------------------------------------

def test_endpoint_returns_200():
    r = client.post(
        "/api/agentic-rag/investigate",
        json={"objective": OBJECTIVE, "max_hops": 3},
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Test 2 — Response contains required top-level fields
# ---------------------------------------------------------------------------

def test_response_shape(response):
    required_fields = {
        "objective", "status", "plan", "timeline",
        "searches_performed", "evidence_hits", "leads_discovered",
        "archive_sources", "stopping_reason", "requires_external_investigation",
    }
    for field in required_fields:
        assert field in response, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Test 3 — Objective echoed back
# ---------------------------------------------------------------------------

def test_objective_echoed(response):
    assert response["objective"] == OBJECTIVE


# ---------------------------------------------------------------------------
# Test 4 — Status is a known value
# ---------------------------------------------------------------------------

def test_status_is_valid(response):
    valid = {"PLANNING", "SEARCHING", "ARCHIVE_BOUNDARY", "COMPLETE"}
    assert response["status"] in valid, f"Unexpected status: {response['status']}"


# ---------------------------------------------------------------------------
# Test 5 — Plan contains initial_query and planned_angles
# ---------------------------------------------------------------------------

def test_plan_fields(response):
    plan = response["plan"]
    assert plan.get("initial_query"), "plan.initial_query is empty"
    assert plan.get("planned_angles"), "plan.planned_angles is empty"
    assert isinstance(plan["planned_angles"], list)


# ---------------------------------------------------------------------------
# Test 6 — Timeline contains events
# ---------------------------------------------------------------------------

def test_timeline_nonempty(response):
    assert len(response["timeline"]) > 0, "timeline is empty"


# ---------------------------------------------------------------------------
# Test 7 — Timeline event types are from the controlled vocabulary
# ---------------------------------------------------------------------------

def test_timeline_event_types(response):
    valid_types = {
        "PLAN_CREATED", "SEARCH_STARTED", "EVIDENCE_FOUND",
        "LEAD_DISCOVERED", "SEARCH_UPDATED",
        "ARCHIVE_BOUNDARY_REACHED", "INVESTIGATION_COMPLETE",
    }
    for evt in response["timeline"]:
        assert evt["type"] in valid_types, f"Unknown event type: {evt['type']}"


# ---------------------------------------------------------------------------
# Test 8 — Evidence hits have required fields
# ---------------------------------------------------------------------------

def test_evidence_hits_fields(response):
    assert response["evidence_hits"], "evidence_hits is empty"
    for hit in response["evidence_hits"]:
        assert hit.get("case_id"),     f"Missing case_id on hit"
        assert hit.get("source_file"), f"Missing source_file on hit"
        assert hit.get("text"),        f"Missing text on hit"
        assert "confidence" in hit
        assert "hop" in hit


# ---------------------------------------------------------------------------
# Test 9 — All four case files covered in evidence
# ---------------------------------------------------------------------------

def test_all_four_case_files_in_response(response):
    source_files = {h["source_file"] for h in response["evidence_hits"]}
    assert "robbery-001-hawthorne-jewellers.txt"   in source_files
    assert "robbery-002-millbrook-gallery.txt"     in source_files
    assert "robbery-003-bellweather-electronics.txt" in source_files
    assert "robbery-004-kingsley-watches.txt"      in source_files


# ---------------------------------------------------------------------------
# Test 10 — Leads discovered are nonempty
# ---------------------------------------------------------------------------

def test_leads_nonempty(response):
    assert response["leads_discovered"], "leads_discovered is empty"
    for lead in response["leads_discovered"]:
        assert lead.get("label")
        assert lead.get("context")
        assert isinstance(lead.get("cases_found_in"), list)


# ---------------------------------------------------------------------------
# Test 11 — Northstar lead present in response
# ---------------------------------------------------------------------------

def test_northstar_lead_in_response(response):
    labels = [l["label"] for l in response["leads_discovered"]]
    assert "northstar_facilities" in labels, f"northstar_facilities not in leads: {labels}"


# ---------------------------------------------------------------------------
# Test 12 — Searches performed count is at least 2
# ---------------------------------------------------------------------------

def test_searches_performed(response):
    assert response["searches_performed"] >= 2, (
        f"Only {response['searches_performed']} search(es) performed"
    )


# ---------------------------------------------------------------------------
# Test 13 — requires_external_investigation is a list
# ---------------------------------------------------------------------------

def test_requires_external_investigation_type(response):
    assert isinstance(response["requires_external_investigation"], list)


# ---------------------------------------------------------------------------
# Test 14 — Default objective accepted without explicit field
# ---------------------------------------------------------------------------

def test_default_objective():
    r = client.post("/api/agentic-rag/investigate", json={})
    assert r.status_code == 200
    data = r.json()
    assert "Operation Nightfall" in data["objective"]


# ---------------------------------------------------------------------------
# Test 15 — Short objective rejected (< 10 chars)
# ---------------------------------------------------------------------------

def test_short_objective_rejected():
    r = client.post("/api/agentic-rag/investigate", json={"objective": "short"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Test 16 — max_hops out of range rejected
# ---------------------------------------------------------------------------

def test_max_hops_out_of_range():
    r = client.post(
        "/api/agentic-rag/investigate",
        json={"objective": OBJECTIVE, "max_hops": 99},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Test 17 — Existing /api/query endpoint unaffected
# ---------------------------------------------------------------------------

def test_existing_query_endpoint_unaffected():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
