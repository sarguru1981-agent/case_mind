"""Access Logs Tool — Northstar Facilities credentialed access records.

Source dataset: sentinel/data/tool-data/access-logs.json
Lookup keys:    credential_id (primary) OR person_name
                If both provided, credential_id takes precedence.
                If neither provided, returns invalid_input.

This tool does NOT access any other tool-data file.
A revoked credential with zero events is a valid success result, not an error.
"""
from __future__ import annotations

import json
from pathlib import Path

from services.ai_agent.models import ToolResult

_DATA_FILE = (
    Path(__file__).resolve().parents[4]
    / "data" / "tool-data" / "access-logs.json"
)

_SOURCE_SYSTEM = "Northstar Facilities Ltd — Engineer Credential Access Records"


def _load_credentials() -> tuple[dict[str, dict], dict[str, dict]]:
    """Return (by_credential_id, by_person_name) lookup dicts."""
    with open(_DATA_FILE) as f:
        data = json.load(f)

    by_id:   dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    for cred in data["credentials"]:
        by_id[cred["credential_id"]] = cred
        by_name[cred["assigned_to"].lower()] = cred
    return by_id, by_name


def query_access_logs(arguments: dict) -> ToolResult:
    """Query engineer access records by credential ID or person name."""
    credential_id = arguments.get("credential_id", "").strip() if arguments.get("credential_id") else ""
    person_name   = arguments.get("person_name",   "").strip() if arguments.get("person_name")   else ""

    if not credential_id and not person_name:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_access_logs",
            status        = "invalid_input",
            error         = "At least one of 'credential_id' or 'person_name' is required.",
            query_summary = "Access logs: invalid input",
        )

    by_id, by_name = _load_credentials()

    # credential_id takes precedence
    if credential_id:
        record = by_id.get(credential_id)
        query_key = f"credential {credential_id}"
    else:
        record = by_name.get(person_name.lower())
        query_key = f"person '{person_name}'"

    if record is None:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_access_logs",
            status        = "not_found",
            result        = {
                "query":         {"credential_id": credential_id, "person_name": person_name},
                "message":       f"No credential record found matching {query_key}.",
                "source_system": _SOURCE_SYSTEM,
            },
            query_summary = f"Access logs: {query_key} — not found",
        )

    payload = {
        "credential_id":     record["credential_id"],
        "assigned_to":       record["assigned_to"],
        "role":              record["role"],
        "credential_status": record["status"],
        "access_events":     record["access_events"],
        "result_count":      len(record["access_events"]),
        "source_system":     _SOURCE_SYSTEM,
    }
    if record.get("notes"):
        payload["notes"] = record["notes"]

    return ToolResult(
        call_id       = arguments.get("_call_id", ""),
        tool_name     = "query_access_logs",
        status        = "success",
        result        = payload,
        query_summary = f"Access logs: {record['credential_id']} / {record['assigned_to']}",
    )


# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------

ACCESS_TOOL_NAME = "query_access_logs"

ACCESS_TOOL_DESCRIPTION = (
    "Query Northstar Facilities Ltd engineer credential access records "
    "(obtained under Major Crimes Unit formal request). "
    "Returns all premises access events for a given credential ID or named individual, "
    "including date, time, access type, duration, and work-order reference. "
    "Use to determine whether a specific engineer or credential was present at a "
    "target premises, whether any access was out-of-hours, and whether a work order "
    "existed to legitimise the visit."
)

ACCESS_TOOL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "credential_id": {
            "type":        "string",
            "description": "Engineer credential ID, e.g. NF-3847",
        },
        "person_name": {
            "type":        "string",
            "description": "Full name of the engineer, e.g. Daniel Mercer",
        },
    },
    "anyOf": [
        {"required": ["credential_id"]},
        {"required": ["person_name"]},
    ],
}
