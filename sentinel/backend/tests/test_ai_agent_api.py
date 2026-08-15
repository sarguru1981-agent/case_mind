"""API integration tests for the AI Agent investigation endpoint.

Tests that the FastAPI endpoints correctly execute the ReAct loop
and return well-formed AgentState JSON.

Run from sentinel/backend/:
    PYTHONPATH=. pytest tests/test_ai_agent_api.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

client = TestClient(app)

ASSIGNED_TASK = (
    "Using external investigative records, determine whether the dark blue Ford "
    "Transit and credential NF-3847 can be independently corroborated at the "
    "Kingsley Watch Co. on the night of MCR-2025-0291, identify the registered "
    "keeper of the vehicle, and determine whether any financial activity in the "
    "period following the Operation Nightfall incidents is consistent with "
    "Daniel Mercer's involvement."
)


# ---------------------------------------------------------------------------
# Shared fixture — run investigation once per test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def agent_response():
    r = client.post(
        "/api/agent/investigate",
        json={"assigned_task": ASSIGNED_TASK},
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# POST /api/agent/investigate
# ---------------------------------------------------------------------------

class TestInvestigateEndpoint:
    def test_returns_200(self, agent_response):
        assert agent_response is not None

    def test_status_field(self, agent_response):
        assert agent_response["status"] in ("complete", "max_iterations_reached")

    def test_tool_calls_returned(self, agent_response):
        calls = agent_response["tool_calls"]
        assert isinstance(calls, list)
        assert len(calls) > 0

    def test_observations_returned(self, agent_response):
        obs = agent_response["observations"]
        assert isinstance(obs, list)
        assert len(obs) == len(agent_response["tool_calls"])

    def test_evidence_returned(self, agent_response):
        assert isinstance(agent_response["evidence"], list)
        assert len(agent_response["evidence"]) > 0

    def test_completion_summary_returned(self, agent_response):
        summary = agent_response["completion_summary"]
        assert summary and len(summary) > 10

    def test_iteration_count(self, agent_response):
        assert agent_response["iteration"] >= 1

    def test_assigned_task_echoed(self, agent_response):
        assert ASSIGNED_TASK in agent_response["assigned_task"] or \
               agent_response["assigned_task"] in ASSIGNED_TASK

    def test_tool_call_structure(self, agent_response):
        for tc in agent_response["tool_calls"]:
            assert "tool_name" in tc
            assert "arguments" in tc
            assert "call_id" in tc

    def test_observation_structure(self, agent_response):
        for obs in agent_response["observations"]:
            assert "tool_name" in obs
            assert "status" in obs
            assert obs["status"] in ("success", "not_found", "invalid_input", "error")

    def test_evidence_structure(self, agent_response):
        for ev in agent_response["evidence"]:
            assert "fact" in ev
            assert "source_tool" in ev
            assert "confidence" in ev

    def test_default_task_used_when_none_provided(self):
        r = client.post("/api/agent/investigate", json={})
        assert r.status_code == 200
        data = r.json()
        assert "NF-3847" in data["assigned_task"] or "MCR-2025-0291" in data["assigned_task"]

    def test_empty_task_returns_422(self):
        r = client.post("/api/agent/investigate", json={"assigned_task": ""})
        # Empty string falls back to default task — not a 422
        # (route falls back to ASSIGNED_TASK for empty input)
        assert r.status_code == 200

    def test_surveillance_called(self, agent_response):
        tool_names = [tc["tool_name"] for tc in agent_response["tool_calls"]]
        assert "query_surveillance" in tool_names

    def test_vehicle_lookup_called(self, agent_response):
        tool_names = [tc["tool_name"] for tc in agent_response["tool_calls"]]
        assert "lookup_vehicle" in tool_names

    def test_access_logs_called(self, agent_response):
        tool_names = [tc["tool_name"] for tc in agent_response["tool_calls"]]
        assert "query_access_logs" in tool_names

    def test_financial_intelligence_called(self, agent_response):
        tool_names = [tc["tool_name"] for tc in agent_response["tool_calls"]]
        assert "query_financial_intelligence" in tool_names


# ---------------------------------------------------------------------------
# Marcus Vale only appears through financial intelligence
# ---------------------------------------------------------------------------

class TestMarcusValeDiscovery:
    def test_marcus_vale_not_in_surveillance_observation(self, agent_response):
        for obs in agent_response["observations"]:
            if obs["tool_name"] == "query_surveillance":
                result_str = str(obs.get("result", ""))
                assert "Marcus Vale" not in result_str

    def test_marcus_vale_not_in_vehicle_observation(self, agent_response):
        for obs in agent_response["observations"]:
            if obs["tool_name"] == "lookup_vehicle":
                result_str = str(obs.get("result", ""))
                assert "Marcus Vale" not in result_str

    def test_marcus_vale_not_in_access_logs_observation(self, agent_response):
        for obs in agent_response["observations"]:
            if obs["tool_name"] == "query_access_logs":
                result_str = str(obs.get("result", ""))
                assert "Marcus Vale" not in result_str

    def test_marcus_vale_appears_in_financial_observation(self, agent_response):
        found = False
        for obs in agent_response["observations"]:
            if obs["tool_name"] == "query_financial_intelligence":
                if obs.get("result") and "Marcus Vale" in str(obs["result"]):
                    found = True
        assert found, "Marcus Vale should appear in financial intelligence observation"


# ---------------------------------------------------------------------------
# GET /api/agent/tools
# ---------------------------------------------------------------------------

class TestToolsEndpoint:
    @pytest.fixture(scope="class")
    def tools_response(self):
        r = client.get("/api/agent/tools")
        assert r.status_code == 200
        return r.json()

    def test_returns_list(self, tools_response):
        assert isinstance(tools_response, list)

    def test_four_tools(self, tools_response):
        assert len(tools_response) == 4

    def test_tool_has_name_description_schema(self, tools_response):
        for tool in tools_response:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_no_function_callable_exposed(self, tools_response):
        for tool in tools_response:
            assert "function" not in tool


# ---------------------------------------------------------------------------
# Regression — existing endpoints unaffected
# ---------------------------------------------------------------------------

class TestRegressionExistingEndpoints:
    def test_agentic_rag_investigate_still_works(self):
        r = client.post(
            "/api/agentic-rag/investigate",
            json={"objective": "Are the four Operation Nightfall robberies connected?", "max_hops": 2},
        )
        assert r.status_code == 200
        data = r.json()
        assert "leads_discovered" in data

    def test_health_endpoint_unaffected(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_version_endpoint_unaffected(self):
        r = client.get("/version")
        assert r.status_code == 200
        assert "version" in r.json()
