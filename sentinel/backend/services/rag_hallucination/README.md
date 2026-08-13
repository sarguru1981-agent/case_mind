# RAG Hallucination Service

Trust layer for CaseMind Sentinel. Verifies every LLM-generated answer before it reaches the detective.

---

## What This Package Does

Implements the trustworthy RAG pipeline: after the LLM generates an answer, this service checks for prompt injection, contradictions in the evidence, claim-level fact verification, and produces a scored verdict.

Introduced in Part 4: *The Wrong Evidence That Made RAG Hallucinate*.

---

## Files

### `guardrail.py`

Prompt injection guard. Screens the incoming question before any LLM call is made.

Matches against 9 regex patterns covering common injection techniques (role overrides, instruction leakage, jailbreak attempts).

**Public API:**

```python
from services.rag_hallucination.guardrail import check_injection

if check_injection(question):
    # reject — return INJECTION_DETECTED status
```

---

### `contradiction.py`

Contradiction detector. Scans retrieved evidence pages for conflicting facts across three forensic categories.

| Rule | What It Detects |
|------|-----------------|
| `accelerant` | Conflicting mentions of accelerant presence or absence |
| `fire_origin` | Conflicting origin location statements |
| `incident_date` | Conflicting date references |

**Public API:**

```python
from services.rag_hallucination.contradiction import ContradictionDetector

detector = ContradictionDetector()
report = detector.detect(evidence_pages)
# report.count          — number of contradictions found
# report.contradictions — list of Contradiction objects
# report.penalty        — 1.0 if clean, 0.0 if any contradiction detected
```

---

### `fact_check.py`

Claim extractor and verifier. Breaks the LLM answer into individual sentences and checks each one against the evidence pages.

A claim is considered verified if the word overlap between the claim and any evidence page exceeds 0.40 (Jaccard similarity on lowercase token sets).

**Public API:**

```python
from services.rag_hallucination.fact_check import extract_claims, verify_claims

claims = extract_claims(answer)
report = verify_claims(claims, evidence_pages)
# report.verification_rate — fraction of claims verified (0.0–1.0)
# report.results           — list of Claim objects with verified status
```

---

### `trust_score.py`

Trust score computation and trusted response assembly.

**Trust formula:**

```
trust_score = 0.40 × retrieval_confidence
            + 0.35 × verification_rate
            + 0.25 × contradiction_penalty
```

If any contradiction is detected (`contradiction_penalty < 1.0`), the score is capped at 0.49, forcing a `LOW / REVIEW REQUIRED` verdict regardless of other factors.

**Verdicts:**

| Verdict | Condition |
|---------|-----------|
| `HIGH` | score ≥ 0.75 |
| `MEDIUM` | score ≥ 0.50 |
| `LOW / REVIEW REQUIRED` | score < 0.50, or any contradiction detected |

**Public API:**

```python
from services.rag_hallucination.trust_score import build_trusted_response

response = build_trusted_response(
    question, answer, evidence_pages,
    contradiction_report, fact_report, retrieval_confidence
)
```

Returns a `TrustedResponse` Pydantic model containing the answer, claims, contradictions, trust score, and verdict.

---

## Where This Fits

```
api/routes.py
    → services/rag/                               (retrieve evidence, build prompt)
    → services/llm/client.py                      (generate answer)
    → services/rag_hallucination/contradiction    (check evidence pages for conflicts)
    → services/rag_hallucination/fact_check       (verify answer claims against evidence)
    → services/rag_hallucination/trust_score      (score and assemble trusted response)
```

See the [RAG service](../rag/README.md) for the retrieval pipeline that runs before this layer.
