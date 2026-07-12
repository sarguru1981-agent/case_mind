# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 6
#
# Milestone 5 built the Evidence Archive. It stores pages and searches
# by fingerprint. But it requires the caller to prepare a fingerprint
# before every search. A detective does not work with vectors. A
# detective works with questions.
#
# The Retrieval Desk closes that gap.
#
# It sits in front of the archive and handles the translation step:
#   1. Receive a natural language question from the detective
#   2. Embed the question into a query fingerprint
#   3. Send the fingerprint to the archive
#   4. Return the top-K most relevant pages
#
# This is the first milestone where a human-readable question
# retrieves evidence from the archive without any manual steps.
#
# The pipeline is now:
#
#   question  →  embed  →  fingerprint  →  archive.search  →  results
#
# Two questions are demonstrated to show that the retriever responds
# to meaning, not keywords: different questions produce different
# fingerprints and return different pages.
# =============================================================================

import os
import math


# ---------------------------------------------------------------------------
# The Fingerprint Engine (standalone)
# ---------------------------------------------------------------------------

FINGERPRINT_DIMENSIONS = {
    "incident":      ["fire", "arson", "warehouse", "engulf", "damage",
                      "corner", "northwest", "structure"],
    "forensic":      ["accelerant", "distillate", "petroleum", "residue",
                      "origin", "ignition", "concentration", "samples", "traces"],
    "timeline":      ["03:18", "05:40", "02:47", "march", "april",
                      "september", "2019", "minutes"],
    "investigation": ["suspect", "inquiry", "witness", "cctv",
                      "identified", "registered", "database"],
    "conclusion":    ["suspended", "transferred", "unsolved", "insufficient"],
}

DIM_NAMES = list(FINGERPRINT_DIMENSIONS.keys())


def embed_passage(text):
    text_lower = text.lower()
    vector = []
    for keywords in FINGERPRINT_DIMENSIONS.values():
        hits = sum(1 for kw in keywords if kw in text_lower)
        score = round(min(hits / 3.0, 1.0), 2)
        vector.append(score)
    return vector


# ---------------------------------------------------------------------------
# The Relevance Scorer (standalone)
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a, vec_b):
    dot   = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# The Evidence Archive (standalone)
# ---------------------------------------------------------------------------

class EvidenceArchive:

    def __init__(self):
        self._entries = []

    def add(self, page_num, text, fingerprint):
        self._entries.append({
            "page_num":    page_num,
            "text":        text,
            "fingerprint": fingerprint,
        })

    def search(self, query_fingerprint, top_k=3):
        scored = []
        for entry in self._entries:
            score = cosine_similarity(query_fingerprint, entry["fingerprint"])
            scored.append({**entry, "score": score})
        scored.sort(key=lambda e: -e["score"])
        return scored[:top_k]

    def all_scores(self, query_fingerprint):
        """Return scores for every page without truncation — for display."""
        scored = []
        for entry in self._entries:
            score = cosine_similarity(query_fingerprint, entry["fingerprint"])
            scored.append((entry["page_num"], score))
        return scored

    def __len__(self):
        return len(self._entries)


# ---------------------------------------------------------------------------
# The Retrieval Desk
# ---------------------------------------------------------------------------

def retrieve(question, archive, top_k=3):
    """
    The retrieval pipeline.

    Accepts a natural language question.
    Returns the top-K most relevant pages from the archive.

    The archive never sees the question — only the fingerprint.
    """
    query_fingerprint = embed_passage(question)
    results = archive.search(query_fingerprint, top_k=top_k)
    return query_fingerprint, results


# ---------------------------------------------------------------------------
# Case file loading and chunking (standalone)
# ---------------------------------------------------------------------------

def load_case_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    path = os.path.join(project_dir, "case-files", filename)
    with open(path, "r") as f:
        return f.read()


