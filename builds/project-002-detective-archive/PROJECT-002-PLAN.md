# Project 002 — Building The Detective Archive
## Implementation Plan

---

## 1. Purpose

Project 002 is the companion codebase for **Part 3 — The Cold Case Files That Created RAG**.

It teaches Retrieval-Augmented Generation (RAG) from first principles using the same educational approach as Project 001: no external AI libraries, no vector databases, no production frameworks — only Python's standard library and the core ideas made concrete.

By the end of this project, a reader will understand every stage of a RAG pipeline: why it exists, what each component does, and how the pieces connect.

---

## 2. Relationship to Part 3 Article

| Article Chapter | Python Module |
|----------------|---------------|
| The Intelligence Gap | `01_intelligence_gap.py` |
| The Case File Splitter | `02_case_file_splitter.py` |
| The Fingerprint Engine | `03_fingerprint_engine.py` |
| The Relevance Scorer | `04_relevance_scorer.py` |
| The Evidence Archive | `05_evidence_archive.py` |
| The Retrieval Desk | `06_retrieval_desk.py` |
| The Precision Ranker | `07_precision_ranker.py` |
| The Detective's Brief | `08_detective_brief.py` |
| The Complete Detective Archive | `09_complete_archive.py` |

Each Python file is a standalone script, run at the exact moment the article introduces the matching concept. The output is the lesson.

---

## 3. Educational Philosophy

Identical to Project 001.

```
Read a chapter in the article
        ↓
Run the matching Python file
        ↓
Observe the output in your terminal
        ↓
Return to the article
        ↓
Repeat
```

### What this project does NOT use

- `langchain`, `llamaindex`, `haystack`, or any RAG framework
- `faiss`, `pinecone`, `chromadb`, or any vector database
- `numpy`, `torch`, `sentence-transformers`, or any ML library
- Any network calls or external APIs

Vectors are hand-crafted or deterministically computed. Similarity is implemented by hand. The store is an in-memory list.

The goal is understanding, not performance.

### What this project DOES assume

Readers are familiar with:
- Tokens, token IDs, and embeddings (Project 001, Part 1)
- How an LLM produces output (Project 001, Part 2)

These concepts are treated as existing knowledge. They are used but not re-explained.

### What this project does NOT cover

Part 4 concepts are deliberately excluded from this milestone:
- Verification of retrieved evidence
- Fact-checking and hallucination detection
- Guardrails and safety filters
- Trusted AI pipeline design

Those belong in Project 002's second milestone, after Part 4 is read.

---

## 4. Learning Objectives

After completing this project, the reader will be able to explain:

1. **Why RAG exists** — what the knowledge cutoff problem is and why it matters
2. **Document chunking** — how large documents are split into retrievable units and why chunk size is a design decision
3. **Document embedding** — how each chunk becomes a vector that captures its meaning
4. **Similarity search** — how cosine similarity finds the most relevant chunk for any query
5. **The vector store** — what a vector store is and how an in-memory store is built from scratch
6. **Retrieval** — how a query is embedded, compared against the store, and the top-K results are returned
7. **Reranking** — how a second pass improves precision beyond cosine similarity alone
8. **Prompt augmentation** — how retrieved evidence is inserted into the prompt before the LLM sees the question
9. **The full RAG pipeline** — how all nine steps compose into a single query → answer flow

---

## 5. Folder Structure

```
builds/project-002-detective-archive/
│
├── PROJECT-002-PLAN.md           ← this file
│
├── README.md                     ← what the build is, how to run it
│
├── case-files/
│   └── millbrook_arson_2019.txt  ← the cold case document
│
└── detective-archive/
    ├── 01_intelligence_gap.py
    ├── 02_case_file_splitter.py
    ├── 03_fingerprint_engine.py
    ├── 04_relevance_scorer.py
    ├── 05_evidence_archive.py
    ├── 06_retrieval_desk.py
    ├── 07_precision_ranker.py
    ├── 08_detective_brief.py
    └── 09_complete_archive.py
```

---

## 6. Investigation Milestones

All milestones share a continuous detective narrative: **The Unsolved Cold Cases of Millbrook County**.

The Police Department's records system only holds current investigations. When Detective Morgan needs to answer questions about old cases — cases solved before the current system existed — the LLM has no knowledge of them. The archive must be searched manually, the relevant files retrieved, and the briefing augmented with what was found.

---

### `01_intelligence_gap.py` — The Intelligence Gap

**Concept:** Why an LLM cannot answer questions about information outside its training data.

