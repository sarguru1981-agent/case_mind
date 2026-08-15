"""Agentic AI orchestrator — mission loop for Operation Nightfall.

Public API:
    run_mission(mission, max_cycles, rag_fn, agent_fn, synthesis_fn) -> MissionState

The mission loop is NOT a ReAct loop.  It operates at the task level:

  MISSION_RECEIVED
    → DECOMPOSE       (decomposer.decompose)
    → PRIORITISE      (prioritizer.rebuild_queue)
    → for each cycle:
        SELECT        (pop highest-priority READY task)
        ROUTE         (pick capability based on task.assigned_capability)
        EXECUTE       (call capability with task.objective)
        OBSERVE       (store result on task)
        EXTRACT       (pull known_findings from result)
        ADAPT         (create new tasks, re-prioritise existing tasks)
        REPRIORITISE  (resolve_dependencies + rebuild_queue)
        CHECK         (completion criteria satisfied?)
    → READY_FOR_HUMAN_REVIEW (or MAX_CYCLES_REACHED / BLOCKED)

Data boundary
-------------
* This module never reads JSON files directly.
* It never imports from ai_agent.tools.* or agentic_rag.investigator.
* All external data is accessed through the injected capability functions.
* operation-nightfall-ground-truth.json is never accessed here.

Human authority boundary
------------------------
* Final status is READY_FOR_HUMAN_REVIEW.
* final_assessment uses language like "person of interest", "warrants further
  investigation", "human review required".
* It never claims guilt, issues warrants, or recommends arrest.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .decomposer import decompose
from .models import (
    MissionState,
    MissionStatus,
    Priority,
    Task,
    TaskStatus,
    TaskType,
    WorkflowEvent,
    WorkflowEventType,
)
from .prioritizer import (
    critical_and_high_complete,
    deprioritize,
    elevate_priority,
    rebuild_queue,
    resolve_dependencies,
    synthesis_complete,
)


# ---------------------------------------------------------------------------
# Broad mission constant
# ---------------------------------------------------------------------------

BROAD_MISSION = (
    "Investigate the Operation Nightfall robbery series, determine whether the"
    " four incidents are connected, identify the strongest persons of interest,"
    " evaluate significant alternative leads, and produce an evidence-backed"
    " investigation assessment for human review."
)

# Case directory — relative anchor used when orchestrator calls agentic_rag
_CASE_DIR = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "data" / "case-files" / "serial-robbery"
)

# Patterns for extracting entities from text
_CASE_ID_RE    = re.compile(r"MCR-\d{4}-\d{4}")
_CRED_RE       = re.compile(r"\bNF-\d{4}\b")
_PLATE_RE      = re.compile(r"\b([A-Z]{2,3}-\d{4})\b")
_NAME_RE       = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")

# Parts that appear in lead labels but are NOT person name components.
# Two-word underscore labels where BOTH parts are absent from this set
# are treated as person names by Rule 0.
_NON_PERSON_PARTS: frozenset[str] = frozenset({
    "facilities", "pattern", "transit", "mode", "maintenance",
    "validation", "records", "credential", "incident", "nightfall",
    "operation", "suspect", "persons", "unknown", "vehicle", "alarm",
    "dark", "blue", "white", "guard", "sentry",
})

# Commercial-entity indicators used by Rule 5 to detect eliminated vehicles.
_COMMERCIAL_INDICATORS: frozenset[str] = frozenset({
    "Ltd", "Limited", "plc", "Inc", "Corp",
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_mission(
    mission:       str                               = BROAD_MISSION,
    max_cycles:    int                               = 15,
    rag_fn:        Optional[Callable[..., Any]]      = None,
    agent_fn:      Optional[Callable[..., Any]]      = None,
    synthesis_fn:  Optional[Callable[[str], str]]    = None,
) -> MissionState:
    """Execute the Agentic AI mission loop.

    Args:
        mission:      The broad investigation mission.
        max_cycles:   Safety ceiling on loop iterations.
        rag_fn:       Injectable for tests.  Defaults to agentic_rag.investigate.
        agent_fn:     Injectable for tests.  Defaults to ai_agent.run_investigation.
        synthesis_fn: Injectable for tests.  Defaults to llm.client.generate_grounded_answer.

    Returns:
        MissionState with full task history, findings, and final assessment.
    """
    _rag_fn      = rag_fn      or _default_rag
    _agent_fn    = agent_fn    or _default_agent
    _synth_fn    = synthesis_fn or _default_synthesis

    state = MissionState(
        mission_id          = str(uuid.uuid4())[:8],
        mission             = mission,
        status              = MissionStatus.INITIALIZING,
        max_cycles          = max_cycles,
        completion_criteria = [
            "All CRITICAL tasks completed",
            "All HIGH tasks completed or deprioritised",
            "SYNTHESIS task completed",
            "Sufficient known findings collected",
        ],
    )

    _emit(state, WorkflowEventType.MISSION_RECEIVED, mission[:120], cycle=0)

    # --- Decompose ----------------------------------------------------------
    initial_tasks = decompose(mission)
    state.status  = MissionStatus.ACTIVE
    _emit(state, WorkflowEventType.MISSION_DECOMPOSED,
          f"Decomposed into {len(initial_tasks)} initial tasks", cycle=0)

    for task in initial_tasks:
        state.tasks.append(task)
        _emit(state, WorkflowEventType.TASK_CREATED,
              f"{task.task_id} — {task.title} [{task.task_type.value} / {task.priority.value}]",
              task_id=task.task_id, cycle=0)

    state.tasks       = resolve_dependencies(state.tasks)
    state.priority_queue = rebuild_queue(state.tasks)

    # --- Mission loop -------------------------------------------------------
    for cycle in range(1, max_cycles + 1):
        state.cycle_count = cycle

        if not state.priority_queue:
            # Nothing ready — check if we're stuck
            in_progress = [t for t in state.tasks if t.status == TaskStatus.IN_PROGRESS]
            if not in_progress:
                state.status = MissionStatus.BLOCKED
                _emit(state, WorkflowEventType.WORKFLOW_REASSESSED,
                      "No READY tasks and nothing IN_PROGRESS — mission blocked", cycle=cycle)
                break
            continue

        # SELECT — pop the highest-priority task
        task_id = state.priority_queue.pop(0)
        task    = _get_task(state, task_id)
        if task is None or task.status != TaskStatus.READY:
            continue

        state.current_focus = task_id
        task = task.model_copy(update={"status": TaskStatus.IN_PROGRESS})
        _replace_task(state, task)
        _emit(state, WorkflowEventType.TASK_STARTED,
              f"{task_id} — {task.title}", task_id=task_id, cycle=cycle)
        _emit(state, WorkflowEventType.CAPABILITY_SELECTED,
              f"{task_id} → capability: {task.assigned_capability}", task_id=task_id, cycle=cycle)

        # EXECUTE
        result, error = _execute_task(task, _rag_fn, _agent_fn, _synth_fn)

        if error:
            task = task.model_copy(update={
                "status": TaskStatus.BLOCKED,
                "result": {"error": error},
            })
            _replace_task(state, task)
            _emit(state, WorkflowEventType.TASK_COMPLETED,
                  f"{task_id} FAILED — {error}", task_id=task_id, cycle=cycle)
            continue

        # OBSERVE — store result
        task = task.model_copy(update={
            "status": TaskStatus.COMPLETED,
            "result": result,
        })
        _replace_task(state, task)
        _emit(state, WorkflowEventType.TASK_COMPLETED,
              f"{task_id} completed successfully", task_id=task_id, cycle=cycle)

        # EXTRACT findings
        new_findings = _extract_findings(task, result)
        for finding in new_findings:
            if finding not in state.known_findings:
                state.known_findings.append(finding)
                _emit(state, WorkflowEventType.NEW_FINDING,
                      finding[:120], task_id=task_id, cycle=cycle)

        # ADAPT — apply rules, create new tasks, update priorities
        _adapt(state, task, result, cycle)

        # REPRIORITISE
        state.tasks          = resolve_dependencies(state.tasks)
        state.priority_queue = rebuild_queue(state.tasks)
        state.reassessment_count += 1
        _emit(state, WorkflowEventType.WORKFLOW_REASSESSED,
              f"Queue rebuilt: {state.priority_queue}", cycle=cycle)

        # CHECK completion
        if _check_completion(state):
            break

    else:
        # Exited via for-else (max_cycles exhausted)
        state.status = MissionStatus.MAX_CYCLES_REACHED

    # Final synthesis — always attempt when investigations are done, even if BLOCKED
    if state.status != MissionStatus.FAILED:
        _ensure_final_synthesis(state, _synth_fn, max_cycles)

    return state


# ---------------------------------------------------------------------------
# Completion check
# ---------------------------------------------------------------------------

def _check_completion(state: MissionState) -> bool:
    if not critical_and_high_complete(state.tasks):
        return False
    if not synthesis_complete(state.tasks):
        return False
    if len(state.known_findings) < 3:
        return False
    state.status = MissionStatus.READY_FOR_HUMAN_REVIEW
    _emit(state, WorkflowEventType.MISSION_READY_FOR_HUMAN_REVIEW,
          "All CRITICAL/HIGH tasks complete and synthesis done — ready for human review",
          cycle=state.cycle_count)
    return True


# ---------------------------------------------------------------------------
# Task execution — routes to the correct capability
# ---------------------------------------------------------------------------

def _execute_task(
    task:         Task,
    rag_fn:       Callable,
    agent_fn:     Callable,
    synthesis_fn: Callable,
) -> tuple[Any, Optional[str]]:
    """Execute the task via its assigned capability.  Returns (result, error)."""
    try:
        if task.assigned_capability == "agentic_rag":
            result = rag_fn(
                objective = task.objective,
                case_dir  = _CASE_DIR,
                max_hops  = 5,
            )
        elif task.assigned_capability in ("ai_agent", "synthesis"):
            if task.task_type == TaskType.SYNTHESIS:
                prompt = _build_synthesis_prompt(task.objective, [])
                result = synthesis_fn(prompt)
            else:
                result = agent_fn(assigned_task=task.objective)
        else:
            return None, f"Unknown capability: {task.assigned_capability}"
        return result, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


# ---------------------------------------------------------------------------
# Finding extraction
# ---------------------------------------------------------------------------

def _extract_findings(task: Task, result: Any) -> list[str]:
    """Pull human-readable finding strings from a capability result."""
    findings: list[str] = []

    if result is None:
        return findings

    # InvestigationResult (agentic_rag)
    conclusion = getattr(result, "archive_level_conclusion", None)
    if isinstance(conclusion, str) and conclusion:
        findings.append(f"[Archive] {conclusion}")

    for lead in getattr(result, "leads_discovered", []) or []:
        label   = getattr(lead, "label", "")
        context = getattr(lead, "context", "")
        if isinstance(label, str) and isinstance(context, str):
            findings.append(f"[Archive lead] {label}: {context}")

    for q in getattr(result, "requires_external_investigation", []) or []:
        if isinstance(q, str) and q not in findings:
            findings.append(f"[Requires external] {q}")

    # AgentState (ai_agent)
    for ev in getattr(result, "evidence", []) or []:
        fact  = getattr(ev, "fact", "")
        tool  = getattr(ev, "source_tool", "")
        conf  = getattr(ev, "confidence", "")
        if isinstance(fact, str) and fact:
            findings.append(f"[{tool} / {conf}] {fact}")

    summary = getattr(result, "completion_summary", None)
    if isinstance(summary, str) and summary:
        findings.append(f"[Agent summary] {summary}")

    # Synthesis (plain string)
    if isinstance(result, str) and result.strip():
        findings.append(f"[Synthesis] {result[:300]}")

    return findings


# ---------------------------------------------------------------------------
# Adaptation rules (deterministic, no ground-truth reads)
# ---------------------------------------------------------------------------

def _adapt(state: MissionState, completed_task: Task, result: Any, cycle: int) -> None:
    """Apply all adaptation rules after a task completes."""

    # Rule 0 — Archive complete → create bounded external tasks from real findings
    _rule_create_external_tasks_from_archive(state, completed_task, result, cycle)

    # Rule 1 — Surveillance evidence → new vehicle lookup task
    _rule_vehicle_lookup(state, completed_task, result, cycle)

    # Rule 2 — Vehicle keeper confirmed → elevate financial task
    _rule_elevate_financial(state, completed_task, result, cycle)

    # Rule 3 — Financial transfer recipient → new lead validation task
    _rule_financial_recipient(state, completed_task, result, cycle)

    # Rule 4 — Revoked/zero-event credential → deprioritise
    _rule_deprioritise_revoked_credential(state, completed_task, result, cycle)

    # Rule 5 — Commercial/eliminated vehicle → red herring task deprioritised
    _rule_eliminate_commercial_vehicle(state, completed_task, result, cycle)

    # Rule 6 — All investigative tasks done → unblock SYNTHESIS
    _rule_unblock_synthesis(state, cycle)


def _extend_synthesis_deps(state: MissionState, new_ids: list[str], cycle: int) -> None:
    """Add *new_ids* to every SYNTHESIS task's dependency list (no-op if already listed)."""
    for i, t in enumerate(state.tasks):
        if t.task_type != TaskType.SYNTHESIS:
            continue
        current_deps = list(t.dependencies or [])
        merged = list(dict.fromkeys(current_deps + new_ids))
        if set(merged) != set(current_deps):
            state.tasks[i] = t.model_copy(update={"dependencies": merged})
            _emit(
                state, WorkflowEventType.TASK_REPRIORITIZED,
                f"{t.task_id} dependencies extended — blocked on {new_ids}",
                task_id=t.task_id, cycle=cycle,
            )


