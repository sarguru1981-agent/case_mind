"""Evidence Retrieval Service — RAG Pipeline.

Embedding backend: TF-IDF (sklearn) — no external model download required.
Upgrade path: swap _Embedder for SentenceTransformer("all-MiniLM-L6-v2")
              when HuggingFace is accessible from the deployment network.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic

_LLM_MODEL   = "claude-sonnet-4-6"
_CHUNK_WORDS = 80
_OVERLAP     = 20
_TOP_K       = 4


class _Index:
    """TF-IDF index for one case file."""
    def __init__(self, chunks: list[str]) -> None:
        self.chunks     = chunks
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.matrix     = self.vectorizer.fit_transform(chunks)

    def query(self, question: str, k: int = _TOP_K) -> list[tuple[str, float]]:
        q_vec  = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.matrix)[0]
        top_k  = int(min(k, len(self.chunks)))
        idx    = np.argsort(scores)[-top_k:][::-1]
        return [(self.chunks[i], float(scores[i])) for i in idx]


_indexes: dict[str, _Index] = {}


def _chunk(text: str) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + _CHUNK_WORDS]))
        i += _CHUNK_WORDS - _OVERLAP
    return [c for c in chunks if len(c) > 20]


def _get_index(case_file: str) -> _Index:
    if case_file not in _indexes:
        chunks = _chunk(Path(case_file).read_text())
        _indexes[case_file] = _Index(chunks)
    return _indexes[case_file]


def _rerank(question: str, hits: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Secondary keyword-overlap rerank on top of TF-IDF scores."""
    query_words = set(re.findall(r"\w+", question.lower()))
    ranked = []
    for doc, score in hits:
        doc_words = set(re.findall(r"\w+", doc.lower()))
        overlap   = len(query_words & doc_words) / max(len(query_words), 1)
        ranked.append((doc, 0.7 * score + 0.3 * overlap))
    return sorted(ranked, key=lambda x: x[1], reverse=True)


def _grounding_brief(question: str, pages: list[str]) -> str:
    evidence = "\n\n".join(f"[Page {i + 1}]\n{p}" for i, p in enumerate(pages))
    return (
        "You are a police evidence analyst. Answer the detective's question using ONLY "
        "the evidence pages below. Cite page numbers inline. Do not speculate beyond "
        "the evidence.\n\n"
        f"EVIDENCE:\n{evidence}\n\n"
        f"QUESTION: {question}\n\nANSWER:"
    )


def retrieve_and_answer(question: str, case_file: str) -> tuple[str, list[str], float]:
    """Returns (answer_text, evidence_pages, retrieval_confidence)."""
    index  = _get_index(case_file)
    hits   = index.query(question)
    ranked = _rerank(question, hits)

    evidence_pages        = [doc for doc, _ in ranked]
    retrieval_confidence  = float(np.mean([s for _, s in ranked])) if ranked else 0.0
    brief          = _grounding_brief(question, evidence_pages)

    client  = anthropic.Anthropic()
    message = client.messages.create(
        model      = _LLM_MODEL,
        max_tokens = 512,
        messages   = [{"role": "user", "content": brief}],
    )
    return message.content[0].text.strip(), evidence_pages, retrieval_confidence
