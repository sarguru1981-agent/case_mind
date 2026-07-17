# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 7
#
# Milestone 6 built the Retrieval Desk. It takes a question, finds
# the most similar pages by fingerprint, and returns the top-K.
#
# But fingerprint similarity is a coarse measure. It captures whether
# a page is broadly about the same topic as the question — it does
# not verify whether the specific words the detective used actually
# appear in the retrieved page.
#
# Two pages can have identical fingerprints and wildly different
# usefulness. Page A might score high because it is about forensics
# generally. Page B might score slightly lower — but it contains the
# exact word "accelerant" that the detective asked about.
#
# The Precision Ranker is a second pass over the retrieved candidates.
# It rescores each page using a different signal: direct term overlap.
# How many content words from the detective's question appear verbatim
# in the page text?
#
# The combined score blends retrieval similarity with direct term
# coverage. Pages that match on both signals rise. Pages that scored
# high on fingerprint similarity but contain none of the question's
# specific words fall.
#
# Two questions are demonstrated:
#
#   Q1 — accelerant question
#        Same retrieval order preserved. The reranker confirms it
#        and widens the gap between #1 and #2.
#
#   Q2 — suspects question
#        Retrieval order reversed for #1 and #2. The reranker promotes
#        a page that contains exact answer terms over one that does not.
#
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

    def __len__(self):
        return len(self._entries)


# ---------------------------------------------------------------------------
# The Retrieval Desk (standalone)
# ---------------------------------------------------------------------------

def retrieve(question, archive, top_k=3):
    query_fingerprint = embed_passage(question)
    results = archive.search(query_fingerprint, top_k=top_k)
    return query_fingerprint, results


# ---------------------------------------------------------------------------
# The Precision Ranker
# ---------------------------------------------------------------------------

def extract_content_words(question):
    """
    Words of 5+ characters from the question.

    Short words (the, was, any, were, used, ...) are too common to carry
    specific meaning. Words of five or more characters name the concepts
    the detective is actually asking about.
    """
    cleaned = question.lower()
    for ch in "?.,!":
        cleaned = cleaned.replace(ch, "")
    return [w for w in cleaned.split() if len(w) >= 5]


def rerank(question, candidates):
    """
    Rescore retrieved candidates using direct term overlap.

    For each candidate page:
      1. Extract content words from the question (5+ char words).
      2. Count how many appear verbatim in the page text (term score).
      3. Combine: 60% retrieval score + 40% term score.

    The 60/40 split preserves semantic relevance as the primary signal
    while giving meaningful weight to exact evidence coverage.

    Returns candidates sorted by combined score, descending.
    Each result gains three new fields:
      rerank_score  — the combined score
      exact_hits    — which content words were found in the page
      content_words — all content words extracted from the question
    """
    content_words = extract_content_words(question)
    rescored = []
    for c in candidates:
        text_lower   = c["text"].lower()
        exact_hits   = [w for w in content_words if w in text_lower]
        term_score   = len(exact_hits) / len(content_words) if content_words else 0.0
        rerank_score = round(0.6 * c["score"] + 0.4 * term_score, 4)
        rescored.append({
            **c,
            "rerank_score":   rerank_score,
            "term_score":     round(term_score, 4),
            "exact_hits":     exact_hits,
            "content_words":  content_words,
        })
    rescored.sort(key=lambda e: -e["rerank_score"])
    return rescored


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