**Narrative:** Detective Morgan asks about the Millbrook Arson of 2019. The department's intelligence system — a `SimulatedLLM` with a training cutoff of December 2018 — draws a blank. The answer exists in a case file on disk. The system simply has no access to it.

**Output:** The LLM's knowledge gap exposed side by side with the answer that exists in the archive. The gap motivates everything that follows.

**AI Connection:** LLMs are frozen at their training cutoff. Any document or event that postdates training — or was never included — is invisible to them. RAG was invented to close this gap.

---

### `02_case_file_splitter.py` — The Case File Splitter

**Concept:** How large documents are split into fixed-size, overlapping chunks for indexing.

**Narrative:** The archive room holds thick case folders. Each must be broken into individually numbered pages — small enough to retrieve precisely, large enough to hold a coherent thought.

**Output:** Three configurations demonstrated against the Millbrook Arson case file (309 words):
- Config A: `chunk_size=15, overlap=0` → 21 pages (too granular — sentences broken)
- Config B: `chunk_size=200, overlap=0` → 2 pages (too coarse — no precision)
- Config C: `chunk_size=60, overlap=15` → 7 pages (recommended — overlap preserves boundary sentences)

**AI Connection:** Chunk size and overlap are among the most consequential design decisions in a RAG pipeline. They cannot be changed after the archive is built without re-indexing.

---

### `03_fingerprint_engine.py` — The Fingerprint Engine

**Concept:** How each chunk is converted into a passage-level vector that represents what the page is about.

**Bridge from Project 001:** Project 001 introduced embeddings at the token level — one vector per word. This milestone embeds at the passage level — one vector per chunk. The question shifts from "what does this word mean?" to "what is this page about?"

**Narrative:** The archivist assigns each case file page a fingerprint — 5 numbers encoding which semantic categories dominate: incident, forensic, timeline, investigation, conclusion.

**Output:** All 7 page fingerprints displayed as bar charts. Two comparisons demonstrate the principle: pages with different content produce different fingerprints; pages that share content (due to overlap) produce similar ones.

**AI Connection:** Production RAG systems use a sentence encoder to produce dense embeddings of 384–768+ dimensions. This milestone uses 5 keyword-scored dimensions so every number is readable and every score is traceable.

---

### `04_relevance_scorer.py` — The Relevance Scorer

**Concept:** Cosine similarity — how two vectors are scored for relevance.

**Educational note:** The fingerprint engine in this project is a simplified educational implementation. Real-world embedding models generate these vectors automatically using pre-trained neural networks. The objective here is to understand how similarity is measured, not how production embeddings are generated.

**Narrative:** Detective Morgan holds a query fingerprint. The archivist measures how closely each page fingerprint points in the same direction. Cosine similarity is the measuring tape.

**Output:** A step-by-step walkthrough showing dot product, vector magnitudes, and cosine similarity calculation for the top-ranked page. All 7 pages scored and ranked. The accelerant query surfaces pages 4, 3, 5 (forensic pages); the conclusion page scores 0.0000.

**AI Connection:** Cosine similarity is the standard relevance metric in vector search. Magnitude normalisation ensures that a page mentioning "fire" fifty times does not outrank a page mentioning "petroleum distillate" and "ignition" once.

---

### `05_evidence_archive.py` — The Evidence Archive

**Concept:** An in-memory vector store: a collection of (text, fingerprint) pairs with `add()` and `search()` methods.

**Narrative:** The archive room is now a proper system. Every case file page has been fingerprinted and filed. The archivist can answer any query: "Give me the three most relevant pages."

**Output:** 7 pages indexed with live progress display. A query fingerprint submitted directly to the archive. All 7 scores displayed. Top 3 results returned with text excerpts. The archive interface exposed: it accepts fingerprints, not questions.

**AI Connection:** Production vector stores (FAISS, Pinecone, Chroma) implement the same interface — `index(id, vector)` and `query(vector, k)` — at scale and speed. The contract is identical.

---

### `06_retrieval_desk.py` — The Retrieval Desk

**Concept:** The retrieval pipeline — the first milestone where a natural language question retrieves evidence.

**Narrative:** Detective Morgan submits a question in plain language. The desk embeds it, queries the archive, and returns evidence. The archive never sees the question — only the fingerprint.

**Output:** Two questions demonstrated end to end:
- Q1: "What accelerant was used?" → fingerprint `[0.33, 0.33, 0.0, 0.0, 0.0]` → pages [4, 3, 5]
- Q2: "Were any suspects identified?" → fingerprint `[0.0, 0.0, 0.0, 0.67, 0.0]` → pages [6, 5, 7]

No pages overlap between the two result sets — the retriever responds to meaning.

