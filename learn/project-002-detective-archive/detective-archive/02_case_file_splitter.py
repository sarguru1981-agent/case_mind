# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 2
#
# Detective Morgan has confirmed that the Millbrook Arson case file contains
# the answer. Now the archive must be built so that every cold case can
# be searched, not just this one.
#
# The first task is intake. Every case file entering the archive must be
# broken into individually numbered pages. A complete 40-page report
# embedded as a single unit produces one vector that encodes everything —
# the incident report, the forensic analysis, the suspect interviews, the
# court outcome — collapsed into one number sequence. A query about
# accelerants retrieves the whole file, not the section that answers.
#
# Precision requires division.
#
# The Case File Splitter takes a raw document and produces a sequence
# of numbered, overlapping pages. Two parameters control the output:
#
#   chunk_size — words per page
#   overlap    — words carried from the end of one page into the start
#                of the next, so a sentence at a boundary is not
#                stranded in only one of the pages it belongs to
#
# This milestone demonstrates what happens when those parameters are
# set too aggressively in either direction — and what balance looks like.
# =============================================================================

import os


# ---------------------------------------------------------------------------
# The Case File Splitter
# ---------------------------------------------------------------------------

def chunk_text(text, chunk_size, overlap):
    """
    Split text into overlapping chunks of chunk_size words.

    Returns a list of strings. Each string is one page of the archive.
    Adjacent pages share their last/first `overlap` words so that
    sentences at page boundaries are not split without context.
    """
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


def load_case_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    path = os.path.join(project_dir, "case-files", filename)
    with open(path, "r") as f:
        return f.read()


def first_words(text, n):
    return " ".join(text.split()[:n])


def last_words(text, n):
    return " ".join(text.split()[-n:])


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

case_text   = load_case_file("millbrook_arson_2019.txt")
total_words = len(case_text.split())


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 2")
print()
print("  Milestone:")
print("  The Case File Splitter")
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
print("  Split a cold case file into individually retrievable pages.")
print("=" * 66)

print(f"""
The Detective Archive cannot fingerprint a whole case file as one unit.
A complete report embedded as a single vector is too coarse to retrieve
precisely — every query returns the entire file regardless of relevance.

The archive's filing system must first break each case file into numbered
pages: small enough to be specific, large enough to hold a coherent thought.

Loaded: case-files/millbrook_arson_2019.txt
Total words: {total_words}

Two parameters control the split.
  chunk_size — words per page
  overlap    — words shared between the end of one page and the start
               of the next (boundary sentences appear in both)

Three configurations are shown below.
""")


# ---------------------------------------------------------------------------
# Configuration A — chunk too small
# ---------------------------------------------------------------------------

SIZE_A    = 15
OVERLAP_A = 0
chunks_a  = chunk_text(case_text, SIZE_A, OVERLAP_A)

print("-" * 66)
print(f"  CONFIGURATION A   chunk_size={SIZE_A}, overlap={OVERLAP_A}")
print(f"  Every page holds {SIZE_A} words. No overlap.")
print("-" * 66)
print()
print(f"  Total pages produced: {len(chunks_a)}")
print()

for i, chunk in enumerate(chunks_a[:5]):
    print(f"  [Page {i+1:02d}]  \"{chunk}\"")
print()
print(f"  ... {len(chunks_a) - 5} more pages not shown.")
print()
print("  Problem:")
print("  Each page holds 2–3 short phrases, not a complete thought.")
print("  Sentences are cut at word 15 regardless of meaning.")
print("  A query about accelerants returns a fragment like:")
print("    \"Petroleum distillate was confirmed as the primary\"")
print("  — with the rest of that sentence on the following page.")
print()
print(f"  Verdict: {len(chunks_a)} pages from one short file is too granular.")
print("           Every page lacks the context to answer any question.")


# ---------------------------------------------------------------------------
# Configuration B — chunk too large
# ---------------------------------------------------------------------------

SIZE_B    = 200
OVERLAP_B = 0
chunks_b  = chunk_text(case_text, SIZE_B, OVERLAP_B)

print()
print("-" * 66)
print(f"  CONFIGURATION B   chunk_size={SIZE_B}, overlap={OVERLAP_B}")
print(f"  Every page holds up to {SIZE_B} words. No overlap.")
print("-" * 66)
print()
print(f"  Total pages produced: {len(chunks_b)}")
print()

for i, chunk in enumerate(chunks_b):
    wc = len(chunk.split())
    print(f"  [Page {i+1:02d}]  ({wc} words)")
    print(f"  \"{first_words(chunk, 20)}...\"")
    print()