def _rule_create_external_tasks_from_archive(
    state: MissionState, task: Task, result: Any, cycle: int
) -> None:
    """Rule 0: archive complete → create bounded external tasks from real RAG findings.

    Extracts case IDs, credentials, and person names from the actual
    InvestigationResult without hardcoding any Operation Nightfall facts.
    """
    if task.task_type != TaskType.ARCHIVE_INVESTIGATION:
        return
    if result is None:
        return

    # Collect all text surfaces to mine for entities
    conclusion = getattr(result, "archive_level_conclusion", "") or ""
    ev_texts: list[str] = [conclusion]
    for ev in getattr(result, "evidence_hits", []) or []:
        ev_texts.append(getattr(ev, "text", "") or "")
        ev_texts.append(getattr(ev, "content", "") or "")
    for q in getattr(result, "requires_external_investigation", []) or []:
        ev_texts.append(q if isinstance(q, str) else "")
    combined = " ".join(ev_texts)

    # Extract case IDs and credentials (de-duplicated, insertion-ordered)
    case_ids = list(dict.fromkeys(_CASE_ID_RE.findall(combined)))
    creds    = list(dict.fromkeys(_CRED_RE.findall(combined)))

    # Extract person names from leads_discovered two-part underscore labels
    person_names: list[str] = []
    for lead in getattr(result, "leads_discovered", []) or []:
        label = (getattr(lead, "label", "") or "").lower().replace("-", "_")
        parts = label.split("_")
        if len(parts) == 2:
            p0, p1 = parts
            if (
                p0 not in _NON_PERSON_PARTS
                and p1 not in _NON_PERSON_PARTS
                and p0.isalpha() and p1.isalpha()
                and len(p0) > 2 and len(p1) > 2
            ):
                name = f"{p0.capitalize()} {p1.capitalize()}"
                if name not in person_names:
                    person_names.append(name)

    created_ids: list[str] = []

    # Create ANPR surveillance task embedding all discovered case IDs
    if case_ids:
        case_list = ", ".join(case_ids[:4])
        surv_task = _create_task(
            state               = state,
            task_id             = f"T-{_next_task_num(state):03d}",
            title               = "ANPR Surveillance Review — Nightfall Incidents",
            objective           = (
                f"Query ANPR surveillance records for Operation Nightfall incidents"
                f" {case_list}. Identify any vehicles captured at the scenes and"
                f" determine whether any registration plates warrant further investigation."
            ),
            task_type           = TaskType.EXTERNAL_INVESTIGATION,
            priority            = Priority.HIGH,
            status              = TaskStatus.READY,
            dependencies        = [],
            assigned_capability = "ai_agent",
            reason              = (
                f"Archive identified {len(case_ids)} incident(s) requiring ANPR"
                f" surveillance cross-check (Rule 0)."
            ),
            created_from        = task.task_id,
            cycle               = cycle,
        )
        created_ids.append(surv_task.task_id)

    # Create access logs task embedding all discovered credentials
    if creds:
        cred_list = ", ".join(creds[:2])
        acc_task = _create_task(
            state               = state,
            task_id             = f"T-{_next_task_num(state):03d}",
            title               = f"Access Logs Review — {creds[0]}",
            objective           = (
                f"Query Northstar Facilities access logs for credential(s) {cred_list}."
                f" Determine who holds this credential and whether any access events"
                f" correspond to Operation Nightfall incident times."
            ),
            task_type           = TaskType.EXTERNAL_INVESTIGATION,
            priority            = Priority.HIGH,
            status              = TaskStatus.READY,
            dependencies        = [],
            assigned_capability = "ai_agent",
            reason              = (
                f"Archive identified credential(s) {cred_list} requiring"
                f" access log verification (Rule 0)."
            ),
            created_from        = task.task_id,
            cycle               = cycle,
        )
        created_ids.append(acc_task.task_id)

    # Create financial intelligence task per discovered person
    for name in person_names[:2]:
        fin_task = _create_task(
            state               = state,
            task_id             = f"T-{_next_task_num(state):03d}",
            title               = f"Financial Intelligence — {name}",
            objective           = (
                f"Query Financial Intelligence Unit records for {name}."
                f" Examine {name}'s financial activity in the period surrounding"
                f" the Operation Nightfall incidents for any unexplained transactions"
                f" or transfers that may indicate involvement."
            ),
            task_type           = TaskType.EXTERNAL_INVESTIGATION,
            priority            = Priority.HIGH,
            status              = TaskStatus.READY,
            dependencies        = [],
            assigned_capability = "ai_agent",
            reason              = (
                f"Archive identified {name} as a lead requiring financial"
                f" intelligence verification (Rule 0)."
            ),
            created_from        = task.task_id,
            cycle               = cycle,
        )
        created_ids.append(fin_task.task_id)

    # Extend T-002 dependencies so synthesis stays BLOCKED until all external tasks finish
    if created_ids:
        _extend_synthesis_deps(state, created_ids, cycle)


