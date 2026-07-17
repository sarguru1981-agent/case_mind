# CaseMind Sentinel — Roadmap

**Police AI Investigation Platform**

Each article delivers one new capability. Each capability is production-grade from the start and is never replaced — only extended.

---

## Part 4 — Trust Layer

**Article:** The Wrong Evidence That Made RAG Hallucinate

**Status:** Complete

**What ships:**

- FastAPI backend with health and query endpoints
- Evidence Retrieval Service (RAG Pipeline) using sentence-transformers + ChromaDB + Anthropic SDK + LangChain or LlamaIndex where useful
- Trust layer (custom): contradiction detection, claim extraction, fact checking, prompt injection guard, trust scoring, trusted response
- React + Vite frontend: query input, trusted response display, trust score panel

**Foundation:** This is the first working version of CaseMind Sentinel.

---

## Part 5 — Memory

**Article:** TBD

**What ships:**

- Persistent query history
- Session context carried across queries
- Prior questions surfaced in the UI

---

## Part 6 — Agents

**Article:** TBD

**What ships:**

- Multi-step autonomous investigation
- Sub-task decomposition
- Agent activity panel in the frontend

---

## Part 7 — Tools

**Article:** TBD

**What ships:**

- External data source integration
- Entity extraction
- Phone number and entity comparison screen

---

## Part 8 — Planning

**Article:** TBD

**What ships:**

- Multi-case reasoning
- Chronological event reconstruction
- Investigation timeline screen

---

## Future — Production Upgrades

As the series progresses, earlier components are upgraded rather than replaced:

- sentence-transformers → fine-tuned forensic model
- ChromaDB local → ChromaDB persistent server
- Simulated evidence → real case file management
- Single case → multi-case knowledge graph

---

*Updated as each part of the series ships.*
