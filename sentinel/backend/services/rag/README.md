# RAG Service

Production evidence retrieval pipeline for CaseMind Sentinel.

---

## What This Package Does

Implements the Retrieval-Augmented Generation (RAG) pipeline: given a detective's question and a case file path, it retrieves the most relevant evidence passages and assembles a grounded prompt for the LLM.

---

## Files

### `retrieval.py`

Retrieves the top-K most relevant evidence passages from a case file.

**Algorithm:**

1. Load and chunk the case file into overlapping 80-word passages with a 20-word overlap
2. Build a TF-IDF vector space from all passages
3. Score each passage against the query using cosine similarity
4. Rerank the top candidates using `0.7 × cosine_score + 0.3 × word_overlap`
5. Return the top-4 passages and a retrieval confidence score

**Public API:**

```python
from services.rag.retrieval import retrieve_evidence

evidence_pages, retrieval_confidence = retrieve_evidence(question, case_file_path)
```

- `evidence_pages` — list of up to 4 passage strings
- `retrieval_confidence` — raw TF-IDF cosine score for the top result (typically in the 0.1–0.3 range)

The caller in `api/routes.py` normalises retrieval confidence before passing it to the trust formula:
`normalised_rc = min(1.0, retrieval_confidence / 0.25)`

---

### `prompting.py`

Assembles retrieved evidence pages into a grounded prompt for the LLM.

**Public API:**

```python
from services.rag.prompting import build_grounding_prompt

prompt = build_grounding_prompt(question, evidence_pages)
```

The grounding prompt instructs the LLM to answer only from the provided evidence and to refuse to speculate beyond it.

---

## Where This Fits

```
api/routes.py
    → services/rag/retrieval.py          (retrieve evidence passages)
    → services/rag/prompting.py          (build grounded prompt)
    → services/llm/client.py             (call LLM via Portkey)
    → services/rag_hallucination/        (verify and score the response)
```

See the [RAG Hallucination service](../rag_hallucination/README.md) for the trust layer that runs after the LLM answer is generated.
