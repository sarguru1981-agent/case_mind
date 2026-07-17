# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 3
#
# The archive now holds 7 individually numbered pages from the Millbrook
# Arson case file. But a page of text cannot be searched by meaning —
# it can only be scanned by keyword. To search by meaning, each page
# needs a fingerprint.
#
# A fingerprint is a fixed-length vector of numbers. It encodes what
# a page is about, not what words it contains. Two pages about the same
# topic produce fingerprints that are close together. Two pages about
# different topics produce fingerprints that are far apart.
#
# This milestone builds the Fingerprint Engine: a function that converts
# any case file page into a 5-dimensional vector, one dimension per
# semantic category present in the archive.
#
# ─────────────────────────────────────────────────────────────────────
# Bridge from Project 001
#
# Project 001 introduced embeddings at the token level. Each word in
# the vocabulary received a vector. The question was: what does this
# word mean in relation to other words?
#
# This milestone embeds at the passage level. The question is no longer
# "what does this word mean?" — it is "what is this page about?"
#
# A passage embedding is a single vector that represents an entire
# chunk of text. The same architecture — text → numbers — operates at
# a higher level of abstraction.
# ─────────────────────────────────────────────────────────────────────
# =============================================================================

import os
import math


# ---------------------------------------------------------------------------
# The Fingerprint Engine
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
    """
    Convert a passage of text into a 5-dimensional fingerprint vector.

    Each dimension scores the presence of semantic keywords in that category.
    Score of 1.0 means three or more category keywords were found.
    Score of 0.0 means none were found.
    """
    text_lower = text.lower()
    vector = []
    for keywords in FINGERPRINT_DIMENSIONS.values():
        hits = sum(1 for kw in keywords if kw in text_lower)
        score = round(min(hits / 3.0, 1.0), 2)
        vector.append(score)
    return vector


def bar(score, width=8):
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Case file loading and chunking (standalone — same logic as Milestone 2)
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


# ---------------------------------------------------------------------------
# Load and split the case file (Config C from Milestone 2)
# ---------------------------------------------------------------------------

case_text = load_case_file("millbrook_arson_2019.txt")
chunks = chunk_text(case_text, chunk_size=60, overlap=15)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 3")
print()
print("  Milestone:")
print("  The Fingerprint Engine")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Intake Processing")
print()
print("  Objective:")
print("  Convert each case file page into a searchable fingerprint.")
print("=" * 66)

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BRIDGE FROM PROJECT 001
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Project 001 introduced embeddings at the token level.
  Each word in the vocabulary received a vector.
  The question was: what does this word mean in relation to others?

  This milestone embeds at the passage level.
  The question is no longer "what does this word mean?" —
  it is "what is this page about?"

  A passage embedding is one vector per chunk, not one vector
  per word. The same principle — text → numbers — operates at
  a higher level of abstraction. A detective's question and a
  case file page can be compared because they live in the same
  numerical space.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print(f"""\
The archive holds {len(chunks)} pages from the Millbrook Arson case file
(chunk_size=60, overlap=15 — Configuration C from Milestone 2).

Each page must now receive a fingerprint: a fixed-length vector of
numbers that encodes what the page is about.

The Fingerprint Engine scores each page across five semantic
dimensions. Each dimension measures how strongly a category of
meaning is present in the text.

  Dimensions: {", ".join(DIM_NAMES)}

  Scoring rule: count keyword hits per dimension.
    0 hits  →  0.00     (category absent)
    1 hit   →  0.33     (category faint)
    2 hits  →  0.67     (category present)
    3+ hits →  1.00     (category dominant)
""")


# ---------------------------------------------------------------------------
# All 7 fingerprints
# ---------------------------------------------------------------------------

print("-" * 66)
print("  ALL PAGES — FINGERPRINTS")
print("-" * 66)
print()
print(f"  {'Page':<6}  {'incident':>8}  {'forensic':>8}  {'timeline':>8}  "
      f"{'investig':>8}  {'conclusn':>8}  preview")
print(f"  {'────':<6}  {'────────':>8}  {'────────':>8}  {'────────':>8}  "
      f"{'────────':>8}  {'────────':>8}")

fingerprints = []
for i, chunk in enumerate(chunks):
    fp = embed_passage(chunk)
    fingerprints.append(fp)
    preview = first_words(chunk, 8)
    print(f"  [P{i+1:02d}]   "
          f"  {fp[0]:>6.2f}    {fp[1]:>6.2f}    {fp[2]:>6.2f}    "
          f"{fp[3]:>6.2f}    {fp[4]:>6.2f}    \"{preview}...\"")

print()


# ---------------------------------------------------------------------------
# Visualisation: all 7 fingerprints as bar charts
# ---------------------------------------------------------------------------

