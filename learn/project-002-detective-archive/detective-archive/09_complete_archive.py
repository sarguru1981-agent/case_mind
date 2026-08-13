# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 9
#
# This is the complete Detective Archive.
#
# Milestones 1 through 8 built every component of a RAG pipeline —
# one concept at a time. This milestone runs the full pipeline end
# to end, tracing every step from a raw case file to a grounded
# answer.
#
# PIPELINE OVERVIEW
# ─────────────────────────────────────────────────────────────────
#
#   DOCUMENT INTAKE — build time, done once
#
#     raw document  →  [1: Load]         →  text
#     text          →  [2: Split]        →  pages
#     pages         →  [3: Fingerprint]  →  vectors
#     vectors       →  [4: Index]        →  archive
#
#   QUERY PROCESSING — query time, once per question
#
#     question  →  [5: Receive]   →  question + query fingerprint
#               →  [6: Retrieve]  →  candidate pages
#               →  [7: Rerank]    →  ranked evidence
#               →  [8: Brief]     →  grounded prompt
#               →  [9: LLM]       →  answer
#
# ─────────────────────────────────────────────────────────────────
#
# Step 9 is the LLM boundary. Project 001 already implemented the
# internals: tokenisation, embeddings, transformer layers, output
# distribution. This pipeline stops at the boundary and calls the
# LLM through a single interface:
#
#   llm.ask(brief)  →  answer
#
# In production, one line changes:
#   SimulatedLLM()  →  AnthropicClient() / OpenAI() / HuggingFace()
#
# Nothing else in the pipeline changes.
#
# =============================================================================

import os
import math


# ---------------------------------------------------------------------------
# Component 1 — The Fingerprint Engine
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
# Component 2 — The Relevance Scorer
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a, vec_b):
    dot   = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Component 3 — The Evidence Archive
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
# Component 4 — The Retrieval Desk
# ---------------------------------------------------------------------------

def retrieve(question, archive, top_k=3):
    query_fingerprint = embed_passage(question)
    results = archive.search(query_fingerprint, top_k=top_k)
    return query_fingerprint, results


# ---------------------------------------------------------------------------
# Component 5 — The Precision Ranker
# ---------------------------------------------------------------------------

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
        rescored.append({**c,
                         "rerank_score": rerank_score,
                         "term_score":   round(term_score, 4),
                         "exact_hits":   exact_hits})
    rescored.sort(key=lambda e: -e["rerank_score"])
    return rescored


# ---------------------------------------------------------------------------
# Component 6 — The Detective's Brief
# ---------------------------------------------------------------------------

GROUNDING_INSTRUCTION = """\
You are reviewing evidence from a cold case file.
Answer the question using ONLY the evidence pages provided below.
Do not draw on knowledge outside these pages.
If the answer is not present in the evidence, state that clearly."""


def build_brief(question, evidence_pages, grounding=True):
    sections = []
    if grounding:
        sections.append(GROUNDING_INSTRUCTION)
        sections.append("")
        sections.append("─" * 58)
        sections.append("")
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
# Component 7 — The LLM (simulated)
#
# Interface: llm.ask(brief) → answer
#
# In production, replace SimulatedLLM with any LLM client that
# exposes the same call signature. The pipeline does not change.
#
#   Production example (Anthropic):
#
#     from anthropic import Anthropic
#     client = Anthropic()
#
#     def ask(brief):
#         return client.messages.create(
#             model="claude-opus-4-7",
#             max_tokens=512,
#             messages=[{"role": "user", "content": brief}]
#         ).content[0].text
#
# ---------------------------------------------------------------------------