**AI Connection:** In production, the retrieval step calls a sentence encoder to embed the query using the same model used to embed documents at index time. Query and document share the same vector space.

---

### `07_precision_ranker.py` — The Precision Ranker

**Concept:** Reranking — a second scoring pass that checks whether the retrieved pages directly contain the specific terms the detective used.

**Narrative:** Fingerprint similarity finds pages about the right topic. The Precision Ranker finds the page that actually contains the answer.

**Scoring formula:** `combined = 0.6 × retrieval_score + 0.4 × term_score`

Where `term_score` measures how many content words from the question (words of 5+ characters) appear verbatim in the page.

**Output:** Two questions demonstrate both outcomes:
- Q1 (accelerant): order unchanged, but gap between #1 and #2 widens 6× (P4 contains "accelerant" literally; P3 does not)
- Q2 (suspects): order reversed — P5 overtakes P6 because P5 contains "identified" and "investigation" verbatim while P6 contains neither despite a higher retrieval score

**AI Connection:** Production rerankers are cross-encoder models that read question and document together. They are slower than bi-encoders but more precise. The term overlap approach demonstrates the same principle at educational scale.

---

### `08_detective_brief.py` — The Detective's Brief

**Concept:** Prompt augmentation and grounding — assembling the complete prompt delivered to the LLM.

**Narrative:** The archivist hands the retrieved pages to Detective Morgan and says: "Read these first. Then answer the question." The brief places the evidence before the LLM and tells it to stay within the evidence.

**Three versions demonstrated:**
- V1: Question only → LLM cannot answer (knowledge gap from Milestone 1)
- V2: Evidence + question, no grounding → LLM answers, but speculation mixes in (2 of 5 sentences ungrounded)
- V3: Grounding instruction + evidence + question → every sentence traceable to a page number

**Output:** Each brief displayed in full. V2 annotated sentence by sentence to show which claims come from evidence and which do not.

**AI Connection:** The grounding instruction is part of the system prompt in production RAG. It is the primary mechanism responsible for reducing hallucination: the retrieval pipeline finds the evidence; the grounding instruction ensures the model uses it and nothing else.

---

### `09_complete_archive.py` — The Complete Detective Archive

**Concept:** The full RAG pipeline — all nine steps assembled into a single coherent system.

**Narrative:** The Millbrook cold case archive is built end to end. Morgan asks a question. Nine steps run. A grounded answer emerges from the case files.

**Pipeline:**
```
Document intake (build time):
  [1] Load         case file → text
  [2] Split        text → 7 pages
  [3] Fingerprint  pages → 7 vectors
  [4] Index        vectors → evidence archive

Query processing (query time):
  [5] Receive      question → query fingerprint
  [6] Retrieve     fingerprint → top-K candidates
  [7] Rerank       candidates → ranked evidence
  [8] Brief        evidence + grounding → prompt
  [9] LLM          prompt → grounded answer
```

**LLM boundary:** Project 001 already implemented the internals (tokeniser → embedding lookup → transformer → output distribution). This pipeline stops at the boundary. The interface is `llm.ask(brief)`. In production, `SimulatedLLM` is replaced with any real model client without changing any other step.

**Output:** Each step traced with its input and output. Before/after comparison showing the knowledge gap (Milestone 1) closed by the full pipeline. Pipeline recap in nine lines.

**AI Connection:** This is what every production RAG system does. The sophistication is in the embedding model, the vector store at scale, and the LLM quality — but the pipeline is identical.

---

## 7. Implementation Order

Each milestone builds on the previous one. Implement in the order below.

| Step | File | Depends On |
|------|------|-----------|
| 1 | `01_intelligence_gap.py` | nothing — establishes the problem |
| 2 | `02_case_file_splitter.py` | nothing — standalone splitter |
| 3 | `03_fingerprint_engine.py` | chunking concepts from step 2 |
| 4 | `04_relevance_scorer.py` | fingerprinting from step 3 |
| 5 | `05_evidence_archive.py` | similarity from step 4 |
| 6 | `06_retrieval_desk.py` | archive from step 5 |
| 7 | `07_precision_ranker.py` | retrieval from step 6 |
| 8 | `08_detective_brief.py` | reranking from step 7 |
| 9 | `09_complete_archive.py` | all previous milestones |

---

## Constraints

- Python 3.8+ only. No third-party packages.
- Each file runs standalone: `python3 detective-archive/01_intelligence_gap.py`
- All vectors are computed with `math.sqrt` from stdlib.
- The detective narrative must be present in every file — header block, print statements, and closing summary.
- No Part 4 concepts introduced anywhere in this milestone.
