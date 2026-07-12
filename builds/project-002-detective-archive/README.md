# Build 2 — Building The Detective Archive

> **Starting here?**
>
> Run `detective-archive/01_intelligence_gap.py` and read the output.
> Then open the matching article chapter.

---

## What Is This?

A step-by-step construction of the Police Department's Detective Archive —
an educational RAG (Retrieval-Augmented Generation) system built from scratch
using only Python's standard library.

Each file builds one component of the archive. By the final milestone, the
archive receives a detective's question and returns a grounded answer drawn
from retrieved cold case documents.

---

## Which Article Does This Support?

| Build | Article |
|-------|---------|
| Part 3 | **The Cold Case Files That Created RAG** |

---

## How to Run

```bash
# From the repo root
cd builds/project-002-detective-archive

# Run any milestone directly
python3 detective-archive/01_intelligence_gap.py
```

No dependencies to install. Python 3.8+ is all you need.

---

## What Each File Builds

### The Detective Archive (`detective-archive/`)

| File | Milestone | What You Build |
|------|-----------|----------------|
| `01_intelligence_gap.py` | The Intelligence Gap | The knowledge cutoff problem — why the archive is needed |
| `02_case_file_splitter.py` | The Case File Splitter | A configurable text splitter with chunk size and overlap |
| `03_fingerprint_engine.py` | The Fingerprint Engine | Passage-level embeddings — converting each page into a 5-dimensional vector |
| `04_relevance_scorer.py` | The Relevance Scorer | Cosine similarity from first principles — dot product, magnitudes, ranked scores |
| `05_evidence_archive.py` | The Evidence Archive | In-memory vector store — add pages, search by query fingerprint, return top K |
| `06_retrieval_desk.py` | The Retrieval Desk | Natural language retrieval — question in, top-K evidence pages out |
| `07_precision_ranker.py` | The Precision Ranker | Reranking — term overlap second pass, 60/40 combined score |
| `08_detective_brief.py` | The Detective's Brief | Prompt assembly — grounding instruction, evidence pages, question |
| `09_complete_archive.py` | The Complete Detective Archive | Full RAG pipeline end to end — load, split, fingerprint, index, retrieve, rerank, brief, answer |

---

## Important Note

These implementations are **educational demonstrations**, not production RAG code.

- The LLM is simulated using a Python class (`SimulatedLLM`) — not a real language model.
- Vectors are hand-crafted or computed using Python's `math` module.
- The vector store is an in-memory list.
- No external libraries are used at any point.

Real RAG systems use sentence encoders, vector databases, and large language
models. This build demonstrates the same ideas at a scale where every value
is readable and every step is traceable.

The goal is understanding, not performance.
