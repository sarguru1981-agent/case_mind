# Part 4 — Implementation Plan

**Article:** The Wrong Evidence That Made RAG Hallucinate
**Application:** CaseMind Sentinel v1.0
**Folder:** `sentinel/`

---

## Objective

Part 4 builds the first working version of CaseMind Sentinel.

The article demonstrates a specific failure mode of RAG systems: a pipeline that is technically correct in every step — grounding instruction followed, evidence retrieved, answer cited — but answers confidently from corrupted evidence. The reader must understand what goes wrong and why the standard RAG pipeline cannot detect it.

The solution is a trust layer that runs alongside the pipeline and produces a verifiable, scored response rather than a raw answer.

---

## Naming Convention

The underlying technique is RAG (Retrieval-Augmented Generation). Inside CaseMind Sentinel the service is called the **Evidence Retrieval Service**. Both terms appear in this document:

- **RAG Pipeline / RAG** — used when discussing the technical concept
- **Evidence Retrieval Service** — used when referring to the service in CaseMind Sentinel

---

## What We Use Libraries For

The Evidence Retrieval Service is not rebuilt from scratch. Part 3 and the `learn/project-002-detective-archive/` educational project already showed how the RAG Pipeline works step by step. In CaseMind Sentinel, we use real libraries for the Evidence Retrieval Service and focus implementation effort on the trust layer.

### sentence-transformers

Used to embed case file chunks and queries into dense 384-dimensional vectors. Provides real semantic similarity rather than the keyword fingerprint used in the educational project.

```
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode(chunk_text)
```

### ChromaDB

Used as the persistent vector store. Stores embeddings and retrieves the top-K most similar chunks for a given query using approximate nearest-neighbour search.

```
collection.add(documents=[chunk], embeddings=[embedding], ids=[chunk_id])
results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
```

### Anthropic SDK + Portkey AI Gateway

Used to generate a grounded answer from the retrieved evidence pages. CaseMind Sentinel uses the Portkey AI Gateway through Anthropic-compatible API configuration. The Anthropic SDK is pointed at the Portkey base URL; the `x-portkey-provider` header identifies the model provider. The application holds only the Portkey API key.

```
client = anthropic.Anthropic(
    auth_token=PORTKEY_API_KEY,
    base_url=PORTKEY_BASE_URL,
    default_headers={"x-portkey-provider": PORTKEY_PROVIDER},
)
response = client.messages.create(
    model=PORTKEY_MODEL,
    messages=[{"role": "user", "content": brief}]
)
```

### FastAPI + Pydantic

FastAPI handles the REST API. Pydantic validates all request and response shapes. No manual parsing.

### LangChain or LlamaIndex

Used inside the Evidence Retrieval Service where they reduce boilerplate without hiding trust layer logic. Candidate uses: document loading, text splitting, embedding pipeline, retrieval chain assembly. The decision of whether to use them for a specific step is made when that step is implemented — whichever approach is cleaner for the article.

LangChain and LlamaIndex are **not** used inside the trust layer. Contradiction detection, claim extraction, fact checking, and trust scoring are always explicit custom code.

### React + Vite

React renders the frontend command center. Vite provides fast local development. No framework overhead beyond what React requires.

---

## Final Library List

Production targets. See *Local Development Fallbacks* in `docs/architecture.md` for current substitutions active on machines where HuggingFace or esbuild is unavailable.

| Category | Library | Status | Used For |
|----------|---------|--------|---------|
| API server | FastAPI | **active** | REST endpoints |
| Data models | Pydantic | **active** | Request/response validation |
| Configuration | python-dotenv | **active** | Environment variables |
| Embeddings | sentence-transformers | target / TF-IDF fallback active | Dense vector encoding |
| Vector store | ChromaDB | target / not active (TF-IDF in-memory) | Similarity search |
| LLM gateway | anthropic SDK + Portkey AI Gateway | **active** (needs `PORTKEY_API_KEY`) | Anthropic-compatible API config; gateway routes to model provider |
| Orchestration | LangChain or LlamaIndex | not yet used | Evidence Retrieval Service plumbing where useful |
| Frontend framework | React | **active** (CDN fallback) | Component-based UI |
| Frontend build | Vite | target / CDN fallback active | Local dev server and bundler |

---

## What We Implement Ourselves

The trust layer is implemented from scratch. This is intentional.

