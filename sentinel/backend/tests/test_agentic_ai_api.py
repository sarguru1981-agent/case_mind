"""API integration tests for the Agentic AI mission endpoint.

Tests that the FastAPI endpoint correctly wraps run_mission() and returns
well-formed MissionState JSON. Uses short max_cycles to keep tests fast.

Run from sentinel/backend/:
    PYTHONPATH=. pytest tests/test_agentic_ai_api.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

client = TestClient(app)

BROAD_MISSION = (
    "Investigate the Operation Nightfall robbery series, determine whether the"
    " four incidents are connected, identify the strongest persons of interest,"
    " evaluate significant alternative leads, and produce an evidence-backed"
    " investigation assessment for human review."
)


# ---------------------------------------------------------------------------
# Fixture — run mission once (5 cycles), share across all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mission_response():
    r = client.post(
        "/api/agentic-ai/mission",
        json={"mission": BROAD_MISSION, "max_cycles": 5},
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# HTTP contract
# ---------------------------------------------------------------------------

def test_endpoint_returns_200():
    r = client.post(
        "/api/agentic-ai/mission",
        json={"mission": BROAD_MISSION, "max_cycles": 3},
    )
    assert r.status_code == 200


def test_short_mission_rejected():
    r = client.post("/api/agentic-ai/mission", json={"mission": "short"})
    assert r.status_code == 422


def test_max_cycles_out_of_range_rejected():
    r = client.post(
        "/api/agentic-ai/mission",
        json={"mission": BROAD_MISSION, "max_cycles": 99},
    )
    assert r.status_code == 422


def test_default_mission_accepted():
    r = client.post("/api/agentic-ai/mission", json={})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

def test_response_top_level_fields(mission_response):
    required = {
        "mission_id", "mission", "status", "cycle_count",
        "tasks", "priority_queue", "known_findings",
        "workflow_events",
    }
    for field in required:
        assert field in mission_response, f"Missing field: {field}"


def test_mission_echoed(mission_response):
    assert mission_response["mission"] == BROAD_MISSION


def test_mission_id_nonempty(mission_response):
    assert mission_response["mission_id"]


def test_cycle_count_positive(mission_response):
    assert mission_response["cycle_count"] >= 1


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def test_tasks_created(mission_response):
    assert len(mission_response["tasks"]) >= 2


def test_t001_present(mission_response):
    ids = {t["task_id"] for t in mission_response["tasks"]}
    assert "T-001" in ids


def test_task_fields(mission_response):
    required = {"task_id", "title", "objective", "task_type", "priority", "status",
                "assigned_capability", "created_from"}
    for task in mission_response["tasks"]:
        for field in required:
            assert field in task, f"Missing task field: {field}"


def test_t001_completed(mission_response):
    t001 = next(t for t in mission_response["tasks"] if t["task_id"] == "T-001")
    assert t001["status"] == "COMPLETED"


def test_no_forward_knowledge_in_initial_tasks(mission_response):
    forbidden = ["MBK-4172", "Marcus Vale", "NF-3847"]
    initial = [t for t in mission_response["tasks"] if t["created_from"] == "mission_decomposition"]
    for task in initial:
        for word in forbidden:
            assert word not in task["objective"], (
                f"Forward knowledge '{word}' in initial task {task['task_id']}"
            )


# ---------------------------------------------------------------------------
# Status and human authority boundary
# ---------------------------------------------------------------------------

def test_status_not_case_solved(mission_response):
    status = mission_response["status"]
    assert status not in ("CASE_SOLVED", "ARRESTED", "GUILTY")


def test_status_is_valid(mission_response):
    valid = {
        "INITIALIZING", "ACTIVE", "READY_FOR_HUMAN_REVIEW",
        "BLOCKED", "MAX_CYCLES_REACHED", "FAILED",
    }
    assert mission_response["status"] in valid, f"Unexpected status: {mission_response['status']}"


def test_final_assessment_no_guilt_language(mission_response):
    assessment = mission_response.get("final_assessment") or ""
    forbidden = ["is guilty", "arrest", "warrant for arrest", "convicted"]
    for phrase in forbidden:
        assert phrase.lower() not in assessment.lower(), (
            f"Forbidden phrase '{phrase}' in final_assessment"
        )


# ---------------------------------------------------------------------------
# Workflow events
# ---------------------------------------------------------------------------

def test_workflow_events_present(mission_response):
    assert len(mission_response["workflow_events"]) >= 2


def test_mission_received_event(mission_response):
    types = [e["event_type"] for e in mission_response["workflow_events"]]
    assert "MISSION_RECEIVED" in types


def test_events_have_timestamps(mission_response):
    for ev in mission_response["workflow_events"]:
        assert ev.get("timestamp"), f"Missing timestamp on event: {ev}"


# ---------------------------------------------------------------------------
# Health endpoint unaffected
# ---------------------------------------------------------------------------

def test_health_endpoint_unaffected():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Corrected autonomy — initial decomposition is minimal (T-001 + T-002 only)
# ---------------------------------------------------------------------------

def test_initial_decomposition_is_minimal(mission_response):
    """Decomposer must only create T-001 + T-002; external tasks created by Rule 0."""
    initial = [t for t in mission_response["tasks"] if t["created_from"] == "mission_decomposition"]
    ids = {t["task_id"] for t in initial}
    assert ids == {"T-001", "T-002"}, (
        f"Initial decomposition should be T-001 + T-002 only, got: {ids}"
    )


def test_t002_initially_blocked_only_on_t001(mission_response):
    """At decomposition T-002 depends only on T-001 — external deps are added by Rule 0."""
    # The initial dependencies recorded in priority_history must mention T-001 only
    t002 = next(t for t in mission_response["tasks"] if t["task_id"] == "T-002")
    history_text = " ".join(t002.get("priority_history", []))
    assert "T-003" not in history_text.split("T-001")[0], (
        "T-002 initial priority history must not reference T-003 before Rule 0 runs"
    )


def test_external_tasks_created_from_t001(mission_response):
    """T-003, T-004, T-005 must be created dynamically from T-001's archive result."""
    dynamic = [
        t for t in mission_response["tasks"]
        if t.get("created_from") == "T-001"
    ]
    types = {t["task_type"] for t in dynamic}
    assert "EXTERNAL_INVESTIGATION" in types, (
        "At least one EXTERNAL_INVESTIGATION task must be created from T-001's findings"
    )


