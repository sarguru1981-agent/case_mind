"""Vehicle Records Tool — DVLA enquiry for Millbrook County Police.

Source dataset: sentinel/data/tool-data/vehicle-records.json
Lookup key:     registration (exact match only)

This tool does NOT access any other tool-data file.
It does NOT return keeper_dob.
It does NOT infer guilt or investigative conclusions.
"""
from __future__ import annotations

import json
from pathlib import Path

from services.ai_agent.models import ToolResult

_DATA_FILE = (
    Path(__file__).resolve().parents[4]  # sentinel/
    / "data" / "tool-data" / "vehicle-records.json"
)

_SOURCE_SYSTEM = "DVLA Vehicle Enquiry — Millbrook County Police Major Crimes Unit"

# Fields intentionally excluded from tool output
_EXCLUDED_FIELDS = {"keeper_dob"}


def _load_records() -> dict[str, dict]:
    with open(_DATA_FILE) as f:
        data = json.load(f)
    return {r["registration"]: r for r in data["records"]}


def lookup_vehicle(arguments: dict) -> ToolResult:
    """Query vehicle records by exact registration plate."""
    registration = arguments.get("registration")

    if not registration or not isinstance(registration, str) or not registration.strip():
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "lookup_vehicle",
            status        = "invalid_input",
            error         = "'registration' is required and must be a non-empty string.",
            query_summary = "Vehicle lookup: invalid input",
        )

    registration = registration.strip().upper()
    records = _load_records()

    if registration not in records:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "lookup_vehicle",
            status        = "not_found",
            result        = {
                "query":   {"registration": registration},
                "message": f"No vehicle record found for registration {registration}.",
                "source_system": _SOURCE_SYSTEM,
            },
            query_summary = f"Vehicle lookup: {registration} — not found",
        )

    raw = records[registration]
    result_payload = {
        k: v for k, v in raw.items() if k not in _EXCLUDED_FIELDS
    }
    result_payload["source_system"] = _SOURCE_SYSTEM
    result_payload["result_count"]  = 1

    return ToolResult(
        call_id       = arguments.get("_call_id", ""),
        tool_name     = "lookup_vehicle",
        status        = "success",
        result        = result_payload,
        query_summary = f"Vehicle lookup: {registration}",
    )


# ---------------------------------------------------------------------------
# Tool schema (exposed to the registry and agent)
# ---------------------------------------------------------------------------

VEHICLE_TOOL_NAME = "lookup_vehicle"

VEHICLE_TOOL_DESCRIPTION = (
    "Query DVLA vehicle records by exact registration plate. "
    "Returns the registered keeper, vehicle description (make, model, colour, "
    "year, body type), and insurance status. "
    "Use when a vehicle registration has been surfaced by another tool and "
    "keeper identity is required, or to verify/eliminate a suspect vehicle."
)

VEHICLE_TOOL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "registration": {
            "type":        "string",
            "description": "Vehicle registration plate, e.g. MBK-4172",
        }
    },
    "required": ["registration"],
}