print("-" * 66)
print("  FINGERPRINT VISUALISATION — all pages")
print("-" * 66)
print()

for i, (chunk, fp) in enumerate(zip(chunks, fingerprints)):
    print(f"  [Page {i+1:02d}]  \"{first_words(chunk, 10)}...\"")
    for dim, score in zip(DIM_NAMES, fp):
        print(f"    {dim:<14}  {bar(score)}  {score:.2f}")
    print()


# ---------------------------------------------------------------------------
# Comparison A — clearly different pages
# ---------------------------------------------------------------------------

print("-" * 66)
print("  COMPARISON A — Pages 1, 4, 7")
print("  Different content → Different fingerprints")
print("-" * 66)
print()

comparison_a = [0, 3, 6]
labels_a = ["Page 1 (header / metadata)",
            "Page 4 (forensic findings)",
            "Page 7 (conclusion)"]

for idx, label in zip(comparison_a, labels_a):
    fp = fingerprints[idx]
    print(f"  {label}")
    print(f"  \"{first_words(chunks[idx], 10)}...\"")
    for dim, score in zip(DIM_NAMES, fp):
        print(f"    {dim:<14}  {bar(score)}  {score:.2f}")
    print()

print("  Observation:")
print("  Each page has a distinct fingerprint profile.")
print("  Page 1 is dominated by timeline (case header dates).")
print("  Page 4 is dominated by incident and forensic (arson scene).")
print("  Page 7 is dominated by timeline and conclusion (case closure).")
print("  A query about accelerants will not match Page 1 or Page 7.")
print()


# ---------------------------------------------------------------------------
# Comparison B — similar neighbouring pages
# ---------------------------------------------------------------------------

print("-" * 66)
print("  COMPARISON B — Pages 3 and 4")
print("  Similar content → Similar fingerprints")
print("-" * 66)
print()

comparison_b = [2, 3]
labels_b = ["Page 3 (incident → forensic transition)",
            "Page 4 (forensic findings)"]

for idx, label in zip(comparison_b, labels_b):
    fp = fingerprints[idx]
    print(f"  {label}")
    print(f"  \"{first_words(chunks[idx], 10)}...\"")
    for dim, score in zip(DIM_NAMES, fp):
        print(f"    {dim:<14}  {bar(score)}  {score:.2f}")
    print()

p3 = fingerprints[2]
p4 = fingerprints[3]
shared = sum(1 for a, b in zip(p3, p4) if a == b)

print("  Observation:")
print(f"  Pages 3 and 4 share matching scores on "
      f"{shared} of {len(DIM_NAMES)} dimensions.")
print("  Both have incident=1.00 and forensic=1.00.")
print("  This is because Page 3 carries the overlap — the last 15 words")
print("  of Page 3 are the same as the first 15 words of Page 4.")
print("  The Fingerprint Engine captures this proximity.")
print("  A query about accelerants will match both pages.")
print()


# ---------------------------------------------------------------------------
# Key evidence — where does the accelerant fingerprint appear?
# ---------------------------------------------------------------------------

print("-" * 66)
print("  KEY EVIDENCE — forensic signal across all pages")
print("-" * 66)
print()

forensic_pages = [(i + 1, fp[1]) for i, fp in enumerate(fingerprints) if fp[1] > 0]
print("  Pages with a non-zero forensic dimension:")
print()
for page_num, score in forensic_pages:
    print(f"    Page {page_num:02d}  forensic={score:.2f}  {bar(score)}")
print()
print("  The forensic signal is highest on pages 3, 4, and 5.")
print("  These are the pages the retriever will surface when a detective")
print("  asks: \"What accelerant was used in the Millbrook Arson?\"")
print()


print("""
==========================

Investigation Summary

The Fingerprint Engine converts each case file page into a
5-dimensional vector. Each dimension captures the presence of
a semantic category: incident, forensic, timeline, investigation,
or conclusion.

Pages about different topics produce clearly different fingerprints.
Pages about the same topic produce similar ones — including pages
that share content because of the overlap from Milestone 2.

The archive now holds 7 fingerprinted pages. Each page has a
text form (what the archivist can read) and a numerical form
(what the retrieval system can compare).

AI Connection

In production RAG systems, passage embeddings are produced by a
sentence encoder — a transformer model trained to map any text
into a dense vector of 384, 768, or more dimensions. The principle
is identical: text in, numbers out, similar meaning → similar vector.

This milestone uses 5 dimensions and keyword scoring so that every
number is readable and every score is traceable. A production encoder
captures far more nuance, but it is doing exactly this — at scale.

Continue Investigation

The archive is ready. 7 pages, 7 fingerprints.
The next step is to measure how close any query fingerprint is to
each page fingerprint — and rank the results.

Open:
    04_relevance_scorer.py
""")