def test_surveillance_task_embeds_case_ids(mission_response):
    """The ANPR surveillance task must contain MCR-XXXX-XXXX case IDs in its objective."""
    import re
    surv = next(
        (t for t in mission_response["tasks"]
         if t.get("created_from") == "T-001"
         and "surveillance" in t["title"].lower()),
        None,
    )
    assert surv is not None, "Surveillance task created from T-001 not found"
    case_ids = re.findall(r"MCR-\d{4}-\d{4}", surv["objective"])
    assert len(case_ids) >= 2, (
        f"Surveillance objective must embed case IDs for AI Agent to query; found: {case_ids}"
    )


def test_access_logs_task_embeds_credential(mission_response):
    """The access logs task must contain an NF-XXXX credential in its objective."""
    import re
    acc = next(
        (t for t in mission_response["tasks"]
         if t.get("created_from") == "T-001"
         and "access" in t["title"].lower()),
        None,
    )
    assert acc is not None, "Access logs task created from T-001 not found"
    creds = re.findall(r"\bNF-\d{4}\b", acc["objective"])
    assert len(creds) >= 1, (
        f"Access logs objective must embed a credential; found: {creds}"
    )


def test_task_created_from_finding_events_present(mission_response):
    """TASK_CREATED_FROM_FINDING events prove dynamic task creation fires at runtime."""
    event_types = [e["event_type"] for e in mission_response["workflow_events"]]
    count = event_types.count("TASK_CREATED_FROM_FINDING")
    assert count >= 3, (
        f"Expected >= 3 TASK_CREATED_FROM_FINDING events (T-003, T-004, T-005 minimum),"
        f" got {count}"
    )


# ---------------------------------------------------------------------------
# Full autonomy run (15 cycles) — all 10 concepts must be present
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def full_mission_response():
    r = client.post(
        "/api/agentic-ai/mission",
        json={"mission": BROAD_MISSION, "max_cycles": 15},
    )
    assert r.status_code == 200
    return r.json()


