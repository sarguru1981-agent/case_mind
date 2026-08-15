"""AI Agent data models — ToolCall, ToolResult, AgentState.

These are the public contracts between the agent loop, the tool registry,
and any future API layer.  No hidden chain-of-thought is stored here.
Every field is safe and useful to surface in an investigation UI.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Function-calling contracts
# ---------------------------------------------------------------------------

class ToolCall(BaseModel):
    """The agent's intent: which tool to call with what structured arguments."""
    call_id:   str            = Field(default_factory=_short_id)
    tool_name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """What the agent observes after the registry executes a tool call."""
    call_id:       str
    tool_name:     str
    status:        Literal["success", "not_found", "invalid_input", "error"]
    result:        Optional[dict[str, Any]] = None
    error:         Optional[str]            = None
    timestamp:     str                      = Field(default_factory=_utc_now)
    query_summary: str                      = ""   # one-liner for UI display


# ---------------------------------------------------------------------------
# Evidence item — a confirmed fact extracted from a tool observation
# ---------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    fact:        str   # plain-language statement of what was confirmed
    source_tool: str   # which tool produced this fact
    call_id:     str   # ties back to the ToolResult
    confidence:  str   # HIGH / MEDIUM / LOW — taken from the tool payload


# ---------------------------------------------------------------------------
# Agent state — the full execution record
# ---------------------------------------------------------------------------

class AgentState(BaseModel):
    """Complete record of one AI Agent investigation run.

    decision_summary contains only concise operational reasoning, e.g.:
        "Surveillance is required to determine whether a vehicle registration
         was captured near Kingsley Watch Co. on the night of MCR-2025-0291."

    It must never store model scratchpads or hidden chain-of-thought.
    """
    # Immutable task context
    assigned_task:  str
    max_iterations: int = 10

    # Mutable execution state
    status:    Literal["active", "complete", "max_iterations_reached"] = "active"
    iteration: int = 0

    # Current iteration (replaced each loop)
    decision_summary: str                = ""
    current_action:   Optional[ToolCall] = None

    # Accumulating records
    tool_calls:   list[ToolCall]    = Field(default_factory=list)
    observations: list[ToolResult]  = Field(default_factory=list)
    evidence:     list[EvidenceItem] = Field(default_factory=list)

    # Final output written when status → "complete"
    completion_summary: Optional[str] = None
