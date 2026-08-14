"""Agentic RAG — iterative archive investigation for CaseMind Sentinel.

Public API:
    investigate(objective, case_dir, max_hops) -> InvestigationResult

Traditional RAG answers a question with one retrieval pass.
Agentic RAG plans an investigation, searches, inspects what it found,
discovers new leads, and decides what to search next — repeating until
it either resolves the objective or reaches the boundary of what the
archive can tell it.

This package does NOT call external tools.  It operates exclusively on
the searchable plain-text case archive under sentinel/data/case-files/.
"""
from .investigator import investigate
from .models import InvestigationResult, InvestigationStatus, EventType

__all__ = ["investigate", "InvestigationResult", "InvestigationStatus", "EventType"]
