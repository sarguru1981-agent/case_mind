# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 8
#
# Milestones 1 through 7 built the full retrieval stack:
#   split → fingerprint → store → retrieve → rerank
#
# The retrieved pages are the evidence. Before the intelligence system
# sees the detective's question, that evidence must be placed in front
# of it — formatted, labelled, and accompanied by an instruction that
# tells the system to answer from what it can see, not from memory.
#
# That instruction is the grounding instruction.
# The assembled document — instruction + evidence + question — is
# the detective's brief.
#
# This milestone demonstrates why each component of the brief matters
# by constructing three versions and comparing their outcomes.
#
#   Version 1 — question only, no evidence
#               The intelligence system draws a blank. The case falls
#               outside its training data. The answer exists in the
#               archive but the system cannot see it.
#
#   Version 2 — evidence + question, no grounding instruction
#               The system has access to the evidence and produces an
#               answer. But without a grounding instruction, it is not
#               constrained to use only the provided pages. Speculation
#               and general knowledge mix into the response alongside
#               the evidence.
#
#   Version 3 — grounding instruction + evidence + question
#               The system is told to use only the provided evidence.
#               The response is traceable to specific pages. Nothing
#               beyond the evidence appears.
#
# The grounding instruction is what separates a reliable evidence-based
# answer from an answer that sounds correct but cannot be verified.
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
# The Retrieval Desk + Precision Ranker (standalone)
# ---------------------------------------------------------------------------

def retrieve(question, archive, top_k=3):
    query_fingerprint = embed_passage(question)
    results = archive.search(query_fingerprint, top_k=top_k)
    return query_fingerprint, results


def extract_content_words(question):
    cleaned = question.lower()
    for ch in "?.,!":
        cleaned = cleaned.replace(ch, "")
    return [w for w in cleaned.split() if len(w) >= 5]


def rerank(question, candidates):
    content_words = extract_content_words(question)
    rescored = []
    for c in candidates:
        text_lower   = c["text"].lower()
        exact_hits   = [w for w in content_words if w in text_lower]
        term_score   = len(exact_hits) / len(content_words) if content_words else 0.0
        rerank_score = round(0.6 * c["score"] + 0.4 * term_score, 4)
        rescored.append({**c, "rerank_score": rerank_score,
                         "term_score": round(term_score, 4),
                         "exact_hits": exact_hits})
    rescored.sort(key=lambda e: -e["rerank_score"])
    return rescored


# ---------------------------------------------------------------------------
# The Detective's Brief — grounding instruction
# ---------------------------------------------------------------------------

GROUNDING_INSTRUCTION = """\
You are reviewing evidence from a cold case file.
Answer the question using ONLY the evidence pages provided below.
Do not draw on knowledge outside these pages.
If the answer is not present in the evidence, state that clearly."""


# ---------------------------------------------------------------------------
# The Detective's Brief — brief builder
# ---------------------------------------------------------------------------

def build_brief(question, evidence_pages=None, grounding=False):
    """
    Assemble the detective's brief: the complete prompt delivered to
    the intelligence system.

    Parameters:
        question       — the detective's natural language question
        evidence_pages — list of reranked result dicts (from the archive)
        grounding      — whether to prepend the grounding instruction

    The brief has three optional components, assembled in order:
        1. Grounding instruction  (if grounding=True)
        2. Evidence pages         (if evidence_pages provided)
        3. Question               (always present)
    """
    sections = []

    if grounding and evidence_pages:
        sections.append(GROUNDING_INSTRUCTION)
        sections.append("")
        sections.append("─" * 58)
        sections.append("")

    if evidence_pages:
        sections.append("Evidence Pages:")
        sections.append("")
        for result in evidence_pages:
            sections.append(f"[Page {result['page_num']:02d}]")
            sections.append(result["text"])
            sections.append("")
        sections.append("─" * 58)
        sections.append("")

    sections.append(f"Question: {question}")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Simulated Intelligence System
#
# Not a real language model. Demonstrates how the same system responds
# to three different brief structures. The response depends entirely on
# what the brief contains — not on any change to the system itself.
# ---------------------------------------------------------------------------

