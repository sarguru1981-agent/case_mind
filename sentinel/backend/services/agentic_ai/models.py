"""Agentic AI data models — MissionState, Task, WorkflowEvent.

Every field is safe and auditable: the full mission lifecycle, each task's
provenance chain, and every workflow decision are captured here so a human
reviewer can reconstruct exactly how the investigation proceeded.

No hidden chain-of-thought.  No implicit state.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Mission status vocabulary
# ---------------------------------------------------------------------------

class MissionStatus(str, Enum):
    INITIALIZING          = "INITIALIZING"
    ACTIVE                = "ACTIVE"
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"
    BLOCKED               = "BLOCKED"
    MAX_CYCLES_REACHED    = "MAX_CYCLES_REACHED"
    FAILED                = "FAILED"


# ---------------------------------------------------------------------------
# Task vocabulary
# ---------------------------------------------------------------------------

class TaskType(str, Enum):
    ARCHIVE_INVESTIGATION    = "ARCHIVE_INVESTIGATION"
    EXTERNAL_INVESTIGATION   = "EXTERNAL_INVESTIGATION"
    LEAD_VALIDATION          = "LEAD_VALIDATION"
    RED_HERRING_VALIDATION   = "RED_HERRING_VALIDATION"
    SYNTHESIS                = "SYNTHESIS"


class TaskStatus(str, Enum):
    NOT_STARTED   = "NOT_STARTED"
    READY         = "READY"
    IN_PROGRESS   = "IN_PROGRESS"
    BLOCKED       = "BLOCKED"
    COMPLETED     = "COMPLETED"
    DEPRIORITIZED = "DEPRIORITIZED"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"


_PRIORITY_ORDER = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}


def priority_rank(p: Priority) -> int:
    """Lower number = higher priority."""
    return _PRIORITY_ORDER[p]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(BaseModel):
    task_id:             str
    title:               str
    objective:           str
    task_type:           TaskType
    priority:            Priority
    status:              TaskStatus
    dependencies:        list[str]       = Field(default_factory=list)
    assigned_capability: str             # "agentic_rag" | "ai_agent" | "synthesis"
    reason:              str
    created_from:        str             # "mission_decomposition" | <task_id>
    result:              Optional[Any]   = None
    evidence_refs:       list[str]       = Field(default_factory=list)
    priority_history:    list[str]       = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Workflow event
# ---------------------------------------------------------------------------

class WorkflowEventType(str, Enum):
    MISSION_RECEIVED             = "MISSION_RECEIVED"
    MISSION_DECOMPOSED           = "MISSION_DECOMPOSED"
    TASK_CREATED                 = "TASK_CREATED"
    TASK_PRIORITIZED             = "TASK_PRIORITIZED"
    TASK_STARTED                 = "TASK_STARTED"
    CAPABILITY_SELECTED          = "CAPABILITY_SELECTED"
    TASK_COMPLETED               = "TASK_COMPLETED"
    NEW_FINDING                  = "NEW_FINDING"
    TASK_CREATED_FROM_FINDING    = "TASK_CREATED_FROM_FINDING"
    TASK_REPRIORITIZED           = "TASK_REPRIORITIZED"
    TASK_DEPRIORITIZED           = "TASK_DEPRIORITIZED"
    WORKFLOW_REASSESSED          = "WORKFLOW_REASSESSED"
    MISSION_READY_FOR_HUMAN_REVIEW = "MISSION_READY_FOR_HUMAN_REVIEW"


class WorkflowEvent(BaseModel):
    event_type: WorkflowEventType
    summary:    str
    task_id:    Optional[str] = None
    cycle:      int
    timestamp:  str           = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Mission state
# ---------------------------------------------------------------------------

class MissionState(BaseModel):
    mission_id:           str
    mission:              str
    status:               MissionStatus
    cycle_count:          int              = 0
    max_cycles:           int              = 15
    reassessment_count:   int              = 0
    tasks:                list[Task]       = Field(default_factory=list)
    priority_queue:       list[str]        = Field(default_factory=list)
    current_focus:        Optional[str]    = None
    known_findings:       list[str]        = Field(default_factory=list)
    unresolved_questions: list[str]        = Field(default_factory=list)
    workflow_events:      list[WorkflowEvent] = Field(default_factory=list)
    completion_criteria:  list[str]        = Field(default_factory=list)
    final_assessment:     Optional[str]    = None