print("  Problem:")
print("  The header, incident report, forensic findings, and half the")
print("  investigation notes are all packed into Page 1.")
print(f"  Page 1 holds {len(chunks_b[0].split())} words.")
print("  A query about accelerants retrieves the entire page —")
print("  approximately 80% of it has nothing to do with the accelerant.")
print()
print(f"  Verdict: {len(chunks_b)} pages is not a filing system. It is two piles.")
print("           No query can retrieve precisely what it is looking for.")


# ---------------------------------------------------------------------------
# Configuration C — recommended
# ---------------------------------------------------------------------------

SIZE_C    = 60
OVERLAP_C = 15
chunks_c  = chunk_text(case_text, SIZE_C, OVERLAP_C)

print()
print("-" * 66)
print(f"  CONFIGURATION C   chunk_size={SIZE_C}, overlap={OVERLAP_C}  ← RECOMMENDED")
print(f"  Every page holds ~{SIZE_C} words. {OVERLAP_C}-word overlap at each boundary.")
print("-" * 66)
print()
print(f"  Total pages produced: {len(chunks_c)}")
print()

for i, chunk in enumerate(chunks_c):
    wc = len(chunk.split())
    print(f"  [Page {i+1:02d}]  ({wc} words)  \"{first_words(chunk, 12)}...\"")
print()


# --- Overlap demonstration: pages 3 → 4 ---

print("-" * 66)
print(f"  OVERLAP DEMONSTRATION   Page 3 → Page 4")
print("-" * 66)
print()
print("  Without overlap, a sentence that crosses a page boundary")
print("  is incomplete in both pages. It ends on one page and begins")
print("  on the next — readable in neither.")
print()

tail = last_words(chunks_c[2], OVERLAP_C)
head = first_words(chunks_c[3], OVERLAP_C)

print(f"  Last {OVERLAP_C} words of Page 3:")
print(f"    \"{tail}\"")
print()
print(f"  First {OVERLAP_C} words of Page 4:")
print(f"    \"{head}\"")
print()
print("  These are the same words.")
print("  The sentence that introduces the forensic finding appears in")
print("  both pages. Neither page is missing the context it needs.")


# --- Key evidence demonstration ---

print()
print("-" * 66)
print("  KEY EVIDENCE — where does 'petroleum distillate' land?")
print("-" * 66)
print()

evidence_pages = []
for i, chunk in enumerate(chunks_c):
    if "petroleum" in chunk.lower():
        evidence_pages.append(i + 1)

print(f"  'petroleum distillate' appears on pages: {evidence_pages}")
print()
print("  It appears on multiple pages because overlap carries the")
print("  forensic finding across the page-3/page-4 boundary.")
print()
print(f"  A query about accelerants will retrieve pages {evidence_pages[0]}–{evidence_pages[-1]}.")
print("  The answer is present in each. No retrieval misses it.")


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  COMPARISON")
print("-" * 66)
print()
print(f"  Config A  size={SIZE_A:>3}, overlap={OVERLAP_A:>2}  →  {len(chunks_a):>2} pages  — too granular")
print(f"  Config B  size={SIZE_B:>3}, overlap={OVERLAP_B:>2}  →  {len(chunks_b):>2} pages  — too coarse")
print(f"  Config C  size={SIZE_C:>3}, overlap={OVERLAP_C:>2}  →  {len(chunks_c):>2} pages  — recommended")

print("""
==========================

Investigation Summary

The Case File Splitter takes a raw document and produces a numbered
sequence of overlapping pages. Chunk size and overlap are design
decisions with visible consequences.

Too small: sentences are broken, each page is a fragment without
enough context to answer any question on its own. Too large: entire
sections collapse into one page, making every retrieval imprecise.

Configuration C produces pages that are specific enough to hold a
focused topic and large enough to hold a coherent passage. Overlap
ensures that a sentence sitting at a boundary between two pages
is not stranded — it appears in both pages, fully intact.

The archive now has 7 individually addressable pages from one case
file. Every page is ready for the next step.

AI Connection

In production RAG systems, chunking parameters are tuned to the
document type and expected query style. Typical values range from
256 to 512 tokens per chunk (approximately 200–400 words) with
10–20 percent overlap. This milestone uses word counts rather than
token counts so that every number is directly readable. A tokeniser
from any production library produces equivalent output from the same
text.

Chunk size and overlap are among the most consequential engineering
decisions in a RAG pipeline. They determine whether retrieval is
precise, whether boundary sentences are lost, and how much context
each retrieved page carries. They cannot be changed after the archive
is built without re-indexing from scratch.

Continue Investigation

The pages are ready. Each one now needs a mathematical fingerprint —
a fixed-length vector that represents what the page is about, so that
a detective's question can be matched against it by meaning rather
than by keyword.

Open:
    03_fingerprint_engine.py
""")
