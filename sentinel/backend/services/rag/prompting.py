from __future__ import annotations


def build_grounding_prompt(question: str, evidence_pages: list[str]) -> str:
    """Assemble the grounding brief sent to the LLM."""
    evidence = "\n\n".join(f"[Page {i + 1}]\n{p}" for i, p in enumerate(evidence_pages))
    return (
        "You are a police evidence analyst. Answer the detective's question using ONLY "
        "the evidence pages below. Cite page numbers inline. Do not speculate beyond "
        "the evidence.\n\n"
        f"EVIDENCE:\n{evidence}\n\n"
        f"QUESTION: {question}\n\nANSWER:"
    )
