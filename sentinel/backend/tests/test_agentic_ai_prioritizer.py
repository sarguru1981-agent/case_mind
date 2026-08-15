"""Tests for agentic_ai.prioritizer — pure deterministic logic."""
import pytest

from services.agentic_ai.models import Priority, Task, TaskStatus, TaskType
from services.agentic_ai.prioritizer import (
    critical_and_high_complete,
    deprioritize,
    elevate_priority,
    rebuild_queue,
    resolve_dependencies,
    synthesis_complete,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task(
    task_id:    str,
    priority:   Priority   = Priority.MEDIUM,
    status:     TaskStatus = TaskStatus.READY,
    deps:       list[str]  = None,
    task_type:  TaskType   = TaskType.ARCHIVE_INVESTIGATION,
    capability: str        = "agentic_rag",
) -> Task:
    return Task(
        task_id             = task_id,
        title               = task_id,
        objective           = f"Objective for {task_id}",
        task_type           = task_type,
        priority            = priority,
        status              = status,
        dependencies        = deps or [],
        assigned_capability = capability,
        reason              = "test",
        created_from        = "test",
    )


# ---------------------------------------------------------------------------
# resolve_dependencies
# ---------------------------------------------------------------------------

class TestResolveDependencies:
    def test_no_deps_stays_ready(self):
        tasks   = [_task("T-001", status=TaskStatus.READY)]
        updated = resolve_dependencies(tasks)
        assert updated[0].status == TaskStatus.READY

    def test_blocked_with_completed_dep_becomes_ready(self):
        tasks = [
            _task("T-001", status=TaskStatus.COMPLETED),
            _task("T-002", status=TaskStatus.BLOCKED, deps=["T-001"]),
        ]
        updated = resolve_dependencies(tasks)
        t002    = next(t for t in updated if t.task_id == "T-002")
        assert t002.status == TaskStatus.READY

    def test_blocked_with_incomplete_dep_stays_blocked(self):
        tasks = [
            _task("T-001", status=TaskStatus.IN_PROGRESS),
            _task("T-002", status=TaskStatus.BLOCKED, deps=["T-001"]),
        ]
        updated = resolve_dependencies(tasks)
        t002    = next(t for t in updated if t.task_id == "T-002")
        assert t002.status == TaskStatus.BLOCKED

    def test_multi_dep_all_complete_unblocks(self):
        tasks = [
            _task("T-001", status=TaskStatus.COMPLETED),
            _task("T-002", status=TaskStatus.COMPLETED),
            _task("T-003", status=TaskStatus.BLOCKED, deps=["T-001", "T-002"]),
        ]
        updated = resolve_dependencies(tasks)
        t003    = next(t for t in updated if t.task_id == "T-003")
        assert t003.status == TaskStatus.READY

    def test_multi_dep_partial_stays_blocked(self):
        tasks = [
            _task("T-001", status=TaskStatus.COMPLETED),
            _task("T-002", status=TaskStatus.READY),
            _task("T-003", status=TaskStatus.BLOCKED, deps=["T-001", "T-002"]),
        ]
        updated = resolve_dependencies(tasks)
        t003    = next(t for t in updated if t.task_id == "T-003")
        assert t003.status == TaskStatus.BLOCKED

    def test_does_not_mutate_input(self):
        tasks  = [_task("T-001", status=TaskStatus.BLOCKED, deps=["T-999"])]
        before = tasks[0].status
        resolve_dependencies(tasks)
        assert tasks[0].status == before


# ---------------------------------------------------------------------------
# rebuild_queue
# ---------------------------------------------------------------------------

class TestRebuildQueue:
    def test_empty_when_no_ready_tasks(self):
        tasks = [
            _task("T-001", status=TaskStatus.BLOCKED),
            _task("T-002", status=TaskStatus.COMPLETED),
        ]
        assert rebuild_queue(tasks) == []

    def test_single_ready_task(self):
        tasks = [_task("T-001", status=TaskStatus.READY)]
        assert rebuild_queue(tasks) == ["T-001"]

    def test_priority_ordering_critical_first(self):
        tasks = [
            _task("T-003", priority=Priority.LOW,      status=TaskStatus.READY),
            _task("T-001", priority=Priority.CRITICAL,  status=TaskStatus.READY),
            _task("T-002", priority=Priority.HIGH,      status=TaskStatus.READY),
        ]
        queue = rebuild_queue(tasks)
        assert queue[0] == "T-001"
        assert queue[1] == "T-002"
        assert queue[2] == "T-003"

    def test_same_priority_sorted_by_task_id(self):
        tasks = [
            _task("T-003", priority=Priority.HIGH, status=TaskStatus.READY),
            _task("T-001", priority=Priority.HIGH, status=TaskStatus.READY),
            _task("T-002", priority=Priority.HIGH, status=TaskStatus.READY),
        ]
        queue = rebuild_queue(tasks)
        assert queue == ["T-001", "T-002", "T-003"]

    def test_excludes_in_progress(self):
        tasks = [
            _task("T-001", status=TaskStatus.IN_PROGRESS),
            _task("T-002", status=TaskStatus.READY),
        ]
        assert rebuild_queue(tasks) == ["T-002"]

    def test_excludes_deprioritized(self):
        tasks = [
            _task("T-001", status=TaskStatus.DEPRIORITIZED),
            _task("T-002", status=TaskStatus.READY),
        ]
        assert rebuild_queue(tasks) == ["T-002"]


# ---------------------------------------------------------------------------
# elevate_priority
# ---------------------------------------------------------------------------

class TestElevatePriority:
    def test_elevates_lower_to_higher(self):
        tasks   = [_task("T-001", priority=Priority.MEDIUM)]
        updated = elevate_priority(tasks, "T-001", Priority.CRITICAL, "test", cycle=1)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert t001.priority == Priority.CRITICAL

    def test_no_op_when_already_higher(self):
        tasks   = [_task("T-001", priority=Priority.CRITICAL)]
        updated = elevate_priority(tasks, "T-001", Priority.HIGH, "test", cycle=1)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert t001.priority == Priority.CRITICAL

    def test_audit_entry_added(self):
        tasks   = [_task("T-001", priority=Priority.LOW)]
        updated = elevate_priority(tasks, "T-001", Priority.HIGH, "reason X", cycle=3)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert any("reason X" in h for h in t001.priority_history)
        assert any("cycle 3" in h for h in t001.priority_history)

    def test_unknown_task_id_is_noop(self):
        tasks   = [_task("T-001")]
        updated = elevate_priority(tasks, "T-999", Priority.CRITICAL, "x", cycle=1)
        assert updated[0].task_id == "T-001"


# ---------------------------------------------------------------------------
# deprioritize
# ---------------------------------------------------------------------------

class TestDeprioritize:
    def test_marks_task_deprioritized(self):
        tasks   = [_task("T-001", status=TaskStatus.READY)]
        updated = deprioritize(tasks, "T-001", "irrelevant", cycle=2)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert t001.status == TaskStatus.DEPRIORITIZED

    def test_audit_entry_added(self):
        tasks   = [_task("T-001")]
        updated = deprioritize(tasks, "T-001", "red herring confirmed", cycle=4)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert any("red herring confirmed" in h for h in t001.priority_history)

    def test_completed_task_not_touched(self):
        tasks   = [_task("T-001", status=TaskStatus.COMPLETED)]
        updated = deprioritize(tasks, "T-001", "reason", cycle=1)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert t001.status == TaskStatus.COMPLETED

    def test_already_deprioritized_not_double_marked(self):
        tasks   = [_task("T-001", status=TaskStatus.DEPRIORITIZED)]
        updated = deprioritize(tasks, "T-001", "reason", cycle=1)
        t001    = next(t for t in updated if t.task_id == "T-001")
        assert t001.status == TaskStatus.DEPRIORITIZED


# ---------------------------------------------------------------------------
# Completion checks
# ---------------------------------------------------------------------------

class TestCompletionChecks:
    def test_critical_and_high_complete_when_all_done(self):
        tasks = [
            _task("T-001", priority=Priority.CRITICAL, status=TaskStatus.COMPLETED),
            _task("T-002", priority=Priority.HIGH,     status=TaskStatus.COMPLETED),
            _task("T-003", priority=Priority.LOW,      status=TaskStatus.READY),
        ]
        assert critical_and_high_complete(tasks) is True

    def test_critical_and_high_not_complete_when_one_pending(self):
        tasks = [
            _task("T-001", priority=Priority.CRITICAL, status=TaskStatus.COMPLETED),
            _task("T-002", priority=Priority.HIGH,     status=TaskStatus.READY),
        ]
        assert critical_and_high_complete(tasks) is False

    def test_deprioritized_counts_as_done(self):
        tasks = [
            _task("T-001", priority=Priority.CRITICAL, status=TaskStatus.COMPLETED),
            _task("T-002", priority=Priority.HIGH,     status=TaskStatus.DEPRIORITIZED),
        ]
        assert critical_and_high_complete(tasks) is True

    def test_synthesis_complete_when_synthesis_done(self):
        tasks = [
            _task("T-001", task_type=TaskType.SYNTHESIS, status=TaskStatus.COMPLETED),
        ]
        assert synthesis_complete(tasks) is True

    def test_synthesis_not_complete_when_not_done(self):
        tasks = [
            _task("T-001", task_type=TaskType.SYNTHESIS, status=TaskStatus.READY),
        ]
        assert synthesis_complete(tasks) is False

    def test_synthesis_not_complete_with_no_synthesis_task(self):
        tasks = [
            _task("T-001", task_type=TaskType.ARCHIVE_INVESTIGATION, status=TaskStatus.COMPLETED),
        ]
        assert synthesis_complete(tasks) is False
