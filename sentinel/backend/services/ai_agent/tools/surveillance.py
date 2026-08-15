"""Surveillance Tool — ANPR network and Council CCTV correlation records.

Source dataset: sentinel/data/tool-data/surveillance-records.json
Lookup keys:    incident_case (MCR-YYYY-NNNN) OR registration (exact plate)
                Optional: time_window_start / time_window_end (ISO date-time,
                          only valid alongside incident_case)

This tool does NOT implement:
  - facial recognition
  - image analysis
  - live surveillance queries
  - keyword search on vehicle descriptions

It returns structured sighting metadata exactly as recorded by the
Millbrook Technical Surveillance Unit.
This tool does NOT access any other tool-data file.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from services.ai_agent.models import ToolResult

_DATA_FILE = (
    Path(__file__).resolve().parents[4]
    / "data" / "tool-data" / "surveillance-records.json"
)

_SOURCE_SYSTEM = "ANPR Network + Council CCTV Correlation — Operation Nightfall Series"
_ISO_DT_RE     = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def _load_sightings() -> list[dict]:
    with open(_DATA_FILE) as f:
        return json.load(f)["sightings"]


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _sighting_datetime(sighting: dict) -> datetime | None:
    night = sighting.get("night", "")
    time  = sighting.get("time_of_sighting", "")
    date_part = night.split(" ")[0] if night else ""
    if date_part and time:
        try:
            return datetime.fromisoformat(f"{date_part}T{time}")
        except ValueError:
            pass
    return None


def query_surveillance(arguments: dict) -> ToolResult:
    """Query surveillance sighting records by incident case or registration plate."""
    incident_case  = (arguments.get("incident_case") or "").strip()
    registration   = (arguments.get("registration")  or "").strip().upper()
    window_start   = (arguments.get("time_window_start") or "").strip()
    window_end     = (arguments.get("time_window_end")   or "").strip()

    # Validate: at least one lookup key required
    if not incident_case and not registration:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_surveillance",
            status        = "invalid_input",
            error         = "At least one of 'incident_case' or 'registration' is required.",
            query_summary = "Surveillance: invalid input",
        )

    # Validate: time window only valid with incident_case
    if (window_start or window_end) and not incident_case:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_surveillance",
            status        = "invalid_input",
            error         = "'time_window_start' / 'time_window_end' can only be used with 'incident_case'.",
            query_summary = "Surveillance: invalid input",
        )

    # Validate ISO date-time format if provided
    if window_start and not _ISO_DT_RE.match(window_start):
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_surveillance",
            status        = "invalid_input",
            error         = "'time_window_start' must be ISO 8601 format YYYY-MM-DDTHH:MM.",
            query_summary = "Surveillance: invalid input",
        )
    if window_end and not _ISO_DT_RE.match(window_end):
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_surveillance",
            status        = "invalid_input",
            error         = "'time_window_end' must be ISO 8601 format YYYY-MM-DDTHH:MM.",
            query_summary = "Surveillance: invalid input",
        )

    dt_start = _parse_dt(window_start) if window_start else None
    dt_end   = _parse_dt(window_end)   if window_end   else None

    all_sightings = _load_sightings()
    matched: list[dict] = []

    for s in all_sightings:
        if incident_case and registration:
            # Both supplied: must match both
            if s.get("incident_case") != incident_case:
                continue
            if s.get("registration_plate") != registration:
                continue
        elif incident_case:
            if s.get("incident_case") != incident_case:
                continue
        else:  # registration only
            if not s.get("registration_captured"):
                continue
            if s.get("registration_plate") != registration:
                continue

        # Time window filter
        if dt_start or dt_end:
            s_dt = _sighting_datetime(s)
            if s_dt is None:
                continue
            if dt_start and s_dt < dt_start:
                continue
            if dt_end and s_dt > dt_end:
                continue

        matched.append(s)

    query_label = incident_case or registration
    if not matched:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_surveillance",
            status        = "not_found",
            result        = {
                "query":         {"incident_case": incident_case, "registration": registration},
                "sightings":     [],
                "message":       f"No sighting records found for {query_label}.",
                "source_system": _SOURCE_SYSTEM,
            },
            query_summary = f"Surveillance: {query_label} — no sightings",
        )

    return ToolResult(
        call_id       = arguments.get("_call_id", ""),
        tool_name     = "query_surveillance",
        status        = "success",
        result        = {
            "query":         {"incident_case": incident_case, "registration": registration},
            "sightings":     matched,
            "result_count":  len(matched),
            "source_system": _SOURCE_SYSTEM,
        },
        query_summary = f"Surveillance: {query_label} — {len(matched)} sighting(s)",
    )


# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------

SURVEILLANCE_TOOL_NAME = "query_surveillance"

SURVEILLANCE_TOOL_DESCRIPTION = (
    "Query ANPR network and Council CCTV sighting records compiled by the "
    "Millbrook Technical Surveillance Unit. "
    "Returns structured sighting metadata: vehicle description, registration "
    "(if captured), time, camera ID, distance from premises, and confidence level. "
    "Use to determine whether a specific vehicle or registration was observed near "
    "a crime scene, or to retrieve all surveillance data for a specific incident. "
    "Does NOT perform facial recognition, image analysis, or live surveillance."
)

SURVEILLANCE_TOOL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "incident_case": {
            "type":        "string",
            "description": "Case reference number, e.g. MCR-2025-0291",
        },
        "registration": {
            "type":        "string",
            "description": "Vehicle registration plate, e.g. MBK-4172",
        },
        "time_window_start": {
            "type":        "string",
            "description": "ISO 8601 date-time lower bound, e.g. 2025-04-01T23:00. Only valid with incident_case.",
        },
        "time_window_end": {
            "type":        "string",
            "description": "ISO 8601 date-time upper bound. Only valid with incident_case.",
        },
    },
    "anyOf": [
        {"required": ["incident_case"]},
        {"required": ["registration"]},
    ],
}
