# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 6
#
# Morgan sits down at his desk with the full evidence board in front of him.
# He has five pieces of evidence. He has one burning question:
#
#   "Who had both the MOTIVE and the ACCESS to steal the Royal Diamond?"
#
# That question is his QUERY. Each piece of evidence is a KEY.
# ATTENTION scores how relevant each key is to the query, then blends
# the most relevant evidence into a single focused output.
# This is how transformers decide where to look.
# =============================================================================

import math


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def softmax(scores):
    """Convert raw scores into probabilities that sum to 1."""
    max_s = max(scores)
    exps  = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def attention(query, keys, values):
    """
    Compute attention output for a single query.

    1. Score each key: dot(query, key) / sqrt(d_k)
    2. Softmax → attention weights (sum to 1)
    3. Weighted sum of values → context output
    """
    d_k     = len(query)
    scores  = [dot_product(query, k) / math.sqrt(d_k) for k in keys]
    weights = softmax(scores)
    d_v     = len(values[0])
    output  = [sum(weights[j] * values[j][i] for j in range(len(values)))
               for i in range(d_v)]
    return weights, [round(x, 4) for x in output]


# ---------------------------------------------------------------------------
# Morgan's query vs. each piece of evidence from the crime scene
# Dimensions: [motive_signal, access_signal, physical_link, timing_match]
# ---------------------------------------------------------------------------

# Morgan's question: who had motive AND access?
query_morgan = [0.90, 0.85, 0.50, 0.60]

evidence = {
    "blackwell_at_museum":   ([0.90, 0.55, 0.60, 0.85], [0.90, 0.55, 0.60, 0.85]),
    "vault_keypad_log":      ([0.10, 0.95, 0.80, 0.90], [0.10, 0.95, 0.80, 0.90]),
    "dropped_business_card": ([0.85, 0.40, 0.90, 0.70], [0.85, 0.40, 0.90, 0.70]),
    "cctv_footage_gap":      ([0.20, 0.80, 0.40, 0.95], [0.20, 0.80, 0.40, 0.95]),
    "muddy_footprints":      ([0.30, 0.50, 0.95, 0.60], [0.30, 0.50, 0.95, 0.60]),
}

keys   = [v[0] for v in evidence.values()]
values = [v[1] for v in evidence.values()]
names  = list(evidence.keys())

print("=" * 62)
print("  CASE FILE 06")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Attention")
print()
print("  Investigation Status:")
print("  Active — Investigation Focus, Day 2")
print()
print("  Objective:")
print("  Score every piece of evidence against Morgan's key question")
print("  and synthesise the most relevant findings into one output.")
print("=" * 62)

print("""
Morgan stands at the whiteboard and writes one question:

  "Who had MOTIVE and ACCESS to steal the Royal Diamond?"

That question becomes his QUERY vector. Every piece of evidence
on the board is a KEY. Attention will tell him which keys are
most relevant to his query — and how much to trust each one.
""")

print(f"Morgan's query vector:  {query_morgan}")
print(f"Dimensions: [motive_signal, access_signal, physical_link, timing_match]")

weights, output = attention(query_morgan, keys, values)

print(f"\n  {'Evidence':<26}  {'Attention':>10}  Relevance")
print(f"  {'-'*62}")
for name, w in zip(names, weights):
    bar = "█" * int(w * 50)
    print(f"  {name:<26}  {w:>10.4f}  {bar}")

print(f"\n  Weights sum: {sum(weights):.4f}  (always = 1.0)")
print(f"\nSynthesised focus output (weighted blend of all evidence):")
print(f"  {output}")

print("""
  Morgan points to the top two results.

  "The vault keypad log and Blackwell's presence at the museum
   score highest. Not because I chose them. Because the math did.
   Attention weights tell the model WHERE to look for each query.
   Nothing is ignored — it's all blended, weighted by relevance."
""")

print("""
==========================

Investigation Summary

Morgan writes one question — "Who had motive AND access?" — and converts
it into a query vector. Every piece of evidence is scored against that
query. The vault keypad log and Blackwell's confirmed presence at the
museum receive the highest attention weights. The math confirms the lead.

AI Connection

Attention lets the model ask a targeted question (query) and retrieve
the most relevant context (keys). The output is a weighted blend of all
values — not a single chosen answer but a soft focus where everything
contributes and nothing is discarded.

Continue Investigation

Tomorrow every clue will question every other clue — not just one
detective's query, but a full cross-examination across the evidence board.
Open:
    07_self_attention.py
""")