class SimulatedLLM:
    """
    Simulates an intelligence system with a training cutoff of December 2018.
    The Millbrook Arson of 2019 is outside its training data.

    The response changes based on what the brief contains:
      - No evidence  → knowledge gap response (cannot answer)
      - Evidence, no grounding → answers using evidence, but speculation
                                  from training knowledge mixes in
      - Evidence + grounding   → answers strictly from the provided pages
    """

    TRAINING_CUTOFF = "December 2018"

    def ask(self, brief):
        has_evidence  = "[Page" in brief
        has_grounding = "ONLY" in brief and "not draw" in brief

        if not has_evidence:
            return (
                "I have no information relevant to that question. "
                "The Millbrook Arson of 2019 falls outside my training data "
                f"(cutoff: {self.TRAINING_CUTOFF}). No cold case files from "
                "that period were included in my training set."
            )

        if not has_grounding:
            return (
                "Petroleum distillate was the primary accelerant used in the fire. "
                "This type of accelerant is favoured in commercial arson due to its "
                "low cost, wide availability, and rapid ignition profile. "
                "The four square metre application at the northwest corner, combined "
                "with stairwell traces, indicates the perpetrator had prior access "
                "to the building. The rear entry and exit pattern is consistent with "
                "a deliberate, low-profile approach."
            )

        return (
            "Based on the provided evidence only: petroleum distillate was "
            "confirmed as the primary accelerant (Page 4 — Forensic Findings). "
            "Concentration levels indicated deliberate application across "
            "approximately four square metres. Secondary residue traces "
            "consistent with petroleum distillate were recovered from the "
            "northeast stairwell (Page 5). No claims beyond these evidence "
            "pages have been made in this response."
        )


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


def _wrap_text(text, width=56):
    """Word-wrap a single line of text to fit within width characters."""
    if len(text) <= width:
        return [text]
    words = text.split()
    if not words:
        return [""]
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        if len(trial) <= width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines if lines else [text[:width]]


def print_brief(brief, label):
    print(f"  ╔═ {label} {'═' * (57 - len(label))}╗")
    for line in brief.splitlines():
        for wl in _wrap_text(line, width=56):
            print(f"  ║  {wl:<56}║")
    print(f"  ╚{'═' * 60}╝")


def print_response(response, label="RESPONSE"):
    print(f"  [{label}]")
    words = response.split()
    line, lines = [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) > 58:
            lines.append(" ".join(line[:-1]))
            line = [word]
    if line:
        lines.append(" ".join(line))
    for l in lines:
        print(f"  {l}")


# ---------------------------------------------------------------------------
# Build the archive
# ---------------------------------------------------------------------------

case_text = load_case_file("millbrook_arson_2019.txt")
chunks    = chunk_text(case_text, chunk_size=60, overlap=15)
archive   = EvidenceArchive()

for i, chunk in enumerate(chunks):
    archive.add(page_num=i + 1, text=chunk, fingerprint=embed_passage(chunk))

QUESTION = "What accelerant was used in the Millbrook Arson?"

_, candidates = retrieve(QUESTION, archive, top_k=3)
evidence       = rerank(QUESTION, candidates)

llm = SimulatedLLM()


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 8")
print()
print("  Milestone:")
print("  The Detective's Brief")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive Room — Brief Assembly")
print()
print("  Objective:")
print("  Assemble the prompt. Demonstrate why grounding matters.")
print("=" * 66)

print(f"""
The archive has retrieved and reranked the top 3 evidence pages
for the detective's question:

  Question: "{QUESTION}"

  Retrieved (reranked):  Pages {[r['page_num'] for r in evidence]}

The brief is now assembled — a structured prompt that delivers
the right evidence to the intelligence system, along with the
precise instruction that governs how it must respond.

Three versions are shown. The same question. The same evidence.
Different brief structures. Different outcomes.
""")


# ---------------------------------------------------------------------------
# Brief components
# ---------------------------------------------------------------------------

print("-" * 66)
print("  THE THREE COMPONENTS OF A DETECTIVE'S BRIEF")
print("-" * 66)
print("""
  Component 1 — The Grounding Instruction
  ─────────────────────────────────────────
  Tells the intelligence system to use ONLY the provided evidence.
  Without this, the system may draw on its training data —
  producing answers that sound correct but cannot be traced back
  to a specific page in the file.

  Component 2 — The Evidence Pages
  ─────────────────────────────────
  The reranked pages from the archive. Retrieved by fingerprint
  similarity, reranked by exact term coverage. The system reads
  these before answering.

  Component 3 — The Question
  ───────────────────────────
  The detective's natural language question. Placed last, after
  the evidence, so the system reads the context first.
""")


# ---------------------------------------------------------------------------
# Version 1 — question only
# ---------------------------------------------------------------------------

brief_v1 = build_brief(QUESTION, evidence_pages=None, grounding=False)

print("=" * 66)
print("  VERSION 1 — question only, no evidence")
print("=" * 66)
print()
print_brief(brief_v1, "BRIEF V1")
print()
response_v1 = llm.ask(brief_v1)
print_response(response_v1, "INTELLIGENCE SYSTEM")
print()
print("  Outcome: the system cannot answer. The case falls outside")
print("  its training cutoff (December 2018). The evidence exists in")
print("  the archive — but the brief delivered nothing to work from.")


