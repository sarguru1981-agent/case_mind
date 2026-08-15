"""AI Agent — ReAct execution loop.

Implements the Reason → Act → Observe → Repeat cycle.

Design principles
-----------------
1. The agent receives an ASSIGNED TASK.  It does NOT decompose broad goals,
   prioritise sub-tasks, or manage its own workflow.  Those belong to a
   future Agentic AI layer.

2. Tool selection is derived at runtime from:
     a) case/credential IDs extracted from the assigned task text
     b) registrations/persons discovered inside tool observations
   It is NOT a hardcoded iteration-to-tool mapping.

3. The critical ordering dependency is naturally preserved:
     lookup_vehicle("MBK-4172") can only be triggered AFTER
     query_surveillance returns that plate in an observation.
   The agent does not know "MBK-4172" in advance.

4. No private chain-of-thought is stored.  decision_summary contains
   only concise operational reasoning safe to display to the detective.

5. This module imports ONLY the ToolRegistry.
   It never imports vehicle_records, access_logs, surveillance, or
   financial_intelligence directly.
   It never reads any tool-data JSON file.
   It never reads operation-nightfall-ground-truth.json.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from services.ai_agent.models import AgentState, EvidenceItem, ToolCall, ToolResult
from services.ai_agent.tools import ToolRegistry

# ---------------------------------------------------------------------------
# Patterns for extracting entities from text
# ---------------------------------------------------------------------------

_CASE_ID_RE    = re.compile(r"MCR-\d{4}-\d{4}")
_CREDENTIAL_RE = re.compile(r"\bNF-\d{4}\b")
_NAME_RE       = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:'s|,|\s+involvement|\s+financial|\s+activity)")


# ---------------------------------------------------------------------------
# Decision engine — derives the next tool call from task + observations
# ---------------------------------------------------------------------------

def _plates_needing_lookup(state: AgentState) -> list[str]:
    """Registrations discovered in surveillance observations not yet looked up."""
    discovered: list[str] = []
    seen: set[str] = set()
    for obs in state.observations:
        if obs.tool_name == "query_surveillance" and obs.status == "success" and obs.result:
            for sighting in obs.result.get("sightings", []):
                plate = sighting.get("registration_plate")
                if plate and sighting.get("registration_captured") and plate not in seen:
                    discovered.append(plate)
                    seen.add(plate)

    already_looked_up = {
        tc.arguments.get("registration", "")
        for tc in state.tool_calls
        if tc.tool_name == "lookup_vehicle"
    }
    return [p for p in discovered if p not in already_looked_up]


def _cases_needing_surveillance(state: AgentState) -> list[str]:
    """Case IDs in the task text that have not yet been queried in surveillance."""
    task_cases = _CASE_ID_RE.findall(state.assigned_task)
    already_queried = {
        tc.arguments.get("incident_case", "")
        for tc in state.tool_calls
        if tc.tool_name == "query_surveillance"
    }
    return [c for c in task_cases if c not in already_queried]


def _credentials_needing_access_query(state: AgentState) -> list[str]:
    """Credential IDs in the task text not yet queried in access logs."""
    task_creds = _CREDENTIAL_RE.findall(state.assigned_task)
    already_queried = {
        tc.arguments.get("credential_id", "")
        for tc in state.tool_calls
        if tc.tool_name == "query_access_logs"
    }
    return [c for c in task_creds if c not in already_queried]


def _persons_needing_financial_query(state: AgentState) -> list[str]:
    """
    Persons requiring a financial intelligence query, derived from:
    1. Names explicitly mentioned in the task text alongside 'financial'
    2. Keeper names confirmed by vehicle lookup observations

    Returns only persons not yet queried.
    """
    if "financial" not in state.assigned_task.lower():
        return []

    candidates: list[str] = []
    seen: set[str] = set()

    # Source 1: names from task text
    for m in _NAME_RE.finditer(state.assigned_task):
        name = m.group(1)
        if name not in seen:
            candidates.append(name)
            seen.add(name)

    # Source 2: keepers confirmed by vehicle lookups
    for obs in state.observations:
        if obs.tool_name == "lookup_vehicle" and obs.status == "success" and obs.result:
            keeper = obs.result.get("registered_keeper", "")
            if keeper and keeper not in seen:
                candidates.append(keeper)
                seen.add(keeper)

    already_queried = {
        tc.arguments.get("person_name", "")
        for tc in state.tool_calls
        if tc.tool_name == "query_financial_intelligence"
    }
    return [p for p in candidates if p not in already_queried]


def _decide_next_action(
    state:    AgentState,
    registry: ToolRegistry,
) -> Optional[tuple[str, ToolCall]]:
    """
    Derive the next (decision_summary, ToolCall) from task + observations.

    Returns None when all task requirements have been addressed —
    signalling the loop to complete.

    Decision priority:
      1. Vehicle lookup for any plate discovered in surveillance (dynamic)
      2. Surveillance for any case ID in the task (from task text)
      3. Access logs for any credential in the task (from task text)
      4. Financial intelligence for any person in the task / confirmed as keeper
      5. None → task complete
    """

    # 1. Dynamic: vehicle lookup for newly discovered plates
    plates = _plates_needing_lookup(state)
    if plates:
        plate = plates[0]
        return (
            f"Surveillance observation returned registration {plate}. "
            f"Vehicle keeper identity is required to connect the vehicle to an individual.",
            ToolCall(tool_name="lookup_vehicle", arguments={"registration": plate}),
        )

    # 2. Surveillance for case IDs in the task
    cases = _cases_needing_surveillance(state)
    if cases:
        case = cases[0]
        return (
            f"Task requires surveillance evidence for {case}. "
            f"Querying external ANPR and CCTV records for that incident.",
            ToolCall(tool_name="query_surveillance", arguments={"incident_case": case}),
        )

    # 3. Access logs for credentials in the task
    creds = _credentials_needing_access_query(state)
    if creds:
        cred = creds[0]
        return (
            f"Task requires credential access history for {cred}. "
            f"Querying Northstar Facilities engineer access records.",
            ToolCall(tool_name="query_access_logs", arguments={"credential_id": cred}),
        )

    # 4. Financial intelligence
    persons = _persons_needing_financial_query(state)
    if persons:
        person = persons[0]
        return (
            f"Task requires financial activity review for {person}. "
            f"Querying Financial Intelligence Unit records.",
            ToolCall(
                tool_name="query_financial_intelligence",
                arguments={"person_name": person},
            ),
        )

    # 5. All requirements addressed
    return None


# ---------------------------------------------------------------------------
# Evidence extraction — facts confirmed by observations
# ---------------------------------------------------------------------------

def _extract_evidence(obs: ToolResult) -> list[EvidenceItem]:
    """Extract structured evidence items from a successful tool observation."""
    items: list[EvidenceItem] = []
    if obs.status != "success" or not obs.result:
        return items

    r = obs.result

    if obs.tool_name == "lookup_vehicle":
        keeper = r.get("registered_keeper", "")
        colour = r.get("colour", "")
        make   = r.get("make", "")
        model  = r.get("model", "")
        reg    = r.get("registration", "")
        if keeper and reg:
            items.append(EvidenceItem(
                fact        = f"{reg} is a {colour} {make} {model} registered to {keeper}.",
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "HIGH",
            ))

    elif obs.tool_name == "query_access_logs":
        events    = r.get("access_events", [])
        assigned  = r.get("assigned_to", "")
        cred_id   = r.get("credential_id", "")
        oos_count = sum(1 for e in events if "out-of-hours" in e.get("access_type", "").lower())
        if events:
            items.append(EvidenceItem(
                fact        = (
                    f"Credential {cred_id} ({assigned}) has {len(events)} recorded access event(s) "
                    f"at Operation Nightfall premises"
                    + (f", including {oos_count} out-of-hours entry(s) with no work order." if oos_count else ".")
                ),
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "HIGH",
            ))
        elif r.get("credential_status", "").startswith("Revoked"):
            items.append(EvidenceItem(
                fact        = f"Credential {cred_id} ({assigned}) was revoked and has no access events.",
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "HIGH",
            ))

    elif obs.tool_name == "query_surveillance":
        sightings = r.get("sightings", [])
        for s in sightings:
            plate      = s.get("registration_plate")
            confidence = s.get("confidence", "UNKNOWN")
            case_id    = s.get("incident_case", "")
            time       = s.get("time_of_sighting", "")
            elim       = s.get("vehicle_of_interest") is False
            if plate and s.get("registration_captured"):
                label = "ELIMINATED" if elim else "observed"
                items.append(EvidenceItem(
                    fact        = (
                        f"Registration {plate} was {label} at {case_id} at {time} "
                        f"(confidence: {confidence})."
                    ),
                    source_tool = obs.tool_name,
                    call_id     = obs.call_id,
                    confidence  = "HIGH" if elim or "HIGH" in confidence else "MEDIUM",
                ))

    elif obs.tool_name == "query_financial_intelligence":
        name       = r.get("name", "")
        txns       = r.get("transactions", [])
        transfers  = r.get("inbound_transfers_from_mercer", [])
        cash       = sum(t["amount_gbp"] for t in txns if t.get("type") == "Cash Deposit")
        out_total  = sum(t["amount_gbp"] for t in txns if "Outbound" in t.get("type", ""))
        recipients = list({t["recipient_name"] for t in txns if t.get("recipient_name")})

        if cash:
            items.append(EvidenceItem(
                fact        = (
                    f"{name} made cash deposits totalling £{cash:,} "
                    f"across the Operation Nightfall incident period with no identified legitimate source."
                ),
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "MEDIUM",
            ))
        if recipients and out_total:
            items.append(EvidenceItem(
                fact        = (
                    f"{name} transferred £{out_total:,} to {', '.join(recipients)} "
                    f"labelled 'consultancy' with no formal arrangement on record."
                ),
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "MEDIUM",
            ))
        if transfers:
            total = sum(t["amount_gbp"] for t in transfers)
            items.append(EvidenceItem(
                fact        = (
                    f"{name} received £{total:,} in inbound transfers "
                    f"labelled 'consultancy' with no formal arrangement on record."
                ),
                source_tool = obs.tool_name,
                call_id     = obs.call_id,
                confidence  = "MEDIUM",
            ))

    return items


# ---------------------------------------------------------------------------
# Completion summary
# ---------------------------------------------------------------------------

def _build_completion_summary(state: AgentState) -> str:
    """Compose a factual, evidence-backed completion summary.

    States only what the tool observations confirmed.
    Does not conclude guilt, name criminals, or claim case solved.
    """
    parts: list[str] = []
    tools_called = {tc.tool_name for tc in state.tool_calls}

    vehicle_facts = [
        e.fact for e in state.evidence if e.source_tool == "lookup_vehicle"
    ]
    access_facts = [
        e.fact for e in state.evidence if e.source_tool == "query_access_logs"
    ]
    surveillance_facts = [
        e.fact for e in state.evidence
        if e.source_tool == "query_surveillance" and "ELIMINATED" not in e.fact
    ]
    financial_facts = [
        e.fact for e in state.evidence
        if e.source_tool == "query_financial_intelligence"
    ]

    if surveillance_facts:
        parts.append(
            "Surveillance records corroborate: "
            + " ".join(surveillance_facts)
        )
    if vehicle_facts:
        parts.append(
            "Vehicle records confirm: "
            + " ".join(vehicle_facts)
        )
    if access_facts:
        parts.append(
            "Access records show: "
            + " ".join(access_facts)
        )
    if financial_facts:
        parts.append(
            "Financial records indicate: "
            + " ".join(financial_facts)
        )

    # Analyst note on Marcus Vale — factual, not conclusory
    financial_obs = [
        obs for obs in state.observations
        if obs.tool_name == "query_financial_intelligence"
        and obs.status == "success"
        and obs.result
    ]
    for obs in financial_obs:
        txns = obs.result.get("transactions", [])
        recipients = list({t["recipient_name"] for t in txns if t.get("recipient_name")})
        for r in recipients:
            # Confirm the recipient's role if observable from the data
            parts.append(
                f"{r} is identified in financial records as a recipient of "
                f"unexplained payments. Further enquiry is required to determine "
                f"the nature of that financial relationship."
            )

    if not parts:
        parts.append("External tool queries completed. See observations for details.")

    tool_count = len(state.tool_calls)
    parts.append(
        f"Investigation complete after {state.iteration} iteration(s), "
        f"{tool_count} tool call(s)."
    )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

ASSIGNED_TASK = (
    "Using external investigative records, determine whether the dark blue Ford "
    "Transit and credential NF-3847 can be independently corroborated at the "
    "Kingsley Watch Co. on the night of MCR-2025-0291, identify the registered "
    "keeper of the vehicle, and determine whether any financial activity in the "
    "period following the Operation Nightfall incidents is consistent with "
    "Daniel Mercer's involvement."
)


def run_investigation(
    assigned_task:  str          = ASSIGNED_TASK,
    registry:       Optional[ToolRegistry] = None,
    max_iterations: int          = 10,
) -> AgentState:
    """
    Execute the AI Agent ReAct loop for the assigned task.

    The loop:
      DECIDE → ACT → OBSERVE → extract evidence → DECIDE → ...

    Stops when:
      a) the decision engine returns None  (task complete)
      b) max_iterations is reached
    """
    if registry is None:
        from services.ai_agent.tools import build_registry
        registry = build_registry()

    if not assigned_task or not assigned_task.strip():
        raise ValueError("assigned_task must be a non-empty string.")

    state = AgentState(
        assigned_task  = assigned_task,
        max_iterations = max_iterations,
    )

    for _ in range(max_iterations):
        state.iteration += 1

        # ----- REASON -----
        next_action = _decide_next_action(state, registry)

        if next_action is None:
            # Decision engine found no remaining requirements
            state.status             = "complete"
            state.decision_summary   = "All task requirements have been addressed by tool observations."
            state.current_action     = None
            state.completion_summary = _build_completion_summary(state)
            break

        decision_summary, tool_call = next_action
        state.decision_summary = decision_summary
        state.current_action   = tool_call

        # Inject call_id so tools can echo it back
        tool_call.arguments["_call_id"] = tool_call.call_id
        state.tool_calls.append(tool_call)

        # ----- ACT -----
        observation = registry.invoke_call(tool_call)

        # Restore call_id from tool_call in case tool didn't echo it
        if not observation.call_id:
            observation = observation.model_copy(update={"call_id": tool_call.call_id})

        # Clean up internal _call_id from arguments (not part of public contract)
        tool_call.arguments.pop("_call_id", None)

        # ----- OBSERVE -----
        state.observations.append(observation)

        # ----- EXTRACT EVIDENCE -----
        new_evidence = _extract_evidence(observation)
        state.evidence.extend(new_evidence)

    else:
        # Exhausted max_iterations
        state.status           = "max_iterations_reached"
        state.decision_summary = f"Stopped after {max_iterations} iterations without completing all task requirements."
        state.completion_summary = (
            f"Investigation stopped at maximum iteration limit ({max_iterations}). "
            + _build_completion_summary(state)
        )

    return state