def _rule_vehicle_lookup(state: MissionState, task: Task, result: Any, cycle: int) -> None:
    """Rule 1: if surveillance returned a registration → create vehicle lookup task."""
    if task.task_type not in (TaskType.EXTERNAL_INVESTIGATION, TaskType.LEAD_VALIDATION):
        return
    if not hasattr(result, "observations"):
        return

    existing_plates = _plates_already_scheduled(state)
    for obs in result.observations:
        if obs.tool_name != "query_surveillance" or obs.status != "success":
            continue
        for sighting in (obs.result or {}).get("sightings", []):
            plate = sighting.get("registration_plate")
            if plate and sighting.get("registration_captured") and plate not in existing_plates:
                # Surveillance-eliminated vehicles still get a lookup task but at LOW
                # priority — Rule 5 will deprioritise when vehicle records confirm.
                not_of_interest = sighting.get("vehicle_of_interest") is False
                lookup_priority = Priority.LOW if not_of_interest else Priority.CRITICAL
                new_task = _create_task(
                    state    = state,
                    task_id  = f"T-{_next_task_num(state):03d}",
                    title    = f"Vehicle Records Lookup — {plate}",
                    objective = (
                        f"Identify the registered keeper of vehicle {plate}"
                        f" using DVLA vehicle registration records."
                    ),
                    task_type           = TaskType.LEAD_VALIDATION,
                    priority            = lookup_priority,
                    status              = TaskStatus.READY,
                    dependencies        = [],
                    assigned_capability = "ai_agent",
                    reason              = (
                        f"Surveillance confirmed {plate} at an Operation Nightfall"
                        f" scene (Rule 1 — registration_captured=True"
                        + (", pre-eliminated by surveillance" if not_of_interest else "")
                        + ")."
                    ),
                    created_from = task.task_id,
                    cycle        = cycle,
                )
                _extend_synthesis_deps(state, [new_task.task_id], cycle)
                existing_plates.add(plate)


