# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 5
#
# Milestones 2, 3, and 4 built three separate components:
#
#   Milestone 2 — The Case File Splitter
#     Takes a raw document and produces numbered, overlapping pages.
#
#   Milestone 3 — The Fingerprint Engine
#     Converts each page into a 5-dimensional vector.
#
#   Milestone 4 — The Relevance Scorer
#     Computes cosine similarity between a query fingerprint and a
#     page fingerprint.
#
# These three components are now assembled into a single object:
# the Evidence Archive.
#
# The archive has two responsibilities:
#   1. Intake  — accept a page (text + fingerprint) and store it
#   2. Search  — accept a query fingerprint and return the top-K
#                most relevant pages, ranked by cosine similarity
#
# The archive does not accept natural language questions. The caller
# is responsible for converting a question into a fingerprint before
# submitting a search. That step — the retrieval pipeline — is
# Milestone 6. This milestone builds the storage layer beneath it.
#
# An archive that can store and rank is a vector store.
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
# The Evidence Archive
# ---------------------------------------------------------------------------

class EvidenceArchive:
    """
    An in-memory archive of case file pages.

    Each entry stores the original page text and its fingerprint vector.
    The archive can be searched by fingerprint: submit a query vector and
    receive the top-K most relevant pages, ranked by cosine similarity.

    The archive does not embed queries. The caller provides a fingerprint.
    Converting a natural language question into a fingerprint is the
    retrieval pipeline's responsibility (Milestone 6).
    """

    def __init__(self):
        self._entries = []

    def add(self, page_num, text, fingerprint):
        """Store one page with its pre-computed fingerprint."""
        self._entries.append({
            "page_num":    page_num,
            "text":        text,
            "fingerprint": fingerprint,
        })

    def search(self, query_fingerprint, top_k=3):
        """
        Score every stored page against the query fingerprint.
        Return the top_k entries, sorted by descending relevance score.
        Each result is a dict: {"page_num", "text", "fingerprint", "score"}.
        """
        scored = []
        for entry in self._entries:
            score = cosine_similarity(query_fingerprint, entry["fingerprint"])
            scored.append({**entry, "score": score})
        scored.sort(key=lambda e: -e["score"])
        return scored[:top_k]

    def __len__(self):
        return len(self._entries)


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


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 5")
print()
print("  Milestone:")
print("  The Evidence Archive")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Storage and Retrieval")
print()
print("  Objective:")
print("  Store fingerprinted pages and search them by query fingerprint.")
print("=" * 66)

print("""
Milestones 2, 3, and 4 produced three standalone operations:
  split a document → fingerprint each page → score against a query.

The Evidence Archive assembles these into a single object. Its
interface is simple:

  archive.add(page_num, text, fingerprint)  — intake a page
  archive.search(query_fingerprint, top_k)  — retrieve top K pages

The archive stores. The archive ranks. It does not embed queries.
A query fingerprint must be prepared before search is called.
That step is the retrieval pipeline — Milestone 6.
""")


# ---------------------------------------------------------------------------
# Build the archive
# ---------------------------------------------------------------------------

print("-" * 66)
print("  INDEXING — loading and filing the Millbrook Arson case")
print("-" * 66)
print()

case_text = load_case_file("millbrook_arson_2019.txt")
chunks    = chunk_text(case_text, chunk_size=60, overlap=15)
archive   = EvidenceArchive()

for i, chunk in enumerate(chunks):
    fp = embed_passage(chunk)
    archive.add(page_num=i + 1, text=chunk, fingerprint=fp)
    wc = len(chunk.split())
    print(f"  [+] Page {i+1:02d}  ({wc:>2} words)  fingerprint={fp}")

print()
print(f"  Archive ready.  {len(archive)} pages indexed.")


# ---------------------------------------------------------------------------
# Prepare the query fingerprint
# ---------------------------------------------------------------------------

QUESTION = "What accelerant was used in the Millbrook Arson?"
query_fp = embed_passage(QUESTION)

print()
print("-" * 66)
print("  QUERY FINGERPRINT SUBMITTED")
print("-" * 66)
print()
print(f"  Question (for context):  \"{QUESTION}\"")
print()
print("  The archive does not receive the question.")
print("  The question is embedded outside the archive by the caller.")
print("  What the archive receives is only the fingerprint:")
print()
print(f"  query_fingerprint = {query_fp}")
print()
print("  archive.search(query_fingerprint, top_k=3)")


# ---------------------------------------------------------------------------
# Show scoring in progress
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  SCORING — cosine similarity against all indexed pages")
print("-" * 66)
print()
print(f"  {'Page':<6}  {'Score':>6}  {'Bar':<10}  fingerprint")
print(f"  {'────':<6}  {'─────':>6}  {'──────────':<10}")

all_scored = []
for entry in archive._entries:
    score = cosine_similarity(query_fp, entry["fingerprint"])
    all_scored.append((entry["page_num"], score, entry["text"], entry["fingerprint"]))
    print(f"  [P{entry['page_num']:02d}]   {score:>5.4f}  {bar(score):<10}  {entry['fingerprint']}")

print()
print(f"  All {len(archive)} pages scored. Sorting by descending score...")


# ---------------------------------------------------------------------------
# Top-K results
# ---------------------------------------------------------------------------

TOP_K   = 3
results = archive.search(query_fp, top_k=TOP_K)

print()
print("-" * 66)
print(f"  TOP {TOP_K} RESULTS")
print("-" * 66)
print()

for rank, result in enumerate(results, 1):
    page_num = result["page_num"]
    score    = result["score"]
    text     = result["text"]
    fp       = result["fingerprint"]

    print(f"  #{rank}  [Page {page_num:02d}]  score={score:.4f}  {bar(score)}")
    print(f"       fingerprint: {fp}")
    print(f"       text excerpt:")

    words = text.split()
    line1 = " ".join(words[:15])
    line2 = " ".join(words[15:30]) if len(words) > 15 else ""
    print(f"         \"{line1}")
    if line2:
        print(f"          {line2}...\"")
    else:
        print("         \"")
    print()

print("  The archive returned exactly the three pages that hold the")
print("  forensic evidence. Page 4 leads: it is the core forensic")
print("  findings section. Pages 3 and 5 follow: they carry the overlap")
print("  and the secondary residue evidence respectively.")
print()
print("  Pages about the incident timeline, investigation notes, and")
print("  case closure were not returned. Their fingerprints do not")
print("  point toward forensic content.")


print("""
==========================

Investigation Summary

The Evidence Archive is a vector store: a collection of (text,
fingerprint) pairs with a search method. Adding a page takes
constant time. Searching scores every stored page, sorts the
results, and returns the top K.

The interface is intentionally minimal:
  add(page_num, text, fingerprint)
  search(query_fingerprint, top_k)

The archive knows nothing about questions. It knows only
fingerprints and scores. The caller prepares the query fingerprint
before calling search. This separation is a design principle: the
storage layer is independent of the query layer.

AI Connection

Production vector stores (FAISS, Pinecone, Chroma) implement the
same interface at scale: index(id, vector) and query(vector, k).
They use approximate nearest-neighbour algorithms to search millions
of vectors in milliseconds — but the contract is identical to what
this archive implements.

The difference is performance. The principle is the same.

Continue Investigation

The archive is built and searchable by fingerprint.
The next step is to remove the manual embedding step from the caller.
A detective should be able to submit a natural language question
and receive the top pages — without preparing a fingerprint by hand.

Open:
    06_retrieval_desk.py
""")
