"""Tests for agentic_ai.models — data contracts and invariants."""
import pytest
from pydantic import ValidationError

from services.agentic_ai.models import (
    MissionState,
    MissionStatus,
    Priority,
    Task,
    TaskStatus,
    TaskType,
    WorkflowEvent,
    WorkflowEventType,
    priority_rank,
)


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrder:
    def test_critical_is_highest(self):
        assert priority_rank(Priority.CRITICAL) < priority_rank(Priority.HIGH)

    def test_high_above_medium(self):
        assert priority_rank(Priority.HIGH) < priority_rank(Priority.MEDIUM)

    def test_medium_above_low(self):
        assert priority_rank(Priority.MEDIUM) < priority_rank(Priority.LOW)

    def test_full_ordering(self):
        ordered = sorted(
            [Priority.LOW, Priority.CRITICAL, Priority.MEDIUM, Priority.HIGH],
            key=priority_rank,
        )
        assert ordered == [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]


# ---------------------------------------------------------------------------
# Task construction
# ---------------------------------------------------------------------------

def _make_task(**overrides) -> Task:
    defaults = dict(
        task_id             = "T-001",
        title               = "Test task",
        objective           = "Do something",
        task_type           = TaskType.ARCHIVE_INVESTIGATION,
        priority            = Priority.HIGH,
        status              = TaskStatus.READY,
        assigned_capability = "agentic_rag",
        reason              = "testing",
        created_from        = "mission_decomposition",
    )
    defaults.update(overrides)
    return Task(**defaults)


class TestTask:
    def test_minimal_construction(self):
        task = _make_task()
        assert task.task_id == "T-001"
        assert task.dependencies == []
        assert task.evidence_refs == []
        assert task.priority_history == []
        assert task.result is None

    def test_invalid_task_type_rejected(self):
        with pytest.raises(ValidationError):
            _make_task(task_type="INVENTED")

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            _make_task(priority="ULTRA")

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            _make_task(status="RUNNING")

    def test_dependencies_stored(self):
        task = _make_task(dependencies=["T-001", "T-002"])
        assert task.dependencies == ["T-001", "T-002"]

    def test_model_copy_immutable_original(self):
        task    = _make_task()
        updated = task.model_copy(update={"status": TaskStatus.COMPLETED})
        assert task.status    == TaskStatus.READY
        assert updated.status == TaskStatus.COMPLETED

    def test_priority_history_appended(self):
        task = _make_task(priority_history=["HIGH (initial)"])
        assert task.priority_history == ["HIGH (initial)"]


# ---------------------------------------------------------------------------
# WorkflowEvent
# ---------------------------------------------------------------------------

class TestWorkflowEvent:
    def test_construction(self):
        ev = WorkflowEvent(
            event_type = WorkflowEventType.TASK_CREATED,
            summary    = "T-001 created",
            cycle      = 1,
            timestamp  = "2025-01-01T00:00:00+00:00",
        )
        assert ev.event_type == WorkflowEventType.TASK_CREATED
        assert ev.task_id is None

    def test_with_task_id(self):
        ev = WorkflowEvent(
            event_type = WorkflowEventType.TASK_COMPLETED,
            summary    = "done",
            task_id    = "T-001",
            cycle      = 2,
            timestamp  = "2025-01-01T00:00:00+00:00",
        )
        assert ev.task_id == "T-001"

    def test_invalid_event_type_rejected(self):
        with pytest.raises(ValidationError):
            WorkflowEvent(
                event_type = "MADE_UP",
                summary    = "x",
                cycle      = 0,
                timestamp  = "2025-01-01T00:00:00+00:00",
            )


# ---------------------------------------------------------------------------
# MissionState
# ---------------------------------------------------------------------------

class TestMissionState:
    def test_construction_defaults(self):
        state = MissionState(
            mission_id = "abc123",
            mission    = "Do some investigation",
            status     = MissionStatus.INITIALIZING,
        )
        assert state.cycle_count          == 0
        assert state.tasks                == []
        assert state.known_findings       == []
        assert state.workflow_events      == []
        assert state.priority_queue       == []
        assert state.final_assessment     is None
        assert state.current_focus        is None

    def test_task_appended(self):
        state = MissionState(
            mission_id = "x",
            mission    = "m",
            status     = MissionStatus.ACTIVE,
        )
        state.tasks.append(_make_task())
        assert len(state.tasks) == 1

    def test_status_transitions(self):
        state = MissionState(
            mission_id = "x",
            mission    = "m",
            status     = MissionStatus.ACTIVE,
        )
        state.status = MissionStatus.READY_FOR_HUMAN_REVIEW
        assert state.status == MissionStatus.READY_FOR_HUMAN_REVIEW

    def test_all_mission_statuses_valid(self):
        for s in MissionStatus:
            state = MissionState(
                mission_id = "x",
                mission    = "m",
                status     = s,
            )
            assert state.status == s

    def test_known_findings_accumulate(self):
        state = MissionState(
            mission_id = "x",
            mission    = "m",
            status     = MissionStatus.ACTIVE,
        )
        state.known_findings.append("Finding one")
        state.known_findings.append("Finding two")
        assert len(state.known_findings) == 2

    def test_max_cycles_configurable(self):
        state = MissionState(
            mission_id = "x",
            mission    = "m",
            status     = MissionStatus.ACTIVE,
            max_cycles = 5,
        )
        assert state.max_cycles == 5

    def test_workflow_events_ordered(self):
        state = MissionState(
            mission_id = "x",
            mission    = "m",
            status     = MissionStatus.ACTIVE,
        )
        state.workflow_events.append(WorkflowEvent(
            event_type = WorkflowEventType.MISSION_RECEIVED,
            summary    = "first",
            cycle      = 0,
            timestamp  = "2025-01-01T00:00:00+00:00",
        ))
        state.workflow_events.append(WorkflowEvent(
            event_type = WorkflowEventType.TASK_CREATED,
            summary    = "second",
            cycle      = 0,
            timestamp  = "2025-01-01T00:00:01+00:00",
        ))
        assert state.workflow_events[0].summary == "first"
        assert state.workflow_events[1].summary == "second"