def show_reranking(question, archive, top_k=3):
    """Print the full retrieval → reranking pipeline for one question."""

    print(f"  Question: \"{question}\"")
    print()

    # Retrieval
    query_fp, candidates = retrieve(question, archive, top_k=top_k)
    retrieval_order = [c["page_num"] for c in candidates]
    content_words   = extract_content_words(question)

    print(f"  Content words extracted (5+ chars):")
    print(f"    {content_words}")
    print()

    # Retrieval order table
    print(f"  {'─'*64}")
    print(f"  RETRIEVAL — cosine similarity scores")
    print(f"  {'─'*64}")
    print()
    print(f"  {'Rank':<5}  {'Page':<6}  {'Score':>6}  {'Bar':<10}  preview")
    print(f"  {'────':<5}  {'────':<6}  {'─────':>6}  {'──────────'}")
    for rank, c in enumerate(candidates, 1):
        preview = first_words(c["text"], 8)
        print(f"  #{rank:<4}  [P{c['page_num']:02d}]   {c['score']:>5.4f}  "
              f"{bar(c['score']):<10}  \"{preview}...\"")
    print()

    # Reranking
    reranked = rerank(question, candidates)
    reranked_order = [c["page_num"] for c in reranked]

    print(f"  {'─'*64}")
    print(f"  RERANKING — 0.6 × retrieval + 0.4 × term overlap")
    print(f"  {'─'*64}")
    print()
    print(f"  {'Page':<6}  {'Retrieval':>9}  {'Term':>5}  {'Combined':>8}  "
          f"{'Bar':<10}  exact hits")
    print(f"  {'────':<6}  {'─────────':>9}  {'────':>5}  {'────────':>8}  "
          f"{'──────────'}")

    for c in reranked:
        hits_str = str(c["exact_hits"]) if c["exact_hits"] else "[none]"
        print(f"  [P{c['page_num']:02d}]    {c['score']:>9.4f}  "
              f"{c['term_score']:>5.4f}  {c['rerank_score']:>8.4f}  "
              f"{bar(c['rerank_score']):<10}  {hits_str}")

    # Did the order change?
    print()
    if retrieval_order == reranked_order:
        print(f"  Order: {retrieval_order}  →  {reranked_order}  (unchanged)")
    else:
        print(f"  Order: {retrieval_order}  →  {reranked_order}  ← REORDERED")

    # Top result after reranking
    top = reranked[0]
    print()
    print(f"  {'─'*64}")
    print(f"  TOP RESULT AFTER RERANKING — Page {top['page_num']:02d}")
    print(f"  {'─'*64}")
    print()
    words = top["text"].split()
    line1 = " ".join(words[:15])
    line2 = " ".join(words[15:30]) if len(words) > 15 else ""
    print(f"  \"{line1}")
    if line2:
        print(f"   {line2}...\"")
    print()
    return retrieval_order, reranked_order, reranked


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
print("  MILESTONE 7")
print()
print("  Milestone:")
print("  The Precision Ranker")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Second Pass Evaluation")
print()
print("  Objective:")
print("  Rescore retrieved candidates for evidence precision.")
print("=" * 66)

print(f"""
The Retrieval Desk returns the pages most similar to the question
by fingerprint. That is a semantic signal — it finds pages about
the same broad topic.

But fingerprint similarity does not check whether the specific
words the detective used actually appear in the page. A page may
score highly because it is broadly about forensics, while a page
that scores lower contains the exact term "accelerant" the
detective asked about.

The Precision Ranker is a second pass. It rescores each retrieved
candidate by counting how many content words from the question
appear verbatim in the page text.

Scoring formula:
  combined = 0.6 × retrieval_score + 0.4 × term_score

  retrieval_score — cosine similarity (from Milestone 4)
  term_score      — fraction of question content words found in page
  content words   — question words of 5+ characters

The 60/40 split keeps semantic relevance as the primary signal
while giving meaningful weight to direct evidence coverage.

Two questions are shown. One confirms the retrieval order. One
reverses it — and the reason is traceable.
""")


# ---------------------------------------------------------------------------
# Q1 — accelerant question
# ---------------------------------------------------------------------------

print("=" * 66)
print("  QUERY 1 — forensic question")
print("=" * 66)
print()
q1_retrieval, q1_reranked, q1_results = show_reranking(
    "What accelerant was used in the Millbrook Arson?", archive, top_k=3)

