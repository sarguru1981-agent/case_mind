"""Archive investigation planner.

Converts a detective's investigation objective into an initial retrieval
plan — the starting point for the Agentic RAG loop.

Agentic RAG planning is retrieval-focused:
  - determine what evidence to search first
  - identify the angles worth pursuing
  - leave room for the investigator to update the plan as evidence emerges

It is NOT an autonomous task decomposition engine for arbitrary goals.
"""
from __future__ import annotations

from .models import InvestigationPlan


# Angles that make sense for any serial-incident archive investigation.
# The investigator will pursue each as leads emerge — these are not a
# fixed script, they are searchable dimensions to consider.
_ARCHIVE_INVESTIGATION_ANGLES = [
    "Identify shared operational patterns across all incidents (alarm compromise, entry method)",
    "Trace shared organisations or companies appearing in multiple incident records",
    "Identify named individuals or credentials recurring across case files",
    "Locate recurring vehicle or physical suspect descriptions",
    "Establish the archive boundary: determine what facts require external investigation",
]

# Simple vocabulary to recognise connectivity objectives and produce a
# useful seed query rather than sending the raw question to TF-IDF.
_CONNECTIVITY_TERMS = {
    "connected", "connection", "series", "pattern", "link", "related",
    "same", "shared", "common", "repeat", "recurring",
}


def create_plan(objective: str, max_hops: int = 5) -> InvestigationPlan:
    """Return an initial investigation plan for the given objective.

    The initial query is derived from the objective text so that the
    first archive search is immediately relevant, without hard-coding
    case-specific terms.
    """
    words = set(objective.lower().split())
    if words & _CONNECTIVITY_TERMS:
        # Connectivity objective: start broad — security patterns AND physical
        # evidence (vehicle/witness) so the first hop captures both dimensions.
        initial_query = "shared pattern alarm compromise vehicle sighting witness incidents"
    else:
        # Generic objective: use the objective itself as the seed query
        initial_query = objective[:140]

    return InvestigationPlan(
        objective      = objective,
        initial_query  = initial_query,
        planned_angles = _ARCHIVE_INVESTIGATION_ANGLES,
        max_hops       = max_hops,
    )
