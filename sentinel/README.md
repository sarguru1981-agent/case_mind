# CaseMind Sentinel v0.4

**Police AI Investigation Platform**

CaseMind Sentinel is the real-time application built throughout *The Detective's Guide to AI* article series. Each article adds one new capability. Each capability is production-grade from the start.

---

## What This Is

CaseMind Sentinel is not an educational project. It is a long-running platform that grows with the series.

Educational projects live in `learn/`. This application lives in `sentinel/`.

---

## Current Version

**v0.4 — Build 3: Agentic RAG**

*Building an AI Detective Agent*

Status: Approved

CaseMind Sentinel v0.4 adds a multi-hop Agentic RAG investigation loop. The four Operation Nightfall case files are searched iteratively — each hop derives its query from the strongest unexhausted cross-case lead found in the previous hop — until the investigation reaches the archive boundary.

See `docs/version-history.md` for the full version history and roadmap.

---

## Build 3 Capability

The Agentic RAG loop replaces single-pass retrieval with an iterative archive investigation.

**Investigation loop (Search → Reason → Search):**

1. Plan — convert objective into seed query and investigative angles
2. Search all four case files — retrieve top-K chunks from each
3. Reason — identify entities appearing across multiple files (cross-case leads)
4. Select strongest unexhausted lead — generate next query from evidence
5. Repeat up to max hops
6. Archive Boundary — report unresolved facts requiring external data

**Archive boundary signals for Operation Nightfall:**
- Vehicle registration ownership (DVLA)
- Engineer access logs (Northstar Facilities records)
- ANPR / surveillance correlation (Technical Surveillance Unit)
- Financial relationships (Financial Intelligence Unit)

See `backend/services/agentic_rag/README.md` for full implementation detail.

---

## Structure

```
sentinel/
├── backend/              FastAPI application
│   ├── api/              Route handlers
│   ├── config/           Application settings (loaded from .env)
│   ├── models/           Pydantic request/response models
│   ├── services/
│   │   ├── rag/               RAG pipeline (retrieval + prompt builder)
│   │   ├── llm/               LLM client boundary (Portkey AI Gateway)
│   │   ├── rag_hallucination/ Trust layer (guardrail, contradiction, fact-check, scoring)
│   │   └── agentic_rag/       Agentic RAG — multi-hop archive investigation loop
│   ├── tests/            Automated tests (32 agentic RAG tests)
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example      Copy to .env and fill in credentials — do not commit .env
├── frontend/             React + Vite — cinematic Investigation Console
│   ├── src/              Production React components
│   ├── scripts/          prebuild-vendor.mjs (restricted-machine support)
│   ├── index.html
│   └── package.json
├── data/
│   ├── case-files/       Raw case file text (authentic + corrupted Millbrook variants)
│   └── evidence/         Processed evidence artifacts (embeddings, index snapshots — future)
├── article-assets/
│   └── agentic-rag/      Approved Build 3 article screenshots
├── configs/              Application-level configuration (case registry, deployment manifests — future)
└── docs/
    ├── architecture.md               Technical design and two-layer architecture
    ├── part-4-implementation-plan.md Full implementation plan for v1.0
    ├── roadmap.md                    Feature roadmap by article part
    ├── version-history.md            Version history and release notes
    └── article-assets/               Publication screenshots (Part 4 / v1.0)
```

**Service documentation:**

| Package | Description |
|---------|-------------|
| [`services/rag/`](backend/services/rag/README.md) | RAG pipeline — evidence retrieval and prompt assembly |
| [`services/rag_hallucination/`](backend/services/rag_hallucination/README.md) | Trust layer — guardrail, contradiction detection, fact checking, trust scoring |
| [`services/agentic_rag/`](backend/services/agentic_rag/README.md) | Agentic RAG — multi-hop Search → Reason → Search investigation loop |

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

**Frontend (standard):**

```bash
cd sentinel/frontend
npm install
npm run dev
```

**Frontend (restricted machine — esbuild blocked by security policy):**

```bash
cd sentinel/frontend
npm install
npm run dev:no-esbuild
```

The `dev:no-esbuild` script automatically pre-builds vendor bundles via Babel/Rollup before starting Vite. Normal developers use `npm run dev`.

Open `http://localhost:5173`.

**API endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Liveness check |
| GET | /version | Application metadata |
| POST | /api/query | Submit a detective query, receive a trusted response |
| POST | /api/agentic-rag/investigate | Run Agentic RAG multi-hop archive investigation |

---

*Future articles extend this platform. They do not replace it.*