print("  Why the order held:")
print("  Page 4 is the only page that contains \"accelerant\" literally.")
print("  Its term score (0.33) adds to an already high retrieval score.")
print("  Page 3 has no exact hits — its combined score falls further")
print("  behind Page 4 than the retrieval scores suggested.")
print()

q1_gap_before = abs(q1_results[0]["score"] - q1_results[1]["score"])
q1_gap_after  = abs(q1_results[0]["rerank_score"] - q1_results[1]["rerank_score"])
print(f"  Gap between #1 and #2:")
print(f"    After retrieval:  {q1_gap_before:.4f}")
print(f"    After reranking:  {q1_gap_after:.4f}  ({q1_gap_after/q1_gap_before:.1f}× wider)")


# ---------------------------------------------------------------------------
# Q2 — suspects question
# ---------------------------------------------------------------------------

print()
print("=" * 66)
print("  QUERY 2 — investigation question")
print("=" * 66)
print()
q2_retrieval, q2_reranked, q2_results = show_reranking(
    "Were any suspects identified in the investigation?", archive, top_k=3)

# Find the page that moved up
promoted = q2_results[0]
demoted  = q2_results[1]

print(f"  Why the order changed:")
print(f"  Page {demoted['page_num']} ranked first in retrieval. Its fingerprint scores high")
print(f"  on the investigation dimension — it mentions CCTV, registered")
print(f"  vehicles, and the county database. That triggered a high")
print(f"  fingerprint match. But it contains none of the question's")
print(f"  specific terms: not \"suspects\", not \"identified\", not")
print(f"  \"investigation\".")
print()
print(f"  Page {promoted['page_num']} ranked second in retrieval — but it contains two")
print(f"  exact hits: \"identified\" and \"investigation\". Those words are")
print(f"  in the detective's question. The reranker promotes this page")
print(f"  because it is more precisely about what was asked.")
print()
print(f"  Page {demoted['page_num']} term score:  0.0000  (no exact hits)")
print(f"  Page {promoted['page_num']} term score:  {promoted['term_score']:.4f}  "
      f"(hits: {promoted['exact_hits']})")


# ---------------------------------------------------------------------------
# Summary comparison
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  SUMMARY — retrieval vs reranking")
print("-" * 66)
print()
print(f"  {'Query':<10}  retrieval order  →  reranked order  change?")
print(f"  {'─────':<10}  ───────────────     ──────────────  ───────")
print(f"  Q1 (accel)   {q1_retrieval}  →  {q1_reranked}  confirmed")
print(f"  Q2 (suspect) {q2_retrieval}  →  {q2_reranked}  reordered")
print()
print("  Retrieval surfaces pages about the right topic.")
print("  Reranking surfaces the page with the right evidence.")


print("""
==========================

Investigation Summary

The Precision Ranker adds a second scoring pass after retrieval.
It counts how many content words from the question appear verbatim
in each candidate page, then blends that term score with the
original retrieval score at 60/40.

When the two signals agree (Q1), the reranker confirms the order
but widens the gap — making the ranking more decisive. When the
signals disagree (Q2), the reranker promotes the page that
directly addresses the question over the page that is broadly
related to the same topic.

The two signals are complementary. Retrieval finds the right
neighbourhood. Reranking finds the right address.

AI Connection

In production RAG systems, reranking is performed by a cross-encoder
model — a neural network that reads the question and a document
together (not separately) and produces a single relevance score.
Cross-encoders are slower than bi-encoders but more precise,
because they can model the interaction between question and document.

This milestone demonstrates the same idea at educational scale:
a second pass that compares question and page together, using
term overlap as a proxy for the cross-encoder's learned relevance.
The mechanism is simpler. The principle is the same.

Continue Investigation

The retrieved and reranked evidence is ready.
The next step is to place that evidence in front of the detective
before the question reaches the intelligence system — so the
system can answer from what it can see, not from memory.

Open:
    08_detective_brief.py
""")
