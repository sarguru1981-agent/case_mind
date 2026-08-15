"""Agentic AI — mission-driven investigation orchestrator for CaseMind Sentinel.

Public API:
    run_mission(mission, max_cycles) -> MissionState

This is the outermost intelligence layer.  It sits above the two inner
capabilities (Agentic RAG and AI Agent) and orchestrates a self-directed
investigation workflow:

  Broad Mission
    → Goal Decomposition (LLM-injectable)
    → Task Prioritisation (deterministic)
    → Capability Routing (archive / external / synthesis)
    → Observation → Adaptation (new tasks, re-priority)
    → Repeat
    → Human Review Assessment

This package does NOT:
  - read any tool-data JSON or case-file directly
  - import from ai_agent.tools.* or agentic_rag.investigator internals
  - claim guilt, issue warrants, or recommend arrests

Final status is always READY_FOR_HUMAN_REVIEW (not "CASE SOLVED").
"""
from .orchestrator import run_mission, BROAD_MISSION
from .models import (
    MissionState,
    MissionStatus,
    Task,
    TaskType,
    TaskStatus,
    Priority,
    WorkflowEvent,
    WorkflowEventType,
)

__all__ = [
    "run_mission",
    "BROAD_MISSION",
    "MissionState",
    "MissionStatus",
    "Task",
    "TaskType",
    "TaskStatus",
    "Priority",
    "WorkflowEvent",
    "WorkflowEventType",
]