class SimulatedLLM:
    """
    A simulated LLM with a training cutoff of December 2018.
    The Millbrook Arson of 2019 is outside its training data.

    Exposes llm.ask(brief) — identical to the production interface.
    Behaviour is determined by the brief structure, not the model weights.
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
                "The stairwell traces indicate the perpetrator had prior access "
                "to the building."
            )

        return (
            "Based on the provided evidence only: petroleum distillate was "
            "confirmed as the primary accelerant (Page 4 — Forensic Findings). "
            "Concentration levels indicated deliberate application across "
            "approximately four square metres at the northwest origin point. "
            "Secondary residue traces were recovered from the northeast "
            "stairwell, suggesting the perpetrator entered and exited via the "
            "building's rear access point (Page 5). No claims beyond these "
            "evidence pages have been made."
        )


# ---------------------------------------------------------------------------
# Utility
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


def wrap(text, width=58, indent="  "):
    words = text.split()
    lines, line = [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) > width:
            lines.append(indent + " ".join(line[:-1]))
            line = [word]
    if line:
        lines.append(indent + " ".join(line))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The Complete Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(question, archive, llm, top_k=3):
    """
    Query-time pipeline: steps 5 through 9.
    Build-time steps (1–4) are handled outside this function.
    """
    query_fp, candidates = retrieve(question, archive, top_k=top_k)
    evidence = rerank(question, candidates)
    brief    = build_brief(question, evidence, grounding=True)
    answer   = llm.ask(brief)
    return {
        "question":   question,
        "query_fp":   query_fp,
        "candidates": candidates,
        "evidence":   evidence,
        "brief":      brief,
        "answer":     answer,
    }


# ===========================================================================
# OUTPUT
# ===========================================================================

QUESTION   = "What accelerant was used in the Millbrook Arson?"
CASE_FILE  = "millbrook_arson_2019.txt"
CHUNK_SIZE = 60
OVERLAP    = 15
TOP_K      = 3

print("=" * 66)
print("  MILESTONE 9")
print()
print("  Milestone:")
print("  The Complete Detective Archive")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Archive — Full Pipeline Active")
print()
print("  Objective:")
print("  Run the complete RAG pipeline. One question. One answer.")
print("=" * 66)

print("""
  DOCUMENT INTAKE                       QUERY PROCESSING
  ─────────────────────────────         ─────────────────────────────────────
  [1] Load       raw text               [5] Receive    question → fingerprint
  [2] Split      text → pages           [6] Retrieve   fingerprint → candidates
  [3] Fingerprint pages → vectors       [7] Rerank     candidates → evidence
  [4] Index      vectors → archive      [8] Brief      evidence → prompt
                                        [9] LLM        prompt → answer
