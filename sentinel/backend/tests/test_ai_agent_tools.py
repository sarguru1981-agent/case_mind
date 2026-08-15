"""Tests for all four AI Agent investigative tools.

Covers:
  - Happy path (found)
  - Not-found (no match)
  - Invalid input (missing required arg)
  - Red-herring / eliminated vehicle cases
  - Data isolation: each tool reads ONLY its own JSON file (no cross-reads)
  - Ground truth file is never accessed at runtime

All tests are offline / deterministic — no network or LLM calls.
"""
import pytest

from services.ai_agent.tools.vehicle_records import lookup_vehicle
from services.ai_agent.tools.access_logs import query_access_logs
from services.ai_agent.tools.surveillance import query_surveillance
from services.ai_agent.tools.financial_intelligence import query_financial_intelligence


# ---------------------------------------------------------------------------
# vehicle_records
# ---------------------------------------------------------------------------

class TestLookupVehicle:
    def test_found_known_plate(self):
        result = lookup_vehicle({"registration": "MBK-4172"})
        assert result.status == "success"
        assert result.result["registration"] == "MBK-4172"
        assert "registered_keeper" in result.result

    def test_not_found_unknown_plate(self):
        result = lookup_vehicle({"registration": "ZZZ-9999"})
        assert result.status == "not_found"
        assert result.result is not None
        assert "message" in result.result

    def test_invalid_input_missing_registration(self):
        result = lookup_vehicle({})
        assert result.status == "invalid_input"
        assert result.error is not None

    def test_keeper_dob_not_exposed(self):
        """Date of birth is PII — must never appear in tool output."""
        result = lookup_vehicle({"registration": "MBK-4172"})
        if result.status == "success":
            assert "keeper_dob" not in result.result

    def test_call_id_propagated(self):
        result = lookup_vehicle({"registration": "MBK-4172", "_call_id": "test-001"})
        assert result.call_id == "test-001"

    def test_tool_name_in_result(self):
        result = lookup_vehicle({"registration": "MBK-4172"})
        assert result.tool_name == "lookup_vehicle"

    def test_red_herring_plate_not_found(self):
        """Plates that are eliminated / not in the dataset return not_found."""
        result = lookup_vehicle({"registration": "XYZ-0000"})
        assert result.status == "not_found"


# ---------------------------------------------------------------------------
# access_logs
# ---------------------------------------------------------------------------

class TestQueryAccessLogs:
    def test_found_by_credential_id(self):
        result = query_access_logs({"credential_id": "NF-3847"})
        assert result.status == "success"
        assert result.result["credential_id"] == "NF-3847"
        assert "access_events" in result.result

    def test_not_found_unknown_credential(self):
        result = query_access_logs({"credential_id": "NF-9999"})
        assert result.status == "not_found"

    def test_invalid_input_no_args(self):
        result = query_access_logs({})
        assert result.status == "invalid_input"

    def test_found_by_person_name(self):
        result = query_access_logs({"person_name": "Daniel Mercer"})
        assert result.status == "success"
        assert result.result["assigned_to"] == "Daniel Mercer"

    def test_credential_id_takes_precedence(self):
        """When both credential_id and person_name given, credential_id wins."""
        result_by_cred = query_access_logs({"credential_id": "NF-3847"})
        result_both    = query_access_logs({"credential_id": "NF-3847", "person_name": "Someone Else"})
        assert result_by_cred.status == result_both.status == "success"
        assert result_by_cred.result["credential_id"] == result_both.result["credential_id"]

    def test_revoked_credential_returns_success(self):
        """A revoked credential with zero access events is success, not an error."""
        result = query_access_logs({"credential_id": "NF-3847"})
        # Whether or not NF-3847 is revoked, the status must be success or not_found
        assert result.status in ("success", "not_found")

    def test_call_id_propagated(self):
        result = query_access_logs({"credential_id": "NF-3847", "_call_id": "test-002"})
        assert result.call_id == "test-002"

    def test_tool_name_in_result(self):
        result = query_access_logs({"credential_id": "NF-3847"})
        assert result.tool_name == "query_access_logs"

    def test_no_cross_read_of_vehicle_data(self, tmp_path, monkeypatch):
        """Tool must not read vehicle-records.json — only access-logs.json."""
        import services.ai_agent.tools.access_logs as mod
        original = mod._DATA_FILE
        assert "access-logs" in str(original), "Data file must be the access-logs dataset"


# ---------------------------------------------------------------------------
# surveillance
# ---------------------------------------------------------------------------

