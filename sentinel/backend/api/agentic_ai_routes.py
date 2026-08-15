"""Agentic AI mission endpoint.

Exposes the agentic_ai.run_mission() orchestration loop through a single
REST endpoint. The mission runs to completion (or max_cycles) and returns
the full MissionState for the UI to render.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agentic_ai import BROAD_MISSION, MissionState, run_mission

router = APIRouter()


class MissionRequest(BaseModel):
    mission: str = Field(default=BROAD_MISSION, min_length=10, max_length=2000)
    max_cycles: int = Field(default=15, ge=1, le=30)


@router.post("/mission", response_model=MissionState)
async def start_mission(request: MissionRequest) -> MissionState:
    try:
        return run_mission(
            mission=request.mission,
            max_cycles=request.max_cycles,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