The purpose of Part 4 is to show how and why trust checking works. If the trust logic is hidden inside a library call, the article cannot make its argument. The reader must be able to read the code and understand each decision.

### Prompt Injection Guard

Runs before retrieval. Checks the incoming query for known override patterns such as:

- "ignore previous instructions"
- "you are now a different system"
- "disregard the evidence"

If a match is found, the request is rejected before any retrieval or LLM call occurs. No trust score is needed — the query never reaches the pipeline.

```python
def check_injection(query: str) -> bool:
    # returns True if injection detected
```

### Contradiction Detection

Runs on the retrieved evidence pages after retrieval, before the LLM call.

Scans each page for observable facts in predefined categories (accelerant type, incident date, fire origin location, etc.). If two pages record different values for the same category, a contradiction is raised. The detector does not determine which page is correct — it reports that the pages disagree.

Output: `ContradictionReport` with a list of contradictions and a penalty score (1.0 = no contradictions; -0.25 per finding, floored at 0.0).

```python
detector = ContradictionDetector()
report = detector.detect(evidence_pages)
# report.count, report.penalty, report.contradictions
```

### Claim Extraction

Runs on the LLM answer after generation.

Breaks the answer text into discrete factual assertions. Strips meta-framing prefixes. Splits on sentence boundaries. Discards disclaimers and short fragments. Extracts inline page citations. Scores each sentence by how factually substantive it looks (presence of claim verbs, page citations, measurements).

Output: `list[Claim]` — each with `text`, `cited_page`, and `confidence`.

```python
claims = extract_claims(answer)
# [Claim(text="...", cited_page=4, confidence=0.90), ...]
```

### Fact Checking

Runs on the extracted claims against the retrieved evidence pages.

For each claim, locates the cited page (or falls back to the best-matching page by content-word overlap). Computes what fraction of the claim's significant words appear on that page. A claim is verified if the overlap meets the threshold (default 0.65).

Output: `FactCheckReport` with `verification_rate` and a `VerifiedClaim` per input claim.

```python
report = verify_claims(claims, evidence_pages)
# report.verification_rate, report.verified_count, report.results
```

### Trust Score

Combines three sub-scores into a single 0.0–1.0 value:

```
trust_score = (0.40 × retrieval_confidence)
            + (0.35 × verification_rate)
            + (0.25 × contradiction_penalty)
```

- `retrieval_confidence` — average rerank score of the top-K retrieved pages
- `verification_rate` — fraction of extracted claims verified by fact checking
- `contradiction_penalty` — output of the contradiction detector (1.0 = no contradictions)

Verdict thresholds:
- `>= 0.75` → HIGH
- `>= 0.50` → MEDIUM
- `< 0.50`  → LOW / REVIEW REQUIRED

### Trusted Response

The final output returned by the API. Packages all outputs into one structured object.

```python
@dataclass
class TrustedResponse:
    question:       str
    answer:         str
    claims:         list[VerifiedClaim]
    contradictions: ContradictionReport
    trust_score:    float
    verdict:        str   # HIGH / MEDIUM / LOW
```

---

## Frontend Input / Output

### Input — Query Panel

A single text input for the detective's question, with a case file selector.

```
[ Case file: Millbrook Arson 2019 ▾ ]

[ What accelerant was used in the fire?          ]  [ Submit ]
```

### Output — Trusted Response Panel

The frontend renders the full `TrustedResponse` object in four sections:

**Answer**
The grounded answer text from the LLM.

**Trust Score**
A colour-coded badge and numeric score:
- Green: HIGH (≥ 0.75)
- Amber: MEDIUM (≥ 0.50)
- Red: LOW (< 0.50)

**Claim Table**
One row per extracted claim showing: claim text, cited page, verified (✓/✗), overlap score.

**Contradictions**
If any — the category, the two conflicting values, and which pages they came from.

---

## Implementation Milestones

### Milestone 01 — Backend Foundation

- FastAPI application with `/health` and `/version` endpoints
- Pydantic settings loaded from `.env`
- Backend runs: `uvicorn main:app --reload`

**Deliverable:** `GET /health` returns `{ status: ok, version: 1.0.0 }`

---

### Milestone 02 — Evidence Retrieval Service

*Implements the RAG Pipeline using real libraries.*