""")


# ---------------------------------------------------------------------------
# STEP 1 — Load
# ---------------------------------------------------------------------------

print("─" * 66)
print("  STEP 1 — Load case file")
print("─" * 66)
print()

case_text  = load_case_file(CASE_FILE)
word_count = len(case_text.split())

print(f"  File:   case-files/{CASE_FILE}")
print(f"  Words:  {word_count}")
print(f"  Status: loaded")


# ---------------------------------------------------------------------------
# STEP 2 — Split
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 2 — Split into pages")
print("─" * 66)
print()

chunks = chunk_text(case_text, CHUNK_SIZE, OVERLAP)

print(f"  chunk_size={CHUNK_SIZE}, overlap={OVERLAP}")
print(f"  Pages produced: {len(chunks)}")
print()
for i, chunk in enumerate(chunks):
    wc = len(chunk.split())
    print(f"  [Page {i+1:02d}]  ({wc:>2} words)  \"{first_words(chunk, 8)}...\"")


# ---------------------------------------------------------------------------
# STEP 3 — Fingerprint
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 3 — Generate fingerprints")
print("─" * 66)
print()

fingerprints = [embed_passage(c) for c in chunks]

print(f"  Dimensions: {DIM_NAMES}")
print()
print(f"  {'Page':<6}  {'incident':>8}  {'forensic':>8}  "
      f"{'timeline':>8}  {'investig':>8}  {'conclusn':>8}")
print(f"  {'────':<6}  {'────────':>8}  {'────────':>8}  "
      f"{'────────':>8}  {'────────':>8}  {'────────':>8}")
for i, fp in enumerate(fingerprints):
    print(f"  [P{i+1:02d}]   "
          f"  {fp[0]:>6.2f}    {fp[1]:>6.2f}    "
          f"{fp[2]:>6.2f}    {fp[3]:>6.2f}    {fp[4]:>6.2f}")


# ---------------------------------------------------------------------------
# STEP 4 — Index
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 4 — Index the archive")
print("─" * 66)
print()

archive = EvidenceArchive()
for i, (chunk, fp) in enumerate(zip(chunks, fingerprints)):
    archive.add(page_num=i + 1, text=chunk, fingerprint=fp)

print(f"  {len(archive)} pages indexed.")
print(f"  Archive ready.")
print()
print("  ── Build time complete. Archive is standing by. ──────────")


# ---------------------------------------------------------------------------
# STEP 5 — Receive question
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 5 — Question received")
print("─" * 66)
print()

query_fp = embed_passage(QUESTION)

print(f"  Detective Morgan submits:")
print(f"  \"{QUESTION}\"")
print()
print(f"  Query fingerprint generated:")
print(f"  {query_fp}")
print()
for dim, kw_list in FINGERPRINT_DIMENSIONS.items():
    hits = [kw for kw in kw_list if kw in QUESTION.lower()]
    if hits:
        score = round(min(len(hits) / 3.0, 1.0), 2)
        print(f"    {dim:<14}  {hits}  →  {score}")


# ---------------------------------------------------------------------------
# STEP 6 — Retrieve
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 6 — Retrieval Desk")
print("─" * 66)
print()

_, candidates = retrieve(QUESTION, archive, top_k=TOP_K)

print(f"  archive.search(query_fp, top_k={TOP_K})")
print()
print(f"  {'Page':<6}  {'Score':>6}  {'Bar':<10}  preview")
print(f"  {'────':<6}  {'─────':>6}  {'──────────'}")
for c in candidates:
    print(f"  [P{c['page_num']:02d}]   {c['score']:>5.4f}  "
          f"{bar(c['score']):<10}  \"{first_words(c['text'], 8)}...\"")

print()
print(f"  Candidates returned: {[c['page_num'] for c in candidates]}")


# ---------------------------------------------------------------------------
# STEP 7 — Rerank
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 7 — Precision Ranker")
print("─" * 66)
print()

evidence = rerank(QUESTION, candidates)
content_words = extract_content_words(QUESTION)

print(f"  Content words: {content_words}")
print()
print(f"  {'Page':<6}  {'Retrieval':>9}  {'Term':>5}  "
      f"{'Combined':>8}  {'Bar':<10}  hits")
print(f"  {'────':<6}  {'─────────':>9}  {'────':>5}  {'────────':>8}  {'──────────'}")
for e in evidence:
    hits = str(e["exact_hits"]) if e["exact_hits"] else "[none]"
    print(f"  [P{e['page_num']:02d}]    {e['score']:>9.4f}  "
          f"{e['term_score']:>5.4f}  {e['rerank_score']:>8.4f}  "
          f"{bar(e['rerank_score']):<10}  {hits}")

print()
print(f"  Ranked evidence: {[e['page_num'] for e in evidence]}")


# ---------------------------------------------------------------------------
# STEP 8 — Brief
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  STEP 8 — Detective's Brief assembled")
print("─" * 66)
print()

brief = build_brief(QUESTION, evidence, grounding=True)

print("  build_brief(question, evidence, grounding=True)")
print()
print(f"  Component 1 — Grounding instruction  ✓")
print(f"    \"{GROUNDING_INSTRUCTION.splitlines()[0]}\"")
print(f"    \"{GROUNDING_INSTRUCTION.splitlines()[1]}\"")
print()
print(f"  Component 2 — Evidence pages  ✓")
for e in evidence:
    print(f"    [Page {e['page_num']:02d}]  rerank_score={e['rerank_score']:.4f}  "
          f"\"{first_words(e['text'], 8)}...\"")
print()
print(f"  Component 3 — Question  ✓")
print(f"    \"{QUESTION}\"")
print()

brief_words = len(brief.split())
print(f"  Brief assembled: {brief_words} words total.")
print("  The brief is ready for the LLM boundary.")


# ---------------------------------------------------------------------------
# STEP 9 — LLM Boundary
# ---------------------------------------------------------------------------

print()
print("━" * 66)
print("  STEP 9 — THE LLM BOUNDARY")
print("━" * 66)

print("""
  Project 001 already built the internals:

    raw text
      → tokeniser        (text → token IDs)
      → embedding lookup (token IDs → vectors)
      → transformer      (vectors → contextual representations)
      → output head      (representations → probability distribution)
      → sampled token    (distribution → next word)

  Those internals are already understood.
  This pipeline stops at the boundary and treats the LLM as a
  callable that receives a brief and returns an answer.

  ─────────────────────────────────────────────────────────────
  INTERFACE
  ─────────────────────────────────────────────────────────────

  In production — swap SimulatedLLM for any real model client:

    # Anthropic
    from anthropic import Anthropic
    client = Anthropic()
    answer = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": brief}]
    ).content[0].text

    # OpenAI
    from openai import OpenAI
    client = OpenAI()
    answer = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": brief}]
    ).choices[0].message.content

  In this build — same call signature, simulated response:

    llm = SimulatedLLM()
    answer = llm.ask(brief)

  The pipeline calls llm.ask(brief).
  What happens inside the boundary does not change the pipeline.
  ─────────────────────────────────────────────────────────────