def test_full_run_status(full_mission_response):
    assert full_mission_response["status"] == "READY_FOR_HUMAN_REVIEW"


def test_full_run_vehicle_lookup_mbk4172_created(full_mission_response):
    """Rule 1 must create MBK-4172 vehicle lookup task after surveillance runs."""
    titles = [t["title"] for t in full_mission_response["tasks"]]
    assert any("MBK-4172" in title for title in titles), (
        "Vehicle lookup for MBK-4172 not found — Rule 1 did not fire"
    )


def test_full_run_financial_task_elevated_to_critical(full_mission_response):
    """Rule 2 must elevate Daniel Mercer's financial task from HIGH to CRITICAL."""
    fin = next(
        (t for t in full_mission_response["tasks"]
         if "Daniel Mercer" in t["title"] and t["task_type"] == "EXTERNAL_INVESTIGATION"),
        None,
    )
    assert fin is not None, "Financial Intelligence — Daniel Mercer task not found"
    assert fin["priority"] == "CRITICAL", (
        f"Financial task should be CRITICAL after Rule 2, got: {fin['priority']}"
    )


def test_full_run_marcus_vale_task_created(full_mission_response):
    """Rule 3 must create a Lead Validation task for Marcus Vale."""
    titles = [t["title"] for t in full_mission_response["tasks"]]
    assert any("Marcus Vale" in title for title in titles), (
        "Marcus Vale lead validation task not found — Rule 3 did not fire"
    )


def test_full_run_rgw7734_deprioritized(full_mission_response):
    """Rule 5 must create a RED_HERRING_VALIDATION task for RGW-7734 and deprioritise it."""
    rh = next(
        (t for t in full_mission_response["tasks"]
         if t["task_type"] == "RED_HERRING_VALIDATION" and "RGW-7734" in t["title"]),
        None,
    )
    assert rh is not None, "Red Herring task for RGW-7734 not found — Rule 5 did not fire"
    assert rh["status"] == "DEPRIORITIZED", (
        f"RGW-7734 red herring task should be DEPRIORITIZED, got: {rh['status']}"
    )


def test_full_run_synthesis_runs_last(full_mission_response):
    """T-002 (Synthesis) must start after all investigative tasks have completed."""
    events = full_mission_response["workflow_events"]
    t002_start_idx = None
    for i, e in enumerate(events):
        if e["event_type"] == "TASK_STARTED" and e.get("task_id") == "T-002":
            t002_start_idx = i  # keep the LAST start index
    assert t002_start_idx is not None, "T-002 never started"
    investigative_types = {"ARCHIVE_INVESTIGATION", "EXTERNAL_INVESTIGATION", "LEAD_VALIDATION"}
    started_after = [
        e for e in events[t002_start_idx + 1:]
        if e["event_type"] == "TASK_COMPLETED"
        and e.get("task_id", "T-002") != "T-002"
    ]
    # No investigative tasks should complete AFTER synthesis starts (on its final run)
    assert len(started_after) == 0, (
        f"Investigative tasks completed after T-002 final start: {started_after}"
    )


def test_full_run_task_reprioritized_events(full_mission_response):
    """TASK_REPRIORITIZED events must appear — proving live priority changes."""
    event_types = [e["event_type"] for e in full_mission_response["workflow_events"]]
    assert "TASK_REPRIORITIZED" in event_types


def test_full_run_task_deprioritized_events(full_mission_response):
    """TASK_DEPRIORITIZED events must appear — proving deprioritisation fires."""
    event_types = [e["event_type"] for e in full_mission_response["workflow_events"]]
    assert "TASK_DEPRIORITIZED" in event_types


def test_full_run_no_forward_knowledge_in_initial_tasks(full_mission_response):
    """Initial tasks must not mention specific entities discovered at runtime."""
    forbidden = ["MBK-4172", "Marcus Vale", "NF-3847", "Daniel Mercer", "RGW-7734"]
    initial = [t for t in full_mission_response["tasks"]
               if t["created_from"] == "mission_decomposition"]
    for task in initial:
        for word in forbidden:
            assert word not in task["objective"], (
                f"Forward knowledge '{word}' in initial task {task['task_id']}"
            )