def _rule_elevate_financial(state: MissionState, task: Task, result: Any, cycle: int) -> None:
    """Rule 2: vehicle keeper matches a person → elevate financial task to CRITICAL."""
    if not hasattr(result, "evidence"):
        return
    keepers = _extract_vehicle_keepers(result)
    if not keepers:
        return

    for t in state.tasks:
        if t.task_type in (TaskType.EXTERNAL_INVESTIGATION, TaskType.LEAD_VALIDATION):
            obj_lower = t.objective.lower()
            if "financial" in obj_lower or "fiu" in obj_lower:
                for keeper in keepers:
                    if keeper.lower() in obj_lower and t.priority != Priority.CRITICAL:
                        reason = f"Vehicle keeper {keeper!r} confirmed — financial task elevated (Rule 2)"
                        state.tasks = elevate_priority(
                            state.tasks, t.task_id, Priority.CRITICAL, reason, cycle
                        )
                        _emit(state, WorkflowEventType.TASK_REPRIORITIZED,
                              f"{t.task_id} elevated to CRITICAL — {reason}",
                              task_id=t.task_id, cycle=cycle)


def _rule_financial_recipient(state: MissionState, task: Task, result: Any, cycle: int) -> None:
    """Rule 3: financial result shows a transfer recipient → new lead validation task."""
    if task.task_type not in (TaskType.EXTERNAL_INVESTIGATION, TaskType.LEAD_VALIDATION):
        return
    if not hasattr(result, "observations"):
        return

    existing_subjects = _lead_validation_subjects(state)
    for obs in result.observations:
        if obs.tool_name != "query_financial_intelligence" or obs.status != "success":
            continue
        # Financial tool returns 'transactions' list; scan for outbound transfers.
        # Also check legacy 'transfers_out' key for forward compatibility.
        transfers: list[dict] = []
        for txn in (obs.result or {}).get("transactions", []):
            if "outbound" in txn.get("type", "").lower() and txn.get("recipient_name"):
                transfers.append({"recipient_name": txn["recipient_name"]})
        for t in (obs.result or {}).get("transfers_out", []):
            transfers.append(t)

        for transfer in transfers:
            recipient = transfer.get("recipient_name", "")
            if recipient and recipient not in existing_subjects:
                lead_task = _create_task(
                    state               = state,
                    task_id             = f"T-{_next_task_num(state):03d}",
                    title               = f"Lead Validation — {recipient}",
                    objective           = (
                        f"Investigate the financial connection between the primary"
                        f" suspect and {recipient} in relation to Operation Nightfall."
                        f" Review {recipient}'s financial activity for incoming transfers"
                        f" and any transactions connected to the incident period."
                    ),
                    task_type           = TaskType.LEAD_VALIDATION,
                    priority            = Priority.HIGH,
                    status              = TaskStatus.READY,
                    dependencies        = [],
                    assigned_capability = "ai_agent",
                    reason              = (
                        f"Financial intelligence identified {recipient} as a transfer"
                        f" recipient with no formal arrangement (Rule 3)."
                    ),
                    created_from = task.task_id,
                    cycle        = cycle,
                )
                _extend_synthesis_deps(state, [lead_task.task_id], cycle)
                existing_subjects.add(recipient)