# ---------------------------------------------------------------------------
# Version 2 — evidence + question, no grounding
# ---------------------------------------------------------------------------

brief_v2 = build_brief(QUESTION, evidence_pages=evidence, grounding=False)

print()
print("=" * 66)
print("  VERSION 2 — evidence + question, no grounding instruction")
print("=" * 66)
print()
print_brief(brief_v2, "BRIEF V2")
print()
response_v2 = llm.ask(brief_v2)
print_response(response_v2, "INTELLIGENCE SYSTEM")
print()
print("  The system produces an answer. But not all of it comes from")
print("  the provided evidence. Annotation:")
print()
print("  ✓  \"Petroleum distillate was the primary accelerant\"")
print("       Source: Page 4 — directly stated.")
print()
print("  ✗  \"favoured in commercial arson due to low cost, wide")
print("       availability, and rapid ignition profile\"")
print("       Not in any evidence page. From training knowledge.")
print()
print("  ✓  \"four square metre application at the northwest corner\"")
print("       Source: Page 4 — directly stated.")
print()
print("  ✓  \"stairwell traces\" — Source: Page 5 — directly stated.")
print()
print("  ✗  \"perpetrator had prior access to the building\"")
print("       Not in any evidence page. Inference from training.")
print()
print("  ✗  \"deliberate, low-profile approach\"")
print("       Not in any evidence page. Speculation.")
print()
print("  3 of 5 sentences are grounded. 2 are not.")
print("  The response looks correct. Parts of it cannot be verified.")


# ---------------------------------------------------------------------------
# Version 3 — grounding + evidence + question
# ---------------------------------------------------------------------------

brief_v3 = build_brief(QUESTION, evidence_pages=evidence, grounding=True)

print()
print("=" * 66)
print("  VERSION 3 — grounding instruction + evidence + question")
print("=" * 66)
print()
print_brief(brief_v3, "BRIEF V3")
print()
response_v3 = llm.ask(brief_v3)
print_response(response_v3, "INTELLIGENCE SYSTEM")
print()
print("  Every sentence is traceable to a specific evidence page.")
print()
print("  ✓  \"petroleum distillate was confirmed as the primary")
print("       accelerant\" — Page 4, verbatim.")
print()
print("  ✓  \"deliberate application across approximately four")
print("       square metres\" — Page 4, verbatim.")
print()
print("  ✓  \"Secondary residue traces...northeast stairwell\"")
print("       — Page 5, verbatim.")
print()
print("  ✓  \"No claims beyond these evidence pages\"")
print("       — The grounding instruction enforced this.")
print()
print("  5 of 5 sentences are grounded. None are speculative.")


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

print()
print("-" * 66)
print("  COMPARISON — three briefs, three outcomes")
print("-" * 66)
print()
print(f"  {'Version':<12}  {'Evidence':>8}  {'Grounding':>9}  outcome")
print(f"  {'───────':<12}  {'────────':>8}  {'─────────':>9}  ───────")
print(f"  {'V1':<12}  {'No':>8}  {'No':>9}  Cannot answer — knowledge gap")
print(f"  {'V2':<12}  {'Yes':>8}  {'No':>9}  Answers, but speculation mixes in")
print(f"  {'V3':<12}  {'Yes':>8}  {'Yes':>9}  Answers strictly from evidence")
print()
print("  The intelligence system did not change between versions.")
print("  Only the brief changed. The brief determines the answer.")


print("""
==========================

Investigation Summary

The Detective's Brief has three components:
  1. Grounding instruction — constrains the system to provided evidence
  2. Evidence pages        — the reranked output of the retrieval stack
  3. Question              — placed last, after the context is set

Removing the grounding instruction leaves the system unconstrained.
It answers from both the evidence and its own training knowledge.
The parts drawn from training cannot be traced or verified.

Adding the grounding instruction changes the outcome. The system
reads the instruction, reads the evidence, and answers only from
what it can see. Every claim points back to a page number.

This traceability is what makes a RAG system reliable. The answer
is not generated from memory — it is generated from retrieved,
source-labelled evidence, under an explicit instruction to stay
within it.

AI Connection

In production RAG systems, the grounding instruction is part of the
system prompt — the persistent instruction that precedes every
conversation. It typically reads:

  "Answer only from the provided context. If the answer is not
   present in the context, say you do not know."

This single instruction is responsible for much of the reduction in
hallucination that RAG provides over a bare LLM. The retrieval
pipeline finds the right evidence. The grounding instruction ensures
the model uses it and nothing else.

Continue Investigation

All eight components are now built:
  retrieve → rerank → brief → answer

The final milestone assembles the complete pipeline end to end —
one question in, one grounded answer out.

Open:
    09_complete_archive.py
""")
