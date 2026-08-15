# Agentic AI — Mission-Driven Investigation Orchestrator

## Overview

The Agentic AI layer sits above the two inner capabilities and runs a
self-directed investigation workflow:

```
Broad Mission
  → Goal Decomposition
  → Task Prioritisation
  → Capability Routing (archive / external / synthesis)
  → Observe → Adapt
  → Repeat
  → READY_FOR_HUMAN_REVIEW
```

## Architecture

### Files

| File | Responsibility |
|---|---|
| `models.py` | `MissionState`, `Task`, `WorkflowEvent` — all audit-able data |
| `decomposer.py` | LLM-injectable mission → initial task list |
| `prioritizer.py` | Pure deterministic queue, elevation, deprioritisation |
| `orchestrator.py` | `run_mission()` — the mission loop |
| `__init__.py` | Public API exports |

### Layers

```
Agentic AI (this package)
  ├── orchestrator.run_mission()
  │     ├── decomposer.decompose()
  │     ├── prioritizer.rebuild_queue()
  │     ├── [ARCHIVE]   → services.agentic_rag.investigate()
  │     ├── [EXTERNAL]  → services.ai_agent.run_investigation()
  │     └── [SYNTHESIS] → services.llm.client.generate_grounded_answer()
  └── models.MissionState  (returned to caller / future API layer)
```

### Mission Loop vs ReAct Loop

| Concept | Scope | Loop type |
|---|---|---|
| **ReAct** (AI Agent) | Single assigned task | Reason → Act → Observe → Repeat |
| **Mission Loop** (Agentic AI) | Entire investigation | Select → Route → Execute → Adapt → Repeat |

## Data Boundary

- This package **never** reads JSON files directly.
- It **never** imports from `ai_agent.tools.*` or `agentic_rag.investigator`.
- It **never** reads `operation-nightfall-ground-truth.json`.
- All data access is through injected capability functions.

## Adaptation Rules

| Rule | Trigger | Action |
|---|---|---|
| 1 | Surveillance returns `registration_captured=True` | Create CRITICAL vehicle lookup task |
| 2 | Vehicle keeper confirmed → person of interest | Elevate financial task to CRITICAL |
| 3 | Financial returns transfer recipient | Create HIGH lead validation task |
| 4 | Access logs: REVOKED credential, zero events | Deprioritise related tasks |
| 5 | Vehicle confirmed commercial/eliminated | Create LOW red-herring task, immediately deprioritise |
| 6 | All investigative tasks complete | Unblock SYNTHESIS |

## Provenance Guarantees

- **MBK-4172** does not appear in any task objective until after a surveillance
  observation returns it (Rule 1).
- **Marcus Vale** does not appear in any task objective until after a financial
  intelligence observation returns the transfer recipient name (Rule 3).

## Human Authority Boundary

The final mission status is always `READY_FOR_HUMAN_REVIEW`.

`final_assessment` uses language such as:
- "person of interest"
- "warrants further investigation"
- "requires human review"

It **never** claims guilt, issues warrants, or recommends arrest.

## Public API

```python
from services.agentic_ai import run_mission, BROAD_MISSION

state = run_mission(
    mission      = BROAD_MISSION,
    max_cycles   = 15,
    rag_fn       = None,    # inject for tests
    agent_fn     = None,    # inject for tests
    synthesis_fn = None,    # inject for tests
)
# state.status → MissionStatus.READY_FOR_HUMAN_REVIEW
# state.final_assessment → evidence-backed assessment string
# state.known_findings   → list of confirmed findings
# state.tasks            → full task list with provenance
# state.workflow_events  → complete audit trail
```

## Testing

```bash
cd sentinel/backend
python -m pytest tests/test_agentic_ai_models.py tests/test_agentic_ai_decomposer.py \
                 tests/test_agentic_ai_prioritizer.py tests/test_agentic_ai_orchestrator.py -v
```

All tests use injected stubs — no LLM, no filesystem, no network.
