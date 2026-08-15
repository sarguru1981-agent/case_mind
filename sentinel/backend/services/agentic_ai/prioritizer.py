"""Agentic AI task prioritiser — pure deterministic logic, no I/O.

Responsibilities:
  1. resolve_dependencies  — promote BLOCKED tasks whose deps are all COMPLETED
  2. rebuild_queue         — ordered list of task_ids for tasks that are READY
  3. elevate_priority      — raise a task's priority with audit trail
  4. deprioritize          — mark a task DEPRIORITIZED with reason

Priority order (highest first): CRITICAL > HIGH > MEDIUM > LOW
Within the same priority, tasks are ordered by task_id (T-001, T-002 …)
to give deterministic, reproducible ordering.
"""
from __future__ import annotations

from .models import Priority, Task, TaskStatus, priority_rank


# ---------------------------------------------------------------------------
# Dependency resolution
# ---------------------------------------------------------------------------

def resolve_dependencies(tasks: list[Task]) -> list[Task]:
    """Promote BLOCKED tasks to READY when all their dependencies are COMPLETED.

    Does NOT modify the input list.  Returns a new list with updated statuses.
    """
    completed_ids = {t.task_id for t in tasks if t.status == TaskStatus.COMPLETED}
    updated: list[Task] = []
    for task in tasks:
        if task.status == TaskStatus.BLOCKED:
            if all(dep in completed_ids for dep in task.dependencies):
                task = task.model_copy(update={"status": TaskStatus.READY})
        updated.append(task)
    return updated


# ---------------------------------------------------------------------------
# Queue builder
# ---------------------------------------------------------------------------

def rebuild_queue(tasks: list[Task]) -> list[str]:
    """Return task_ids of READY tasks ordered by priority then task_id.

    Only READY tasks are included.  IN_PROGRESS, BLOCKED, COMPLETED, and
    DEPRIORITIZED tasks are excluded.
    """
    ready = [t for t in tasks if t.status == TaskStatus.READY]
    ready.sort(key=lambda t: (priority_rank(t.priority), t.task_id))
    return [t.task_id for t in ready]


# ---------------------------------------------------------------------------
# Priority mutation helpers
# ---------------------------------------------------------------------------

def elevate_priority(
    tasks:      list[Task],
    task_id:    str,
    new_priority: Priority,
    reason:     str,
    cycle:      int,
) -> list[Task]:
    """Raise *task_id*'s priority to *new_priority* (no-op if already higher).

    Appends a history entry and returns a new list.
    """
    updated: list[Task] = []
    for task in tasks:
        if task.task_id == task_id:
            if priority_rank(new_priority) < priority_rank(task.priority):
                history = list(task.priority_history) + [
                    f"{new_priority} (cycle {cycle} — {reason})"
                ]
                task = task.model_copy(update={
                    "priority":         new_priority,
                    "priority_history": history,
                })
        updated.append(task)
    return updated


def deprioritize(
    tasks:   list[Task],
    task_id: str,
    reason:  str,
    cycle:   int,
) -> list[Task]:
    """Mark *task_id* as DEPRIORITIZED with an audit entry."""
    updated: list[Task] = []
    for task in tasks:
        if task.task_id == task_id and task.status not in (
            TaskStatus.COMPLETED, TaskStatus.DEPRIORITIZED
        ):
            history = list(task.priority_history) + [
                f"DEPRIORITIZED (cycle {cycle} — {reason})"
            ]
            task = task.model_copy(update={
                "status":           TaskStatus.DEPRIORITIZED,
                "priority_history": history,
            })
        updated.append(task)
    return updated


# ---------------------------------------------------------------------------
# Completion check
# ---------------------------------------------------------------------------

def critical_and_high_complete(tasks: list[Task]) -> bool:
    """True when every CRITICAL and HIGH priority task is COMPLETED."""
    for task in tasks:
        if task.priority in (Priority.CRITICAL, Priority.HIGH):
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.DEPRIORITIZED):
                return False
    return True


def synthesis_complete(tasks: list[Task]) -> bool:
    """True when the SYNTHESIS task is COMPLETED."""
    for task in tasks:
        if task.task_type.value == "SYNTHESIS":
            if task.status == TaskStatus.COMPLETED:
                return True
    return False
