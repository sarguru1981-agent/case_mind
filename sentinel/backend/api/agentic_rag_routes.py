"""Agentic RAG investigation endpoint.

Exposes the agentic_rag.investigate() loop through a single REST endpoint.
The Operation Nightfall serial robbery archive is the fixed case directory.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agentic_rag import investigate
from services.agentic_rag.models import InvestigationResult

router = APIRouter()

_SERIAL_ROBBERY_DIR = (
    Path(__file__).resolve().parent.parent.parent / "data" / "case-files" / "serial-robbery"
)

_DEFAULT_OBJECTIVE = (
    "Are the four Operation Nightfall robberies connected? "
    "Identify the strongest shared leads using only the police case archive."
)


class InvestigateRequest(BaseModel):
    objective: str = Field(default=_DEFAULT_OBJECTIVE, min_length=10, max_length=500)
    max_hops: int  = Field(default=5, ge=1, le=10)


@router.post("/investigate", response_model=InvestigationResult)
async def investigate_archive(request: InvestigateRequest) -> InvestigationResult:
    if not _SERIAL_ROBBERY_DIR.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Case archive not found: {_SERIAL_ROBBERY_DIR}",
        )

    try:
        return investigate(
            objective=request.objective,
            case_dir=str(_SERIAL_ROBBERY_DIR),
            max_hops=request.max_hops,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