""")

llm    = SimulatedLLM()
answer = llm.ask(brief)

print("  Calling: llm.ask(brief)")
print()
print("  ..." * 10)


# ---------------------------------------------------------------------------
# Final answer
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  FINAL ANSWER")
print("─" * 66)
print()
print(wrap(answer))
print()
print("  Source pages used:")
for e in evidence:
    print(f"    [Page {e['page_num']:02d}]  rerank_score={e['rerank_score']:.4f}  "
          f"\"{first_words(e['text'], 10)}...\"")


# ---------------------------------------------------------------------------
# Before vs After
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  BEFORE AND AFTER — the gap that RAG closes")
print("─" * 66)
print()

brief_no_context = QUESTION
answer_no_context = llm.ask(brief_no_context)

print(f"  Question: \"{QUESTION}\"")
print()
print("  BEFORE (Milestone 1 — no archive, no retrieval):")
print()
print(wrap(answer_no_context, indent="    "))
print()
print("  AFTER (Milestone 9 — full RAG pipeline):")
print()
print(wrap(answer, indent="    "))
print()
print("  Same LLM. Same question. Different brief.")
print("  The archive changed what the system could see.")
print("  Retrieval changed what the system could answer.")


# ---------------------------------------------------------------------------
# Pipeline recap
# ---------------------------------------------------------------------------

print()
print("─" * 66)
print("  PIPELINE RECAP")
print("─" * 66)
print()
print(f"  [1]  Loaded:     case-files/{CASE_FILE} ({word_count} words)")
print(f"  [2]  Split:      {len(chunks)} pages "
      f"(chunk_size={CHUNK_SIZE}, overlap={OVERLAP})")
print(f"  [3]  Fingerprinted: {len(fingerprints)} vectors ({len(DIM_NAMES)} dimensions each)")
print(f"  [4]  Indexed:    {len(archive)} pages in archive")
print(f"  [5]  Question:   \"{QUESTION[:50]}...\"")
print(f"       Fingerprint: {query_fp}")
print(f"  [6]  Retrieved:  top {TOP_K} pages → "
      f"{[c['page_num'] for c in candidates]}")
content_words = extract_content_words(QUESTION)
print(f"  [7]  Reranked:   content words {content_words} → "
      f"{[e['page_num'] for e in evidence]}")
print(f"  [8]  Brief:      grounding ✓  evidence ✓  question ✓  "
      f"({brief_words} words)")
print(f"  [9]  LLM:        llm.ask(brief) → {len(answer.split())} word answer")


print("""
==========================

Investigation Summary

The Complete Detective Archive is a nine-step RAG pipeline.
Four steps at build time prepare the evidence store.
Five steps at query time turn a question into a grounded answer.

The pipeline is modular. Each component has one responsibility:

  Load       — reads a file
  Split      — produces pages
  Fingerprint — produces vectors
  Index      — stores (text, vector) pairs
  Retrieve   — finds similar vectors
  Rerank     — scores by exact evidence coverage
  Brief      — assembles the prompt
  LLM        — generates from context

Every component can be upgraded independently. A better chunking
strategy, a stronger embedding model, a more precise reranker —
each slot is interchangeable without changing the others.

The LLM boundary is the final slot. It is already understood from
Project 001. It accepts a brief. It returns an answer. That is
its contract with the pipeline.

AI Connection

This is what every production RAG system does. The sophistication
is in the embedding model (sentence transformers, not keyword
scoring), the vector store at scale (FAISS, Pinecone, Chroma),
the reranker (a cross-encoder, not term overlap), and the LLM
(a production model, not a simulation).

But the pipeline — load, split, embed, index, retrieve, rerank,
brief, generate — is the same. Understanding it at this scale
means understanding what the production system is doing, because
the logic is identical.

The case is on record.
The archive is built.
The investigation is open.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What Comes Next

The Detective Archive retrieves evidence. It does this well.
Given a question, it finds the pages most likely to hold the
answer and places them in front of the intelligence system.

But retrieval is only half the problem.

The archive assumes that the evidence it retrieves is reliable.
It assumes that what is in the case file is accurate, complete,
and free of error. It does not question its sources.

This assumption is fragile.

Cold case files can contain gaps. Investigation notes can record
what a witness believed, not what happened. Documents can be
filed out of sequence. A forensic report can reference a
follow-up that was never completed. A partial plate number in
one file can conflict with a full plate number in another.

The archive retrieves what is there. It cannot know whether
what is there should be trusted.

When retrieved evidence itself is flawed, the grounding
instruction makes things worse, not better. "Answer from the
provided evidence only" becomes an instruction to answer from
unreliable material — confidently, with no warning.

This is the next problem.

It is not a retrieval problem. Retrieval worked correctly.
It is not a generation problem. The LLM followed its brief.
It is a verification problem: the evidence reached the system,
but the system had no way to evaluate whether it should be
believed.

The Police Department's next challenge is not building a
better archive. It is building a system that knows when to
trust what it finds.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 Part 4 — The Wrong Evidence That Made RAG Hallucinate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