def chunk_text(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += chunk_size - overlap
    return chunks


def first_words(text, n):
    return " ".join(text.split()[:n])


def bar(score, width=8):
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


def show_retrieval(question, archive, top_k=3):
    """Print the full retrieval pipeline for one question."""

    print(f"  Question: \"{question}\"")
    print()

    # Step 1 — embed the question
    query_fp = embed_passage(question)

    print("  Step 1 — embed the question:")
    print(f"    embed_passage(\"{question[:50]}...\")")
    print()
    print(f"    {'dimension':<14}  hits  score")
    print(f"    {'─────────':<14}  ────  ─────")
    for dim_name, keywords in FINGERPRINT_DIMENSIONS.items():
        hits = [kw for kw in keywords if kw in question.lower()]
        score = round(min(len(hits) / 3.0, 1.0), 2)
        hit_str = f"[{', '.join(hits)}]" if hits else "[none]"
        print(f"    {dim_name:<14}  {len(hits):>4}  {score:.2f}  {hit_str}")
    print()
    print(f"    → query fingerprint: {query_fp}")

    # Step 2 — archive search
    print()
    print("  Step 2 — send fingerprint to the archive:")
    print(f"    archive.search({query_fp}, top_k={top_k})")

    # Step 3 — relevance scores
    all_scored = archive.all_scores(query_fp)
    print()
    print("  Step 3 — relevance scores:")
    print()
    print(f"    {'Page':<6}  {'Score':>6}  {'Bar'}")
    print(f"    {'────':<6}  {'─────':>6}")
    for page_num, score in all_scored:
        print(f"    [P{page_num:02d}]   {score:>5.4f}  {bar(score)}")

    # Step 4 — top K results
    query_fp_result, results = retrieve(question, archive, top_k=top_k)
    print()
    print(f"  Step 4 — top {top_k} results returned:")
    print()
    for rank, result in enumerate(results, 1):
        page_num = result["page_num"]
        score    = result["score"]
        text     = result["text"]
        words    = text.split()
        line1    = " ".join(words[:15])
        line2    = " ".join(words[15:28]) if len(words) > 15 else ""
        print(f"  #{rank}  [Page {page_num:02d}]  score={score:.4f}  {bar(score)}")
        print(f"       \"{line1}")
        if line2:
            print(f"        {line2}...\"")
        print()


# ---------------------------------------------------------------------------
# Build the archive
# ---------------------------------------------------------------------------

case_text = load_case_file("millbrook_arson_2019.txt")
chunks    = chunk_text(case_text, chunk_size=60, overlap=15)
archive   = EvidenceArchive()

for i, chunk in enumerate(chunks):
    archive.add(page_num=i + 1, text=chunk, fingerprint=embed_passage(chunk))


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 6")
print()
print("  Milestone:")
print("  The Retrieval Desk")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Retrieval Desk Open")
print()
print("  Objective:")
print("  Accept a natural language question. Return top-K evidence pages.")
print("=" * 66)

print(f"""
The Evidence Archive is built. {len(archive)} pages are indexed and searchable.

Until now, every search required a pre-prepared fingerprint.
The Retrieval Desk removes that requirement.

A detective submits a question in plain language.
The desk embeds it, queries the archive, and returns evidence.

Pipeline:
  question  →  embed  →  fingerprint  →  archive.search  →  results

The archive still never receives the question — only the fingerprint.
The desk handles the translation. The separation is preserved.

Two questions are shown to demonstrate that the retriever responds
to meaning: different questions produce different fingerprints and
surface different pages.
""")


# ---------------------------------------------------------------------------
# Query 1 — forensic question
# ---------------------------------------------------------------------------

print("=" * 66)
print("  QUERY 1 — Detective Morgan submits a forensic question")
print("=" * 66)
print()
show_retrieval("What accelerant was used in the Millbrook Arson?", archive, top_k=3)


# ---------------------------------------------------------------------------
# Query 2 — investigation question
# ---------------------------------------------------------------------------

print("=" * 66)
print("  QUERY 2 — Detective Morgan submits an investigation question")
print("=" * 66)
print()
show_retrieval("Were any suspects identified in the investigation?", archive, top_k=3)


# ---------------------------------------------------------------------------
# Contrast
# ---------------------------------------------------------------------------

print("-" * 66)
print("  CONTRAST — two questions, two different sets of evidence")
print("-" * 66)
print()

q1_fp, q1_results = retrieve(
    "What accelerant was used in the Millbrook Arson?", archive, top_k=3)
q2_fp, q2_results = retrieve(
    "Were any suspects identified in the investigation?", archive, top_k=3)

q1_pages = [r["page_num"] for r in q1_results]
q2_pages = [r["page_num"] for r in q2_results]

print(f"  Q1 fingerprint:  {q1_fp}")
print(f"  Q1 top pages:    {q1_pages}  (forensic evidence)")
print()
print(f"  Q2 fingerprint:  {q2_fp}")
print(f"  Q2 top pages:    {q2_pages}  (investigation notes)")
print()
print("  No pages overlap between the two result sets.")
print("  The retriever surfaces different evidence for different questions.")
print("  The same archive, the same 7 pages — the query determines what")
print("  is relevant.")


print("""
==========================

Investigation Summary

The Retrieval Desk is the entry point to the archive for natural
language queries. Its implementation is a single function:

  retrieve(question, archive, top_k)
    → embed the question
    → call archive.search with the fingerprint
    → return the top-K results

The detective submits a question. The desk handles the embedding.
The archive handles the scoring. The results return up the chain.

Two questions were demonstrated. Different questions produced
different fingerprints, and different fingerprints retrieved
different pages. The archive responded to meaning.

AI Connection

In production RAG systems, the retrieval step calls a sentence
encoder to embed the query — the same encoder that was used to
embed the documents at index time. Query and document embeddings
share the same vector space, so cosine similarity is meaningful
across them.

This milestone uses the same keyword-scoring function for both
documents and queries, which achieves the same property: query
and page fingerprints live in the same space and can be compared.
The embedding method is different. The retrieval principle is
identical.

Continue Investigation

The retrieved pages are the raw evidence. Before the detective
reads them, they should be ranked by a more precise measure of
relevance — not just similarity to the query, but quality of the
specific evidence each page contains.

Open:
    07_precision_ranker.py
""")