def _rule_deprioritise_revoked_credential(
    state: MissionState, task: Task, result: Any, cycle: int
) -> None:
    """Rule 4: access logs show revoked credential with zero relevant events → deprioritise."""
    if not hasattr(result, "observations"):
        return
    for obs in result.observations:
        if obs.tool_name != "query_access_logs" or obs.status != "success":
            continue
        r = obs.result or {}
        if r.get("credential_status") == "REVOKED" and r.get("relevant_events", 1) == 0:
            cred = r.get("credential_id", "")
            for t in state.tasks:
                if cred and cred in t.objective and t.status not in (
                    TaskStatus.COMPLETED, TaskStatus.DEPRIORITIZED
                ):
                    reason = f"Credential {cred} is REVOKED with zero relevant access events (Rule 4)"
                    state.tasks = deprioritize(state.tasks, t.task_id, reason, cycle)
                    _emit(state, WorkflowEventType.TASK_DEPRIORITIZED,
                          f"{t.task_id} deprioritised — {reason}",
                          task_id=t.task_id, cycle=cycle)


def _rule_eliminate_commercial_vehicle(
    state: MissionState, task: Task, result: Any, cycle: int
) -> None:
    """Rule 5: vehicle confirmed commercial/legitimate → eliminate, create RED_HERRING task."""
    if not hasattr(result, "observations"):
        return
    for obs in result.observations:
        if obs.tool_name != "lookup_vehicle" or obs.status != "success":
            continue
        r          = obs.result or {}
        confidence = r.get("confidence", "")
        plate      = r.get("registration", "")
        keeper     = r.get("registered_keeper", "")
        is_eliminated = (
            "ELIMINATED" in str(confidence).upper()
            or any(ind in keeper for ind in _COMMERCIAL_INDICATORS)
        )
        if is_eliminated and plate:
            existing_rh = {t.title for t in state.tasks if t.task_type == TaskType.RED_HERRING_VALIDATION}
            title = f"Red Herring — {plate}"
            if title not in existing_rh:
                rh_task = _create_task(
                    state               = state,
                    task_id             = f"T-{_next_task_num(state):03d}",
                    title               = title,
                    objective           = f"Document that {plate} is a legitimate commercial vehicle.",
                    task_type           = TaskType.RED_HERRING_VALIDATION,
                    priority            = Priority.LOW,
                    status              = TaskStatus.DEPRIORITIZED,
                    dependencies        = [],
                    assigned_capability = "ai_agent",
                    reason              = (
                        f"Vehicle {plate} confirmed as commercial/eliminated (Rule 5)."
                    ),
                    created_from = task.task_id,
                    cycle        = cycle,
                )
                _emit(state, WorkflowEventType.TASK_DEPRIORITIZED,
                      f"{rh_task.task_id} immediately deprioritised — {plate} is eliminated",
                      task_id=rh_task.task_id, cycle=cycle)


