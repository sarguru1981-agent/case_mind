# CaseMind Sentinel — Version History

---

## v1.0 — Part 4: Trust Layer

**Article:** The Wrong Evidence That Made RAG Hallucinate

**Status:** Release Candidate

**Features:**

- FastAPI backend with `/health`, `/version`, and `POST /api/query` endpoints
- React frontend scaffold (production target: Vite; local fallback: CDN React + Babel)
- Evidence Retrieval Service (RAG Pipeline)
  - Production target: sentence-transformers + ChromaDB
  - Local fallback: scikit-learn TF-IDF in-memory index
- Prompt Builder (`build_grounding_prompt`)
- LLM Client through Portkey AI Gateway (Anthropic-compatible API)
- Prompt Injection Guard
- Contradiction Detection
- Claim Extraction
- Fact Checking
- Trust Score (0.0–1.0; verdicts: HIGH / MEDIUM / LOW / REVIEW REQUIRED)
- Trusted Response (`TrustedResponse` API contract)
- Authentic and corrupted Millbrook Arson 2019 case files
- TF-IDF local retrieval fallback (active when HuggingFace unreachable)
- Production targets documented for sentence-transformers and ChromaDB

**API contract established:**
- `POST /api/query` → `TrustedResponse`
- `status` vocabulary: `OK`, `INJECTION_DETECTED`, `ERROR`
- All trust fields are `Optional`; future versions add fields without breaking v1.0 callers

---

## Planned

### v1.1 — Memory

- Persistent query history
- Session context carried across queries

### v1.2 — Agents

- Multi-step autonomous investigation
- Sub-task decomposition

### v1.3 — Tools

- External data source integration
- Entity extraction

### v2.0 — Advanced Multi-Agent Investigation Platform

- Multi-case reasoning
- Production retrieval (fine-tuned forensic model)
- Multi-case knowledge graph
