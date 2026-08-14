# Agentic RAG

> Part of **CaseMind Sentinel** — Police AI Investigation Platform  
> Build 3 · `milestone/v0.4-ai-detective-agent`

---

## Why Traditional RAG Is Not Enough

Traditional RAG answers a question with a single retrieval pass:

```
Question → Retrieve → Answer
```

This works for single-document lookups. It breaks down for a serial-crime investigation spanning four separate case files, where:

- **Clues are distributed**: The Northstar Facilities connection appears in all four files. No single document contains the whole picture.
- **Evidence is layered**: Daniel Mercer is unnamed in Cases 001 and 002. His name only appears when you search in the right direction after finding Northstar.
- **The next question depends on the previous answer**: You can only ask "who is D. MERCER?" after you have found the name on a work order in Case 003.

A single retrieval pass retrieves whatever is most similar to the initial question. It cannot discover what it does not know to search for yet.

---

## What Agentic RAG Adds

Agentic RAG replaces the single retrieval pass with an iterative investigation loop:

```
Question
→ Plan Archive Investigation
→ Search all case files
→ Inspect retrieved evidence
→ Discover new cross-case lead
→ Decide next archive search query  ← derived from evidence, not a script
→ Search again
→ Repeat
→ Answer  OR  reach Archive Boundary
```

The key difference: **the next search query is derived from what was just found**, not from the original question or a hardcoded sequence. The investigation follows the evidence.

---

## Concepts Implemented

### Multi-Hop Retrieval
Each iteration of the loop is one "hop". Evidence discovered in Hop 1 shapes the query for Hop 2. Evidence from Hop 2 shapes Hop 3. The investigation accumulates context across hops rather than starting fresh each time.

### Search → Reason → Search
The "Reason" step (in `investigator.py`) inspects all retrieved evidence and asks: *which entities appear in multiple case files?* A named organisation appearing in 3 out of 4 files is a stronger cross-case lead than one appearing in only 1. The next search is targeted at the strongest unexhausted lead.

### Planning
`planner.py` converts the detective's objective into an initial retrieval plan — a seed query and a set of investigative angles to consider. Planning is **retrieval-focused**: it decides what evidence to search for first, not how to decompose arbitrary goals.

### Dynamic Retrieval
The retrieval path changes based on what has been discovered. The Operation Nightfall investigation follows this path naturally:

| Hop | What drove the query | What was found |
|-----|---------------------|----------------|
| 1 | Initial objective | SentryGuard pattern, Northstar Facilities, dark blue van |
| 2 | SentryGuard lead | Engineer-level credential access confirmed across all cases |
| 3 | Northstar lead | 3-day pre-burglary visit pattern confirmed in all cases |
| 4 | Alarm maintenance mode | Credential-authorised suppression before every burglary |
| 5 | Daniel Mercer lead | NF-3847 out-of-hours access confirmed; vehicle still unplated |

No query in this sequence was hardcoded. Each was generated from the lead most strongly supported by the current evidence.

### Agentic RAG
The investigator acts autonomously within the archive: it decides what to search next, tracks its own investigation state, and determines when to stop. It does not receive external instructions between hops. This is the defining property of Agentic RAG — autonomous retrieval decision-making.

---

## Files

```
services/agentic_rag/
├── __init__.py       # Public API: investigate(), InvestigationResult
├── models.py         # All data models (state, events, leads, result)
├── planner.py        # Converts objective → initial investigation plan
├── investigator.py   # The Search → Reason → Search loop
└── README.md         # This file
```

---

## Investigation Flow

```
investigate(objective, case_dir)
    │
    ├─ planner.create_plan(objective)
    │       → InvestigationPlan (initial_query, planned_angles, max_hops)
    │       → PLAN_CREATED event
    │
    ├─ Loop (up to max_hops):
    │   │
    │   ├─ _search_archive(current_query, case_dir)
    │   │       → calls retrieve_evidence() for each .txt file
    │   │       → returns EvidenceHit[] with case_id + source_file attribution
    │   │       → SEARCH_STARTED, EVIDENCE_FOUND events
    │   │
    │   ├─ _extract_leads(all_evidence, already_searched)
    │   │       → scans evidence for known entity patterns
    │   │       → ranks by cross-case frequency (2+ files = stronger lead)
    │   │       → LEAD_DISCOVERED events
    │   │
    │   ├─ Select strongest unexhausted lead
    │   │       → generate next_query from lead.search_query
    │   │       → SEARCH_UPDATED event
    │   │
    │   └─ Check archive boundary signals
    │           → if plate not captured, external data required → stop
    │
    └─ _build_conclusion(leads, evidence, boundary_signals)
            → factual archive-level conclusion
            → ARCHIVE_BOUNDARY_REACHED, INVESTIGATION_COMPLETE events
```

---

## Operation Nightfall Example

Running against `sentinel/data/case-files/serial-robbery/` with the objective:

> "Are the four Operation Nightfall robberies connected? Identify the strongest shared leads using only the police case archive."

The investigation discovers — in order, from evidence alone:

1. **SentryGuard pattern** — shared alarm platform disabled before all four burglaries
2. **Northstar Facilities** — maintenance visit at each premises 3 days pre-burglary
3. **Alarm maintenance mode** — authorised credential used to suppress alerts each time
4. **Daniel Mercer** — named on Northstar work orders; NF-3847 used for out-of-hours access
5. **Dark blue Ford Transit** — observed near multiple premises; no plate in archive
6. **Credential NF-3847** — confirmed instrument of out-of-hours entry at Kingsley Watch Co.

---

## Archive Boundary

Agentic RAG can decide what archive evidence to retrieve next.  
It **cannot** interact with external investigative systems.

When the investigation establishes that a required fact — such as vehicle registration ownership — does not exist anywhere in the plain-text case archive, it stops and reports:

```
ARCHIVE_BOUNDARY_REACHED
```

With the explanation of what remains unresolved and what external resource would be needed to continue. For Operation Nightfall, those are:

- Vehicle registration ownership (DVLA)
- Complete engineer access logs (Northstar Facilities records)
- ANPR / surveillance correlation (Technical Surveillance Unit)
- Financial relationships (Financial Intelligence Unit)

These cannot be discovered by searching the archive more cleverly. They require external tool access — which is outside the scope of Agentic RAG.

---

## Relationship to Existing RAG

`services/rag/` is the traditional RAG foundation used by Project 002 (CaseMind Sentinel v1.0). It provides single-file retrieval via `retrieve_evidence(question, case_file)`. It remains unchanged and independently usable.

`services/agentic_rag/` builds on top of it. The `_search_archive()` function in `investigator.py` calls `retrieve_evidence()` for each case file in the archive directory, then adds multi-file orchestration, source attribution, lead extraction, and the iterative decision loop on top.

```
services/rag/           ← foundation (unchanged)
    retrieval.py            retrieve_evidence(question, case_file)

services/agentic_rag/   ← builds on top
    investigator.py         _search_archive() calls retrieve_evidence()
                            _extract_leads() reasons over accumulated evidence
                            investigate() runs the full loop
```

---

## What Comes Next

The next stage introduces **external investigative tools** — querying vehicle databases, access logs, surveillance records, and financial intelligence from the `tool-data/` directory. This moves from Agentic RAG (autonomous archive retrieval) to **AI Agent** (autonomous tool-calling with external systems).

Agentic RAG reaches the boundary where it says *"vehicle ownership cannot be determined from the archive"*. The AI Agent picks up there and runs a tool call to find out.