def _rule_unblock_synthesis(state: MissionState, cycle: int) -> None:
    """Rule 6: when all investigative tasks are done → unblock SYNTHESIS if still BLOCKED."""
    investigative_types = {
        TaskType.ARCHIVE_INVESTIGATION,
        TaskType.EXTERNAL_INVESTIGATION,
        TaskType.LEAD_VALIDATION,
    }
    for task in state.tasks:
        if task.task_type not in investigative_types:
            continue
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.DEPRIORITIZED):
            return

    # All investigative tasks done — clear synthesis dependencies
    for i, task in enumerate(state.tasks):
        if task.task_type == TaskType.SYNTHESIS and task.status == TaskStatus.BLOCKED:
            state.tasks[i] = task.model_copy(update={
                "status":       TaskStatus.READY,
                "dependencies": [],
            })
            _emit(state, WorkflowEventType.TASK_REPRIORITIZED,
                  f"{task.task_id} unblocked — all investigative tasks complete (Rule 6)",
                  task_id=task.task_id, cycle=cycle)


# ---------------------------------------------------------------------------
# Synthesis prompt builder
# ---------------------------------------------------------------------------

def _build_synthesis_prompt(objective: str, findings: list[str]) -> str:
    joined = "\n".join(f"- {f}" for f in findings) if findings else "(no findings yet)"
    return (
        "You are a senior police analyst reviewing an AI-assisted investigation.\n\n"
        f"Mission objective: {objective}\n\n"
        "Confirmed findings from archive and external investigations:\n"
        f"{joined}\n\n"
        "Produce a concise, factual investigation assessment:\n"
        "1. Summarise the key evidence links between the incidents.\n"
        "2. Identify the strongest person(s) of interest and the evidence supporting that conclusion.\n"
        "3. Identify any secondary persons of interest.\n"
        "4. Note any significant open questions that require further investigation.\n"
        "5. Use language appropriate for a preliminary assessment: 'person of interest',"
        " 'warrants further investigation', 'human review required'.\n"
        "Do NOT claim guilt, issue warrants, or recommend arrest."
    )


