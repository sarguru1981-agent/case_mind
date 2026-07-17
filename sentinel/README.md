# CaseMind Sentinel v1.0

**Police AI Investigation Platform**

CaseMind Sentinel is the real-time application built throughout *The Detective's Guide to AI* article series. Each article adds one new capability. Each capability is production-grade from the start.

---

## What This Is

CaseMind Sentinel is not an educational project. It is a long-running platform that grows with the series.

Educational projects live in `learn/`. This application lives in `sentinel/`.

---

## Current Version

**v1.0 — Part 4: Trust Layer**

*The Wrong Evidence That Made RAG Hallucinate*

Status: Release Candidate

CaseMind Sentinel v1.0 delivers a full Evidence Retrieval Service (RAG Pipeline) with a custom trust layer that can detect corrupted evidence, verify claims, and score every response for reliability before returning it to the detective.

See `docs/version-history.md` for the full version history and roadmap.

---

## Part 4 Capability

The trust layer runs alongside the RAG pipeline and produces a verifiable, scored response rather than a raw answer.

**Pipeline:**

1. Prompt injection guard — rejects malicious queries before any LLM call
2. Evidence retrieval — retrieves the top-K most relevant case file chunks
3. Grounding prompt — assembles evidence pages into a grounded brief
4. LLM answer — generates a grounded answer via Portkey AI Gateway
5. Contradiction detection — scans retrieved pages for conflicting facts
6. Claim extraction — breaks the answer into discrete verifiable assertions
7. Fact checking — verifies each claim against the source pages it cites
8. Trust scoring — combines retrieval confidence, verification rate, and contradiction penalty
9. Trusted response — packages answer + claims + contradictions + score + verdict

**Trust score verdicts:**
- `HIGH` (≥ 0.75) — answer is reliable
- `MEDIUM` (≥ 0.50) — review recommended
- `LOW / REVIEW REQUIRED` (< 0.50, or any contradiction detected) — do not act on this answer without review

---

## Structure

```
sentinel/
├── backend/              FastAPI application
│   ├── api/              Route handlers
│   ├── config/           Application settings (loaded from .env)
│   ├── models/           Pydantic request/response models
│   ├── services/
│   │   ├── evidence/     Evidence Retrieval Service (retrieval + prompt builder)
│   │   ├── llm/          LLM client boundary (Portkey AI Gateway)
│   │   └── trust/        Trust layer (guardrail, contradiction, fact-check, scoring)
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example      Copy to .env and fill in credentials — do not commit .env
├── frontend/             React + Vite command center
│   ├── src/              Production React components
│   ├── index.html        Local fallback (CDN React, no build step needed)
│   └── package.json
├── data/
│   ├── case-files/       Raw case file text (authentic + corrupted Millbrook variants)
│   └── evidence/         Processed evidence artifacts (embeddings, index snapshots — future)
├── configs/              Application-level configuration (case registry, deployment manifests — future)
└── docs/
    ├── architecture.md               Technical design and two-layer architecture
    ├── part-4-implementation-plan.md Full implementation plan for v1.0
    ├── roadmap.md                    Feature roadmap by article part
    ├── version-history.md            Version history and release notes
    └── article-assets/               Publication screenshots (Part 4)
```

---

## Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```
cp sentinel/backend/.env.example sentinel/backend/.env
```

Required fields:

| Variable | Purpose |
|----------|---------|
| `PORTKEY_API_KEY` | Portkey AI Gateway API key |
| `PORTKEY_BASE_URL` | Gateway endpoint URL |
| `PORTKEY_MODEL` | Model identifier string passed through the gateway |
| `PORTKEY_PROVIDER` | Provider header value (`x-portkey-provider`) |

**Never commit `.env`. It is gitignored. It must never contain real credentials in any tracked file.**

---

## Running Locally

**Backend:**

```bash
cd sentinel/backend
PYTHONPATH=. python3 -m uvicorn main:app --reload --port 8000
```

**Frontend (local fallback — no build step):**

```bash
cd sentinel/frontend
python3 -m http.server 5173
```

Open `http://localhost:5173`.

**API endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Liveness check |
| GET | /version | Application metadata |
| POST | /api/query | Submit a detective query, receive a trusted response |

---

*Future articles extend this platform. They do not replace it.*
