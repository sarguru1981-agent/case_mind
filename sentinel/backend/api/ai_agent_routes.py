"""FastAPI routes for the AI Agent investigation endpoint.

POST /api/agent/investigate
  Body: { "assigned_task": "..." }   (optional — defaults to ASSIGNED_TASK)
  Returns: AgentState as JSON

GET /api/agent/tools
  Returns: list of tool descriptions (name, description, schema)
  Used by the frontend to display available investigative capabilities.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_agent import run_investigation, ASSIGNED_TASK, AgentState
from services.ai_agent.tools import build_registry

router = APIRouter(prefix="/api/agent", tags=["ai-agent"])

_registry = build_registry()


class InvestigateRequest(BaseModel):
    assigned_task:  Optional[str] = None
    max_iterations: Optional[int] = 10


@router.post("/investigate", response_model=AgentState)
def investigate(request: InvestigateRequest) -> AgentState:
    """
    Execute the AI Agent ReAct loop for the assigned task.

    If no assigned_task is provided the default Operation Nightfall task is used.
    The agent reasons over external tool observations — it does NOT access
    the case archive, RAG index, or ground-truth data.
    """
    task = (request.assigned_task or "").strip() or ASSIGNED_TASK
    max_iter = max(1, min(request.max_iterations or 10, 20))

    try:
        state = run_investigation(
            assigned_task  = task,
            registry       = _registry,
            max_iterations = max_iter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return state


@router.get("/tools")
def list_tools() -> list[dict]:
    """Return tool descriptions available to the AI Agent."""
    return _registry.get_tool_descriptions()