def _ensure_final_synthesis(
    state:        MissionState,
    synthesis_fn: Callable,
    max_cycles:   int,
) -> None:
    """If synthesis task is COMPLETED, set final_assessment and close the mission.

    If synthesis hasn't run yet, attempt it now.  If the LLM is unavailable,
    build a fallback summary from known_findings so the mission always reaches
    READY_FOR_HUMAN_REVIEW when investigations are done.
    """
    # Case 1 — synthesis already completed during the main loop
    for task in state.tasks:
        if task.task_type == TaskType.SYNTHESIS and task.status == TaskStatus.COMPLETED:
            if isinstance(task.result, str):
                state.final_assessment = task.result
            state.status = MissionStatus.READY_FOR_HUMAN_REVIEW
            return

    # Only proceed if at least the archive investigation is done
    investigative_types = {
        TaskType.ARCHIVE_INVESTIGATION,
        TaskType.EXTERNAL_INVESTIGATION,
        TaskType.LEAD_VALIDATION,
    }
    all_done = all(
        t.status in (TaskStatus.COMPLETED, TaskStatus.DEPRIORITIZED)
        for t in state.tasks
        if t.task_type in investigative_types
    )
    if not all_done and not state.known_findings:
        return  # investigations still running — nothing to synthesise

    # Case 2 — synthesis not yet run (READY or BLOCKED) — attempt it now
    for task in state.tasks:
        if task.task_type == TaskType.SYNTHESIS:
            prompt = _build_synthesis_prompt(task.objective, state.known_findings)
            text: str
            try:
                text = synthesis_fn(prompt)
            except Exception:  # noqa: BLE001 — LLM unavailable, use fallback
                text = _fallback_assessment(state.known_findings)
            updated = task.model_copy(update={
                "status": TaskStatus.COMPLETED,
                "result": text,
            })
            _replace_task(state, updated)
            state.final_assessment = text
            state.status           = MissionStatus.READY_FOR_HUMAN_REVIEW
            return

    # Case 3 — no synthesis task at all (should not happen, but be safe)
    if state.known_findings:
        state.final_assessment = _fallback_assessment(state.known_findings)
        state.status           = MissionStatus.READY_FOR_HUMAN_REVIEW


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emit(
    state:      MissionState,
    event_type: WorkflowEventType,
    summary:    str,
    task_id:    Optional[str] = None,
    cycle:      int           = 0,
) -> None:
    state.workflow_events.append(WorkflowEvent(
        event_type = event_type,
        summary    = summary,
        task_id    = task_id,
        cycle      = cycle,
        timestamp  = datetime.now(timezone.utc).isoformat(),
    ))


