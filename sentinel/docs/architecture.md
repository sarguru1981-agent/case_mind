# CaseMind Sentinel — Architecture

**Police AI Investigation Platform**

---

## Design Principle

CaseMind Sentinel is built in two layers:

1. **Infrastructure layer** — real libraries handle the AI/RAG pipeline.
2. **Trust layer** — custom code makes the pipeline trustworthy.

The infrastructure layer is not the subject of the article series. The trust layer is.

---

## Stack

### Backend

| Component | Library | Purpose |
|-----------|---------|---------|
| API server | FastAPI | REST endpoints for query, health, version |
| Data models | Pydantic | Request/response validation and serialisation |
| Configuration | python-dotenv | Environment variable management |
| Embeddings | sentence-transformers | Dense vector representations of case file chunks |
| Vector store | ChromaDB | Persistent similarity search over indexed evidence |
| LLM | Anthropic SDK | Grounded answer generation from retrieved evidence |
| Orchestration | LangChain or LlamaIndex | Pipeline orchestration where it reduces boilerplate without hiding trust layer logic |

### Frontend

| Component | Library | Purpose |
|-----------|---------|---------|
| Framework | React | Component-based UI |
| Build tool | Vite | Fast local development server and bundler |

---

## Naming

The underlying AI technique is **RAG** (Retrieval-Augmented Generation). Inside CaseMind Sentinel the service that implements it is called the **Evidence Retrieval Service**. This name is intentional: it reflects what the service does in the context of a police investigation platform, not how it is implemented.

The two names refer to the same thing:

| Term | Context |
|------|---------|
| RAG Pipeline | Technical concept; used in article text and educational projects |
| Evidence Retrieval Service | Service name inside CaseMind Sentinel; used in code, API docs, and the frontend |

---

## Two-Layer Architecture

```
Query
  │
  ▼
┌──────────────────────────────────────────┐
│  TRUST LAYER (custom)                    │
│                                          │
│  Prompt Injection Guard                  │
│    ↓ (passes if clean)                   │
│  [Evidence Retrieval Service]            │
│    (RAG: sentence-transformers +         │
│     ChromaDB + Anthropic SDK +           │
│     LangChain/LlamaIndex if useful)      │
│    ↓                                     │
│  Contradiction Detection                 │
│  Claim Extraction                        │
│  Fact Checking                           │
│  Trust Scoring                           │
└──────────────────────────────────────────┘
  │
  ▼
Trusted Response
  { answer, claims, contradictions, score, verdict }
```

### Infrastructure Layer (libraries)

sentence-transformers converts case file chunks into dense vectors. ChromaDB stores and searches those vectors at query time. The Anthropic SDK generates a grounded answer from the retrieved evidence pages.

LangChain or LlamaIndex may be used inside the Evidence Retrieval Service where they reduce boilerplate without hiding the trust layer logic. The trust layer always remains explicit custom code — orchestration libraries are only used for the retrieval and answer-generation steps where their abstraction is safe.

These components are well-tested libraries. We use them without rebuilding them.

### Trust Layer (custom)

The trust layer sits above and around the Evidence Retrieval Service. It is implemented from scratch because demonstrating how it works — and why it is necessary — is the purpose of Part 4.

| Component | What it does |
|-----------|-------------|
| Prompt injection guard | Rejects queries that attempt to override the grounding instruction |
| Contradiction detection | Scans retrieved pages for conflicting values on the same observable fact |
| Claim extraction | Breaks the LLM answer into discrete verifiable assertions |
| Fact checking | Verifies each claim against the page it cites |
| Trust scoring | Combines retrieval confidence, verification rate, and contradiction penalty into a single score |
| Trusted response | Packages answer + claim table + contradictions + score + plain-English verdict |

---

## Data Flow

```
Case file (text)
  → Chunked by sentence-transformers tokeniser
  → Embedded into 384-dim dense vectors
  → Stored in ChromaDB collection

Query (text)
  → Prompt injection guard checks for override patterns
  → Embedded by sentence-transformers
  → ChromaDB returns top-K similar chunks
  → Reranked by keyword overlap
  → Grounding brief assembled
  → Anthropic SDK generates grounded answer
  → Contradiction detector scans retrieved pages
  → Claim extractor breaks answer into assertions
  → Fact checker verifies each claim against source pages
  → Trust score computed
  → Trusted response returned to frontend
```

---

## LangChain and LlamaIndex

LangChain and LlamaIndex are orchestration frameworks for AI pipelines. They are part of the planned stack and may be used inside the Evidence Retrieval Service where they help.

The boundary rule is:

- **Inside the Evidence Retrieval Service** — LangChain or LlamaIndex may handle document loading, chunking, embedding, and retrieval. This is plumbing. It does not need to be visible in the article.
- **Inside the Trust Layer** — no orchestration framework. Contradiction detection, claim extraction, fact checking, and trust scoring are always explicit custom code. This is the substance of Part 4.

If LangChain or LlamaIndex adds complexity rather than reducing it for any given step, it is not used for that step. Library use is decided per service, not per article.

---

## Local Development Fallbacks

The production targets above require external network access to HuggingFace (model download) and a working esbuild binary. Two fallbacks are active on machines where those are unavailable:

### Embedding — TF-IDF fallback

**Production target:** `sentence-transformers` loads `all-MiniLM-L6-v2` from HuggingFace and produces 384-dimensional dense vectors. ChromaDB stores and searches those vectors.

**Current local fallback:** `sklearn.TfidfVectorizer` (ngram 1–2) + `cosine_similarity`. In-memory index only; no ChromaDB. Activated when HuggingFace is unreachable (e.g. corporate SSL proxy blocking `huggingface.co`).

The trust layer, API contract, and all four trust services (contradiction, fact-check, guardrail, trust-score) are unaffected by this swap. Only the retrieval confidence values differ: TF-IDF cosine scores are in the 0.1–0.3 range; dense-vector cosine scores are in the 0.6–0.9 range. `routes.py` normalises TF-IDF scores before passing them to the trust formula so that a clean authentic query still produces a HIGH verdict.

### Frontend — CDN React fallback

**Production target:** `React + Vite`. The Vite scaffold (`vite.config.js`, `src/`) is in place.

**Current local fallback:** `sentinel/frontend/index.html` uses React 18 + Babel Standalone loaded from `unpkg.com`. No build step needed. Activated when the esbuild native binary is blocked by system security policy (MDM/Gatekeeper kills it with SIGKILL). The component logic in `index.html` mirrors `src/App.jsx`.

Neither fallback changes the API contract, the trust layer logic, or the article's argument.

---

## API Surface (Part 4)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Liveness check |
| GET | /version | Application metadata |
| POST | /api/query | Submit a detective query, receive a trusted response |

---

*Updated as each part of the series ships.*