- sentence-transformers model loaded
- Case file loaded, chunked, embedded (LangChain/LlamaIndex text splitter if useful)
- ChromaDB collection created and populated
- Query embedded and top-K chunks retrieved via ChromaDB similarity search
- Chunks reranked by keyword overlap (custom reranker — not delegated to a framework)
- Grounding brief assembled
- Anthropic SDK generates grounded answer

**Deliverable:** `POST /api/query` returns a raw grounded answer (no trust layer yet)

---

### Milestone 03 — Wrong Evidence Scenario

- Authentic case file (`millbrook_arson_2019.txt`) indexed in collection A
- Corrupted case file (`millbrook_arson_corrupted.txt`) indexed in collection B
- Both collections queried with the same question
- Both return confident, grounded, conflicting answers

**Deliverable:** The pipeline demonstrates the core problem — both answers look correct, one is wrong.

---

### Milestone 04 — Contradiction Detection

- `ContradictionDetector` implemented
- Runs on retrieved evidence pages before LLM call
- `ContradictionReport` returned with contradiction list and penalty score

**Deliverable:** Mixed-evidence query returns a report identifying the accelerant conflict.

---

### Milestone 05 — Claim Extraction

- `extract_claims(answer)` implemented
- Strips meta-framing, splits sentences, filters disclaimers
- Extracts cited pages, scores claim confidence

**Deliverable:** LLM answer broken into 2–4 verifiable `Claim` objects.

---

### Milestone 06 — Fact Checking

- `verify_claims(claims, evidence_pages)` implemented
- Each claim checked against its cited page by content-word overlap
- `FactCheckReport` returned with verification rate

**Deliverable:** Corrupted answer fails verification against authentic evidence.

---

### Milestone 07 — Prompt Injection Guard

- `check_injection(query)` implemented
- Override patterns checked before retrieval
- Injected query rejected with a clear error before any LLM call

**Deliverable:** `POST /api/query` with an injection attempt returns `{ status: "INJECTION_DETECTED", message: "Query rejected: prompt injection pattern detected." }`.

---

### Milestone 08 — Trust Score + Trusted Response

- `TrustScore` computed from retrieval confidence, verification rate, contradiction penalty
- `TrustedResponse` assembled
- `POST /api/query` returns the full trusted response

**Deliverable:** Authentic query → trust score HIGH. Corrupted query (clean but fabricated evidence file) → trust score HIGH with a different answer — demonstrating that the pipeline cannot self-detect corrupted evidence without the trust layer's contradiction detection across sources.

---

### Milestone 09 — Frontend

- React + Vite scaffold running at `localhost:5173`
- Query input panel connected to `POST /api/query`
- Trusted response panel renders answer, trust badge, claim table, contradiction list

**Deliverable:** Full end-to-end — type a question, receive a trusted, scored, verifiable response.

---

## File Map

```
sentinel/
├── backend/
│   ├── main.py                         FastAPI app, CORS, routes
│   ├── config/
│   │   └── settings.py                 Pydantic settings from .env
│   ├── api/
│   │   └── routes.py                   POST /api/query endpoint
│   ├── models/
│   │   └── trust_models.py             Claim, Contradiction,
│   │                                   InvestigationRequest, TrustedResponse
│   └── services/
│       ├── evidence/
│       │   └── retrieval.py            Evidence Retrieval Service
│       │                               (RAG Pipeline: sentence-transformers +
│       │                                ChromaDB + Anthropic SDK +
│       │                                LangChain/LlamaIndex where useful)
│       └── trust/
│           ├── contradiction.py        ContradictionDetector         (custom)
│           ├── fact_check.py           extract_claims, verify_claims (custom)
│           ├── guardrail.py            check_injection               (custom)
│           └── trust_score.py          compute_trust_score,          (custom)
│                                       build_trusted_response
│
├── frontend/
│   ├── index.html                      Live application (CDN React + Babel — active fallback)
│   │                                   Case selector, trust badge, claim table, contradiction
│   │                                   panel, injection rejection panel
│   ├── src/
│   │   └── App.jsx                     Production React scaffold (Vite target — not yet built)
│   ├── vite.config.js
│   └── package.json
│
└── data/
    └── case-files/
        ├── millbrook_arson_2019.txt        Authentic case file
        └── millbrook_arson_corrupted.txt   Corrupted variant (demonstrates the problem)
```
