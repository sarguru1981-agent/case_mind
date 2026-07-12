# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 4
#
# The archive holds 7 fingerprinted pages from the Millbrook Arson case.
# Each page is a vector — five numbers representing what that page is about.
#
# A detective now arrives with a question:
#   "What accelerant was used in the Millbrook Arson?"
#
# That question can also be converted into a fingerprint vector using the
# same Fingerprint Engine. The question and every page now share the same
# five-dimensional space.
#
# The Relevance Scorer measures how closely the question fingerprint
# points in the same direction as each page fingerprint. Pages pointing
# in the same direction as the question score high. Pages pointing in a
# different direction score low.
#
# The measuring instrument is cosine similarity.
#
# ─────────────────────────────────────────────────────────────────────
# Educational note
#
# The fingerprint engine in this project is a simplified educational
# implementation. Real-world embedding models generate these vectors
# automatically using pre-trained neural networks trained on billions
# of sentences. The vectors they produce have hundreds of dimensions
# and capture nuance that keyword scoring cannot.
#
# The objective here is to understand how similarity is measured —
# not how production embeddings are generated. The cosine similarity
# formula used below is identical in production systems. Only the
# vectors it operates on are different.
# ─────────────────────────────────────────────────────────────────────
# =============================================================================

import os
import math


