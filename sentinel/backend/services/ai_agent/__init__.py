"""AI Agent package — ReAct investigation loop for Operation Nightfall.

Public API
----------
run_investigation   Execute the agent loop for an assigned task.
AgentState          Full execution record returned by run_investigation.
build_registry      Build the pre-loaded ToolRegistry (four tools).
ToolRegistry        Tool execution boundary; used in testing / dependency injection.
"""
from .agent import run_investigation, ASSIGNED_TASK
from .models import AgentState, EvidenceItem, ToolCall, ToolResult
from .tools import build_registry, ToolRegistry, ToolNotFoundError

__all__ = [
    "run_investigation",
    "ASSIGNED_TASK",
    "AgentState",
    "EvidenceItem",
    "ToolCall",
    "ToolResult",
    "build_registry",
    "ToolRegistry",
    "ToolNotFoundError",
]
