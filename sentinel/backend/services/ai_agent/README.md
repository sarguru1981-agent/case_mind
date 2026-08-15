# AI Agent — Operation Nightfall Investigative Loop

## What this is

The AI Agent executes a **ReAct loop** (Reason → Act → Observe → Repeat) to investigate
an **assigned task** using four external investigative tools.

This is **Stage 2** of Build 3: Building an AI Detective Agent.

---

## Capability levels (strictly separated)

| Level | Name | What it does | Implemented here? |
|---|---|---|---|
| 1 | **RAG** | Retrieves documents from a static archive | No (see `agentic_rag/`) |
| 2 | **AI Agent** | Calls external tools, reasons over observations | **Yes — this module** |
| 3 | **Agentic AI** | Decomposes broad goals, manages sub-tasks | No (future) |

The AI Agent receives an **ASSIGNED TASK** from a human. It decides _how_ to investigate —
which tools to call, in what order — based on what it observes. It does NOT decompose
high-level goals or prioritise its own workflow.

---

## Files

```
services/ai_agent/
├── __init__.py              Public API: run_investigation, AgentState, build_registry
├── agent.py                 ReAct loop + deterministic decision engine
├── models.py                Pydantic models: ToolCall, ToolResult, EvidenceItem, AgentState
├── README.md                This file
└── tools/
    ├── __init__.py          build_registry() — loads all four tools
    ├── registry.py          ToolRegistry — sole execution boundary between agent and tools
    ├── vehicle_records.py   lookup_vehicle()
    ├── access_logs.py       query_access_logs()
    ├── surveillance.py      query_surveillance()
    └── financial_intelligence.py  query_financial_intelligence()
```

---

## The ReAct loop

```
DECIDE → ACT → OBSERVE → EXTRACT EVIDENCE → DECIDE → ...
```

Each iteration:
1. **REASON** — `_decide_next_action(state, registry)` inspects task text + prior observations
   and returns the next `(decision_summary, ToolCall)`. Returns `None` when complete.
2. **ACT** — `registry.invoke_call(tool_call)` executes the tool via the registry boundary.
3. **OBSERVE** — The `ToolResult` is appended to `state.observations`.
4. **EXTRACT EVIDENCE** — `_extract_evidence(obs)` converts confirmed facts into `EvidenceItem`s.

---

## Decision priority

The decision engine derives tool calls from task text and observations. It never hardcodes
specific values (e.g. a vehicle plate).

```
Priority 1: Vehicle lookup for plates discovered in surveillance observations  ← DYNAMIC
Priority 2: Surveillance for case IDs extracted from the task text
Priority 3: Access logs for credential IDs extracted from the task text
Priority 4: Financial intelligence for persons from task text / vehicle keeper
Priority 5: None → task complete
```

### Why Priority 1 is critical

`lookup_vehicle("MBK-4172")` can only fire **after** `query_surveillance` returns that plate
in an observation. The agent does not know `"MBK-4172"` in advance — it discovers it.
This preserves the correct ordering dependency naturally.

---

## Tool contracts

### lookup_vehicle
- **Input:** `registration` (exact plate string)
- **Source:** `data/tool-data/vehicle-records.json`
- **Returns:** make, model, colour, registered keeper
- **Does NOT return:** keeper date of birth (PII excluded)

### query_access_logs
- **Input:** `credential_id` OR `person_name` (credential_id takes precedence)
- **Source:** `data/tool-data/access-logs.json`
- **Returns:** all access events, role, credential status
- **Note:** Revoked credential with zero events is `status="success"`, not an error

### query_surveillance
- **Input:** `incident_case` OR `registration`; optional `time_window_start` / `time_window_end`
- **Source:** `data/tool-data/surveillance-records.json`
- **Returns:** sighting metadata — plate, confidence, camera ID, time, distance
- **Does NOT do:** facial recognition, image analysis, live surveillance

### query_financial_intelligence
- **Input:** `person_name` OR `account_ref` (account_ref takes precedence)
- **Source:** `data/tool-data/financial-records.json`
- **Returns:** raw transaction history, declared income, analyst notes
- **Does NOT conclude:** guilt, criminal coordination — that is for the human investigator

---

## Data isolation rules

Each tool reads ONLY its own JSON file. `agent.py` reads NO JSON files directly.
The ground truth file (`operation-nightfall-ground-truth.json`) is NEVER accessed
at runtime — it is test-only.

```
Tool module              Reads only
─────────────────────────────────────────────────────────
vehicle_records.py       vehicle-records.json
access_logs.py           access-logs.json
surveillance.py          surveillance-records.json
financial_intelligence.py  financial-records.json
agent.py                 ← reads no JSON at all
```

---

## ToolResult statuses

| Status | Meaning |
|---|---|
| `success` | Record found and returned |
| `not_found` | Valid query, no matching record |
| `invalid_input` | Missing or malformed required argument |
| `error` | Unexpected internal failure |

Tools NEVER raise unhandled Python exceptions for data conditions.
`not_found` is not an error — it is a valid investigative observation.

---

## AgentState fields (returned by run_investigation)

| Field | Description |
|---|---|
| `assigned_task` | The task given to the agent |
| `status` | `complete` or `max_iterations_reached` |
| `iteration` | Number of ReAct cycles executed |
| `decision_summary` | Concise operational reasoning for the last decision |
| `current_action` | Last tool call attempted |
| `tool_calls` | All tool calls made (in order) |
| `observations` | All tool results (in order, 1:1 with tool_calls) |
| `evidence` | Confirmed facts extracted from successful observations |
| `completion_summary` | Factual end-of-investigation summary (no guilt conclusions) |

---

## API endpoints

```
POST /api/agent/investigate
  Body: { "assigned_task": "...", "max_iterations": 10 }
  → AgentState JSON

GET /api/agent/tools
  → List of tool descriptions (name, description, input_schema)
```

---

## Running tests

```bash
cd sentinel/backend
pytest tests/test_ai_agent_tools.py tests/test_ai_agent_registry.py tests/test_ai_agent.py -v
```