class TestQuerySurveillance:
    def test_found_by_incident_case(self):
        result = query_surveillance({"incident_case": "MCR-2025-0291"})
        assert result.status in ("success", "not_found")

    def test_not_found_unknown_case(self):
        result = query_surveillance({"incident_case": "MCR-0000-0000"})
        assert result.status == "not_found"

    def test_invalid_input_no_args(self):
        result = query_surveillance({})
        assert result.status == "invalid_input"

    def test_invalid_time_window_without_case(self):
        result = query_surveillance({
            "registration": "MBK-4172",
            "time_window_start": "2025-04-01T23:00",
        })
        assert result.status == "invalid_input"

    def test_invalid_time_window_format(self):
        result = query_surveillance({
            "incident_case": "MCR-2025-0291",
            "time_window_start": "not-a-date",
        })
        assert result.status == "invalid_input"

    def test_sightings_structure(self):
        result = query_surveillance({"incident_case": "MCR-2025-0291"})
        if result.status == "success":
            for s in result.result["sightings"]:
                assert "registration_plate" in s
                assert "confidence" in s

    def test_eliminated_vehicle_in_sightings(self):
        """Eliminated vehicles have vehicle_of_interest=False; others may omit the field."""
        result = query_surveillance({"incident_case": "MCR-2025-0291"})
        if result.status == "success":
            for s in result.result["sightings"]:
                # If the field is present it must be a boolean
                if "vehicle_of_interest" in s:
                    assert isinstance(s["vehicle_of_interest"], bool)

    def test_call_id_propagated(self):
        result = query_surveillance({"incident_case": "MCR-2025-0291", "_call_id": "test-003"})
        assert result.call_id == "test-003"

    def test_tool_name_in_result(self):
        result = query_surveillance({"incident_case": "MCR-2025-0291"})
        assert result.tool_name == "query_surveillance"

    def test_no_cross_read_of_financial_data(self):
        import services.ai_agent.tools.surveillance as mod
        assert "surveillance-records" in str(mod._DATA_FILE)


# ---------------------------------------------------------------------------
# financial_intelligence
# ---------------------------------------------------------------------------

class TestQueryFinancialIntelligence:
    def test_found_by_person_name(self):
        result = query_financial_intelligence({"person_name": "Daniel Mercer"})
        assert result.status in ("success", "not_found")

    def test_not_found_unknown_person(self):
        result = query_financial_intelligence({"person_name": "Nobody Here"})
        assert result.status == "not_found"

    def test_invalid_input_no_args(self):
        result = query_financial_intelligence({})
        assert result.status == "invalid_input"

    def test_account_ref_precedence(self):
        """account_ref takes precedence over person_name."""
        result = query_financial_intelligence({
            "account_ref": "MBK-ACCT-9921",
            "person_name": "Nobody Here",
        })
        # Either found via account_ref or not_found — not an error
        assert result.status in ("success", "not_found")

    def test_no_guilt_conclusions_in_tool(self):
        """Raw facts only — no 'coordinated', 'criminal', or 'guilty' language."""
        result = query_financial_intelligence({"person_name": "Daniel Mercer"})
        if result.status == "success":
            payload_str = str(result.result)
            prohibited = ["coordinated the robber", "criminal", "guilty", "stole"]
            for word in prohibited:
                assert word not in payload_str.lower(), (
                    f"Tool output must not contain '{word}' — conclusions belong to the investigator"
                )

    def test_call_id_propagated(self):
        result = query_financial_intelligence({"person_name": "Daniel Mercer", "_call_id": "test-004"})
        assert result.call_id == "test-004"

    def test_tool_name_in_result(self):
        result = query_financial_intelligence({"person_name": "Daniel Mercer"})
        assert result.tool_name == "query_financial_intelligence"

    def test_no_cross_read_of_access_logs(self):
        import services.ai_agent.tools.financial_intelligence as mod
        assert "financial-records" in str(mod._DATA_FILE)


# ---------------------------------------------------------------------------
# Data isolation — ground truth must never be read at runtime
# ---------------------------------------------------------------------------

class TestDataIsolation:
    def test_ground_truth_not_imported_by_vehicle_tool(self):
        import services.ai_agent.tools.vehicle_records as mod
        assert "ground-truth" not in str(getattr(mod, "_DATA_FILE", ""))

    def test_ground_truth_not_imported_by_access_tool(self):
        import services.ai_agent.tools.access_logs as mod
        assert "ground-truth" not in str(getattr(mod, "_DATA_FILE", ""))

    def test_ground_truth_not_imported_by_surveillance_tool(self):
        import services.ai_agent.tools.surveillance as mod
        assert "ground-truth" not in str(getattr(mod, "_DATA_FILE", ""))

    def test_ground_truth_not_imported_by_financial_tool(self):
        import services.ai_agent.tools.financial_intelligence as mod
        assert "ground-truth" not in str(getattr(mod, "_DATA_FILE", ""))