def _get_task(state: MissionState, task_id: str) -> Optional[Task]:
    for t in state.tasks:
        if t.task_id == task_id:
            return t
    return None


def _replace_task(state: MissionState, updated: Task) -> None:
    state.tasks = [updated if t.task_id == updated.task_id else t for t in state.tasks]


def _next_task_num(state: MissionState) -> int:
    return len(state.tasks) + 1


def _create_task(
    state: MissionState,
    cycle: int,
    **kwargs: Any,
) -> Task:
    task = Task(
        priority_history = [f"{kwargs['priority']} (cycle {cycle} — {kwargs['reason']})"],
        evidence_refs    = [],
        **{k: v for k, v in kwargs.items() if k not in ("priority_history", "evidence_refs")},
    )
    state.tasks.append(task)
    _emit(state, WorkflowEventType.TASK_CREATED_FROM_FINDING,
          f"{task.task_id} — {task.title} [{task.task_type.value} / {task.priority.value}]",
          task_id=task.task_id, cycle=cycle)
    return task


def _plates_already_scheduled(state: MissionState) -> set[str]:
    plates: set[str] = set()
    for task in state.tasks:
        plates.update(_PLATE_RE.findall(task.objective))
    return plates


def _extract_vehicle_keepers(result: Any) -> list[str]:
    keepers: list[str] = []
    if not hasattr(result, "evidence"):
        return keepers
    for ev in result.evidence:
        if ev.source_tool == "lookup_vehicle":
            m = re.search(r"registered to ([A-Z][a-z]+ [A-Z][a-z]+)", ev.fact)
            if m:
                keepers.append(m.group(1))
    return keepers


def _lead_validation_subjects(state: MissionState) -> set[str]:
    subjects: set[str] = set()
    for task in state.tasks:
        if task.task_type == TaskType.LEAD_VALIDATION:
            subjects.update(_NAME_RE.findall(task.title))
    return subjects


# ---------------------------------------------------------------------------
# Fallback assessment (used when LLM synthesis is unavailable)
# ---------------------------------------------------------------------------

def _fallback_assessment(findings: list[str]) -> str:
    archive  = [f for f in findings if f.startswith("[Archive]")]
    leads    = [f for f in findings if f.startswith("[Archive lead]")]
    external = [f for f in findings if f.startswith("[") and "external" in f.lower()]

    lines = [
        "INVESTIGATION ASSESSMENT — Operation Nightfall",
        "(Synthesised from confirmed findings — human analyst review required)\n",
    ]
    if archive:
        lines.append("Archive findings:")
        lines.extend(f"  • {f[9:]}" for f in archive)
    if leads:
        lines.append("\nLeads requiring further investigation:")
        lines.extend(f"  • {f}" for f in leads[:6])
    if external:
        lines.append("\nExternal investigation requirements identified:")
        lines.extend(f"  • {f}" for f in external[:4])
    if not archive and not leads and not external and findings:
        lines.append("Findings gathered during investigation:")
        lines.extend(f"  • {f}" for f in findings[:8])
    lines.append(
        "\nThis assessment is based on confirmed archive evidence and external"
        " observations. All persons named are persons of interest only."
        " No conclusions of guilt are drawn. Human detective review is required"
        " before any further action."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Default capability implementations (use real services)
# ---------------------------------------------------------------------------

def _default_rag(objective: str, case_dir: str, max_hops: int = 5) -> Any:
    from services.agentic_rag import investigate
    return investigate(objective=objective, case_dir=case_dir, max_hops=max_hops)


def _default_agent(assigned_task: str) -> Any:
    from services.ai_agent import run_investigation
    return run_investigation(assigned_task=assigned_task)


def _default_synthesis(prompt: str) -> str:
    from services.llm.client import generate_grounded_answer
    return generate_grounded_answer(prompt)
