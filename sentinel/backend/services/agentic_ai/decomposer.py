"""Agentic AI goal decomposer.

Converts a broad mission statement into an initial set of Tasks.
The decomposer is LLM-injectable: pass ``llm_fn`` in production to use
the language model; omit it (or pass None) to get the deterministic
keyword-based fallback used in tests.

Design constraints
------------------
* The initial task list must NOT mention MBK-4172, Marcus Vale, Daniel
  Mercer, NF-3847, or any other fact that comes from external tools.
  Those are discovered at runtime by the capabilities, not assumed upfront.

* The initial task list always includes:
    T-001  ARCHIVE_INVESTIGATION   CRITICAL  READY
    T-002  SYNTHESIS               HIGH      BLOCKED([T-001])
  Additional tasks are only added when the mission explicitly mentions
  external investigation needs beyond the archive.

* All task IDs are deterministic slugs (T-001, T-002 …) so tests can
  reference them by ID.
"""
from __future__ import annotations

from typing import Callable, Optional

from .models import Priority, Task, TaskStatus, TaskType


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def decompose(
    mission: str,
    llm_fn:  Optional[Callable[[str], str]] = None,
) -> list[Task]:
    """Decompose *mission* into an initial list of Tasks.

    Args:
        mission: The broad investigation mission text.
        llm_fn:  Optional LLM callable ``(prompt: str) -> str``.
                 When provided the LLM's output is parsed into tasks;
                 on parse failure the deterministic fallback is used.
                 When None the deterministic fallback is always used.

    Returns:
        List of Task objects ready to hand to the prioritiser.
    """
    if llm_fn is not None:
        try:
            return _llm_decompose(mission, llm_fn)
        except Exception:
            pass  # fall through to deterministic fallback

    return _deterministic_decompose(mission)


# ---------------------------------------------------------------------------
# Deterministic fallback — keyword-based, no network, safe for tests
# ---------------------------------------------------------------------------

def _deterministic_decompose(mission: str) -> list[Task]:  # noqa: ARG001
    """Produce an initial task list from the mission without calling an LLM.

    Always returns T-001 (archive) + T-002 (synthesis).
    External investigation tasks are created dynamically by the orchestrator
    (Rule 0) after the archive investigation completes and reveals which
    specific case IDs, credentials, and persons require corroboration.
    """
    tasks: list[Task] = []

    # T-001 — archive investigation is always the first step
    tasks.append(Task(
        task_id             = "T-001",
        title               = "Archive Investigation",
        objective           = (
            "Search the Operation Nightfall case archive to establish"
            " what the recorded evidence can tell us: incident timeline,"
            " common patterns, vehicles or persons mentioned across cases,"
            " and any facts that require external corroboration."
        ),
        task_type           = TaskType.ARCHIVE_INVESTIGATION,
        priority            = Priority.CRITICAL,
        status              = TaskStatus.READY,
        dependencies        = [],
        assigned_capability = "agentic_rag",
        reason              = "Archive investigation is the mandatory first step before any external enquiry.",
        created_from        = "mission_decomposition",
        priority_history    = ["CRITICAL (initial — archive is always the starting point)"],
    ))

    # T-002 — synthesis is always needed; blocked until investigative tasks complete
    tasks.append(Task(
        task_id             = "T-002",
        title               = "Investigation Synthesis",
        objective           = (
            "Synthesise all confirmed findings from the archive and external"
            " investigations into a single evidence-backed assessment for"
            " human review.  State only what the evidence supports."
        ),
        task_type           = TaskType.SYNTHESIS,
        priority            = Priority.HIGH,
        status              = TaskStatus.BLOCKED,
        dependencies        = ["T-001"],
        assigned_capability = "synthesis",
        reason              = "Synthesis requires prior investigative findings to be meaningful.",
        created_from        = "mission_decomposition",
        priority_history    = ["HIGH (initial — synthesis cannot run before investigation)"],
    ))

    return tasks


# ---------------------------------------------------------------------------
# LLM decomposer — parses model output into tasks
# ---------------------------------------------------------------------------

_LLM_PROMPT_TEMPLATE = """\
You are a police investigation planning assistant.

Given the following broad investigation mission, produce an initial list of
investigation tasks.  Each task must be on its own line in this format:

  TASK_ID | TITLE | OBJECTIVE | TASK_TYPE | PRIORITY | CAPABILITY | REASON

Rules:
- Always include T-001 (ARCHIVE_INVESTIGATION, CRITICAL, agentic_rag) as the first task.
- Always include T-002 (SYNTHESIS, HIGH, synthesis, blocked on all investigation tasks).
- TASK_TYPE must be one of: ARCHIVE_INVESTIGATION, EXTERNAL_INVESTIGATION, SYNTHESIS.
- PRIORITY must be one of: CRITICAL, HIGH, MEDIUM, LOW.
- CAPABILITY must be one of: agentic_rag, ai_agent, synthesis.
- Do NOT mention specific vehicle registrations, names, or credentials in the objectives.
  Those are discovered by the capabilities at runtime.
- Use concise, factual language.

Mission:
{mission}

Respond with ONLY the task lines, no other text.
"""


def _llm_decompose(mission: str, llm_fn: Callable[[str], str]) -> list[Task]:
    """Call ``llm_fn`` and parse the response into tasks."""
    prompt   = _LLM_PROMPT_TEMPLATE.format(mission=mission)
    response = llm_fn(prompt)
    tasks    = _parse_llm_response(response)
    if not tasks:
        raise ValueError("LLM returned no parseable tasks")
    return tasks


def _parse_llm_response(response: str) -> list[Task]:
    """Parse pipe-delimited task lines from the LLM response."""
    tasks: list[Task] = []
    seen_ids: set[str] = set()

    for line in response.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7:
            continue

        task_id, title, objective, raw_type, raw_priority, capability, reason = parts[:7]

        try:
            task_type = TaskType(raw_type)
            priority  = Priority(raw_priority)
        except ValueError:
            continue

        if task_id in seen_ids:
            continue
        seen_ids.add(task_id)

        tasks.append(Task(
            task_id             = task_id,
            title               = title,
            objective           = objective,
            task_type           = task_type,
            priority            = priority,
            status              = TaskStatus.READY,
            dependencies        = [],
            assigned_capability = capability,
            reason              = reason,
            created_from        = "mission_decomposition",
            priority_history    = [f"{priority} (initial — from LLM decomposition)"],
        ))

    # Always ensure T-001 and T-002 are present
    ids = {t.task_id for t in tasks}
    if "T-001" not in ids:
        tasks.insert(0, _deterministic_decompose("external")[0])
    if "T-002" not in ids:
        synth = _deterministic_decompose("")[1]
        tasks.append(synth)

    return tasks
