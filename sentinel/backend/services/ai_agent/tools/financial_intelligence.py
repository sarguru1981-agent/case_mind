"""Financial Intelligence Tool — FIU records for Operation Nightfall.

Source dataset: sentinel/data/tool-data/financial-records.json
Lookup keys:    person_name OR account_ref
                If both provided, account_ref takes precedence.

This tool returns raw financial facts.
The AI Agent must infer investigative significance.
The tool does NOT conclude: "Marcus Vale coordinated the robberies."
That inference belongs to human investigation review.

This tool does NOT access any other tool-data file.
"""
from __future__ import annotations

import json
from pathlib import Path

from services.ai_agent.models import ToolResult

_DATA_FILE = (
    Path(__file__).resolve().parents[4]
    / "data" / "tool-data" / "financial-records.json"
)

_SOURCE_SYSTEM = "Financial Intelligence Unit — Operation Nightfall Series"


def _load_subjects() -> tuple[dict[str, dict], dict[str, dict]]:
    """Return (by_account_ref, by_name_lower) lookup dicts."""
    with open(_DATA_FILE) as f:
        data = json.load(f)

    by_ref:  dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    for subject in data["subjects"]:
        by_ref[subject["account_ref"]]          = subject
        by_name[subject["name"].lower()]         = subject
    return by_ref, by_name


def query_financial_intelligence(arguments: dict) -> ToolResult:
    """Query FIU financial records by person name or account reference."""
    person_name = (arguments.get("person_name")  or "").strip()
    account_ref = (arguments.get("account_ref")  or "").strip()

    if not person_name and not account_ref:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_financial_intelligence",
            status        = "invalid_input",
            error         = "At least one of 'person_name' or 'account_ref' is required.",
            query_summary = "Financial intelligence: invalid input",
        )

    by_ref, by_name = _load_subjects()

    # account_ref takes precedence
    if account_ref:
        record    = by_ref.get(account_ref)
        query_key = f"account {account_ref}"
    else:
        record    = by_name.get(person_name.lower())
        query_key = f"'{person_name}'"

    if record is None:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = "query_financial_intelligence",
            status        = "not_found",
            result        = {
                "query":         {"person_name": person_name, "account_ref": account_ref},
                "message":       f"No financial record found for {query_key}.",
                "source_system": _SOURCE_SYSTEM,
            },
            query_summary = f"Financial intelligence: {query_key} — not found",
        )

    # Build payload from actual data; both subject shapes are handled
    payload: dict = {
        "name":                    record["name"],
        "account_ref":             record["account_ref"],
        "occupation":              record.get("occupation", ""),
        "declared_annual_income":  record.get("declared_annual_income"),
        "source_system":           _SOURCE_SYSTEM,
    }

    # Mercer has 'transactions'; Vale has 'inbound_transfers_from_mercer'
    if "transactions" in record:
        payload["transactions"]   = record["transactions"]
        payload["result_count"]   = len(record["transactions"])
    if "inbound_transfers_from_mercer" in record:
        payload["inbound_transfers_from_mercer"] = record["inbound_transfers_from_mercer"]
        payload["result_count"] = len(record["inbound_transfers_from_mercer"])
    if "analyst_note" in record:
        payload["analyst_note"] = record["analyst_note"]

    return ToolResult(
        call_id       = arguments.get("_call_id", ""),
        tool_name     = "query_financial_intelligence",
        status        = "success",
        result        = payload,
        query_summary = f"Financial intelligence: {record['name']}",
    )


# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------

FINANCIAL_TOOL_NAME = "query_financial_intelligence"

FINANCIAL_TOOL_DESCRIPTION = (
    "Query Financial Intelligence Unit records (obtained under Production Order) "
    "for a named individual or account reference. "
    "Returns transaction history, declared income, and analyst notes. "
    "Use to determine whether financial activity is consistent with unexplained "
    "income or to identify financial connections between named individuals."
)

FINANCIAL_TOOL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "person_name": {
            "type":        "string",
            "description": "Full name of the subject, e.g. Daniel Mercer",
        },
        "account_ref": {
            "type":        "string",
            "description": "Account reference number, e.g. MBK-ACCT-9921",
        },
    },
    "anyOf": [
        {"required": ["person_name"]},
        {"required": ["account_ref"]},
    ],
}
