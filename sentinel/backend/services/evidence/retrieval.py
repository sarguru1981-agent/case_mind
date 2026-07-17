"""Evidence Retrieval Service — RAG Pipeline.

Embedding backend: TF-IDF (sklearn) — no external model download required.
Upgrade path: swap _Embedder for SentenceTransformer("all-MiniLM-L6-v2")
              when HuggingFace is accessible from the deployment network.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_CHUNK_WORDS = 80
_OVERLAP     = 20
_TOP_K       = 4


class _Index:
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
    query_words = set(re.findall(r"\w+", question.lower()))
    ranked = []
    for doc, score in hits:
        doc_words = set(re.findall(r"\w+", doc.lower()))
        overlap   = len(query_words & doc_words) / max(len(query_words), 1)
        ranked.append((doc, 0.7 * score + 0.3 * overlap))
    return sorted(ranked, key=lambda x: x[1], reverse=True)


def retrieve_evidence(question: str, case_file: str) -> tuple[list[str], float]:
    """Return (evidence_pages, retrieval_confidence). No LLM call."""
    index  = _get_index(case_file)
    hits   = index.query(question)
    ranked = _rerank(question, hits)
    evidence_pages       = [doc for doc, _ in ranked]
    retrieval_confidence = float(np.mean([s for _, s in ranked])) if ranked else 0.0
    return evidence_pages, retrieval_confidence