# ---------------------------------------------------------------------------
# The Fingerprint Engine (standalone — same logic as Milestone 3)
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
# The Relevance Scorer
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a, vec_b):
    """
    Measure the angle between two vectors.

    A score of 1.0 means both vectors point in exactly the same direction —
    the page is about exactly what the query is about.
    A score of 0.0 means the vectors are perpendicular — no shared meaning.

    Magnitude is factored out: a longer vector does not score higher simply
    because it contains more keywords. Only direction matters.
    """
    dot    = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a  = math.sqrt(sum(x * x for x in vec_a))
    mag_b  = math.sqrt(sum(x * x for x in vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Case file loading and chunking (standalone — same logic as Milestones 2–3)
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


# ---------------------------------------------------------------------------
# Load, chunk, and fingerprint the case file (Config C)
# ---------------------------------------------------------------------------

case_text    = load_case_file("millbrook_arson_2019.txt")
chunks       = chunk_text(case_text, chunk_size=60, overlap=15)
fingerprints = [embed_passage(chunk) for chunk in chunks]


# ---------------------------------------------------------------------------
# The detective's question — embedded as a query fingerprint
# ---------------------------------------------------------------------------

QUESTION = "What accelerant was used in the Millbrook Arson?"
query_fp = embed_passage(QUESTION)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 4")
print()
print("  Milestone:")
print("  The Relevance Scorer")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Query Processing")
print()
print("  Objective:")
print("  Score every page fingerprint against a query fingerprint.")
print("=" * 66)

print(f"""
The archive holds {len(chunks)} pages, each with a 5-dimensional fingerprint.

Detective Morgan submits a question:

  "{QUESTION}"

The Fingerprint Engine converts this question into the same
5-dimensional space as the case file pages. The Relevance Scorer
then measures how closely each page fingerprint points in the same
direction as the query fingerprint.

That measurement is cosine similarity.
""")


# ---------------------------------------------------------------------------
# The formula
# ---------------------------------------------------------------------------

print("-" * 66)
print("  THE FORMULA — cosine similarity")
print("-" * 66)
print("""
  cosine_similarity(A, B) = dot(A, B) / (|A| × |B|)

  dot(A, B)  —  sum of dimension-by-dimension products
                captures how much both vectors agree on each topic

  |A|, |B|   —  magnitudes (lengths) of each vector
                dividing by magnitudes removes the effect of scale:
                a longer vector does not score higher simply because
                it mentioned more keywords

  Result: a number between 0.0 and 1.0
    1.0  →  vectors point in the same direction  (highly relevant)
    0.0  →  vectors are perpendicular            (no shared meaning)
""")


# ---------------------------------------------------------------------------
# The query fingerprint
# ---------------------------------------------------------------------------

print("-" * 66)
print("  QUERY FINGERPRINT")
print("-" * 66)
print()
print(f"  Question: \"{QUESTION}\"")
print()
print("  Keyword hits:")

for dim_name, keywords in FINGERPRINT_DIMENSIONS.items():
    hits = [kw for kw in keywords if kw in QUESTION.lower()]
    score = round(min(len(hits) / 3.0, 1.0), 2)
    hit_str = f"  [{', '.join(hits)}]" if hits else "  [none]"
    print(f"    {dim_name:<14}  {len(hits)} hit(s){hit_str}  →  {score:.2f}")

query_mag = math.sqrt(sum(x * x for x in query_fp))
print()
print(f"  Query fingerprint:  {query_fp}")
print(f"  Query magnitude:    {query_mag:.4f}")
print()
print("  The query is focused on forensic and incident dimensions.")
print("  Pages that are also focused there will score highest.")


# ---------------------------------------------------------------------------
# Step-by-step walkthrough — Page 4 (highest ranked)
# ---------------------------------------------------------------------------

p4 = fingerprints[3]
dot_p4  = sum(a * b for a, b in zip(query_fp, p4))
mag_p4  = math.sqrt(sum(x * x for x in p4))
cos_p4  = cosine_similarity(query_fp, p4)

print()
print("-" * 66)
print("  STEP-BY-STEP WALKTHROUGH — Query vs Page 4")
print(f"  \"{first_words(chunks[3], 10)}...\"")
print("-" * 66)
print()
print("  Step 1 — dot product (dimension-by-dimension contributions):")
print()
print(f"    {'dimension':<14}  {'query':>6}  ×  {'page 4':>6}  =  {'product':>8}")
print(f"    {'─────────':<14}  {'──────':>6}     {'──────':>6}     {'───────':>8}")
for dim, q, p in zip(DIM_NAMES, query_fp, p4):
    print(f"    {dim:<14}  {q:>6.2f}     {p:>6.2f}     {q * p:>8.4f}")
print(f"    {'─────────':<14}  {'':>6}     {'':>6}     {'───────':>8}")
print(f"    {'dot product':<14}  {'':>6}     {'':>6}     {dot_p4:>8.4f}")

print()
print("  Step 2 — vector magnitudes:")
print()

q_sq_parts = " + ".join(f"{x:.2f}²" for x in query_fp)
p4_sq_parts = " + ".join(f"{x:.2f}²" for x in p4)

print(f"    |query| = √( {q_sq_parts} )")
print(f"            = √( {' + '.join(f'{x*x:.4f}' for x in query_fp)} )")
print(f"            = √{sum(x*x for x in query_fp):.4f}")
print(f"            = {query_mag:.4f}")
print()
print(f"    |page4| = √( {p4_sq_parts} )")
print(f"            = √( {' + '.join(f'{x*x:.4f}' for x in p4)} )")
print(f"            = √{sum(x*x for x in p4):.4f}")
print(f"            = {mag_p4:.4f}")

print()
print("  Step 3 — cosine similarity:")
print()
print(f"    dot / (|query| × |page4|)")
print(f"    = {dot_p4:.4f} / ({query_mag:.4f} × {mag_p4:.4f})")
print(f"    = {dot_p4:.4f} / {query_mag * mag_p4:.4f}")
print(f"    = {cos_p4:.4f}")
print()
print(f"  Page 4 relevance score: {cos_p4:.4f}")
print("  Interpretation: the query and Page 4 point in nearly the same")
print("  direction. Page 4 is about the forensic findings — which is")
print("  exactly what the accelerant question asks about.")


# ---------------------------------------------------------------------------
# Full comparison — all pages
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  ALL PAGES — RELEVANCE SCORES")
print("-" * 66)
print()
print(f"  Query fingerprint:  {query_fp}")
print()
print(f"  {'Page':<6}  {'Score':>6}  {'Bar':<10}  preview")
print(f"  {'────':<6}  {'─────':>6}  {'───':>10}")

scores = []
for i, (chunk, fp) in enumerate(zip(chunks, fingerprints)):
    sim = cosine_similarity(query_fp, fp)
    scores.append((i + 1, sim, chunk, fp))
    preview = first_words(chunk, 8)
    print(f"  [P{i+1:02d}]   {sim:>5.4f}  {bar(sim):<10}  \"{preview}...\"")


# ---------------------------------------------------------------------------
# Ranked results
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  RANKED RESULTS — most relevant to least relevant")
print("-" * 66)
print()

ranked = sorted(scores, key=lambda x: -x[1])

for rank, (page_num, sim, chunk, fp) in enumerate(ranked, 1):
    preview = first_words(chunk, 10)
    print(f"  #{rank}  [Page {page_num:02d}]  score={sim:.4f}  {bar(sim)}")
    print(f"       \"{preview}...\"")
    print()

top3 = [page_num for page_num, sim, chunk, fp in ranked[:3]]
print(f"  The top 3 pages are: {top3}")
print()
print("  All three are the pages where forensic evidence is recorded.")
print("  Page 4 (forensic findings) ranks first.")
print("  Page 3 (incident → forensic transition, carrying the overlap) ranks second.")
print("  Page 5 (secondary residue traces) ranks third.")
print()
print("  The conclusion page scores 0.0000 — it shares no dimensions")
print("  with the query. The retriever will not surface it.")


print("""
==========================

Investigation Summary

The Relevance Scorer converts the question of relevance into
arithmetic. Each page fingerprint is compared against the query
fingerprint using cosine similarity: the dot product of the two
vectors divided by the product of their magnitudes.

The result is a score between 0.0 and 1.0. Pages that share the
same semantic focus as the query score high. Pages that cover
different topics score low or zero.

Ranking all 7 pages by their scores produces an ordered list: the
archive's answer to the question "which pages are most likely to
hold what the detective needs?"

AI Connection

In production RAG systems, cosine similarity is computed between
a query embedding (produced by a sentence encoder) and every
stored document embedding. The formula is identical. The difference
is that production embeddings have hundreds of dimensions and encode
far more nuance — but the measurement is the same angle calculation
demonstrated here.

Magnitude normalisation is the key insight: a page that repeats the
word "fire" fifty times does not outrank a page that mentions it
once alongside "petroleum distillate" and "ignition point". Direction
matters. Scale does not.

Continue Investigation

The scores are ready. The ranked list exists.
The next step is to store these fingerprints permanently so that any
query can be compared against the entire archive in a single operation.

Open:
    05_evidence_archive.py
""")
