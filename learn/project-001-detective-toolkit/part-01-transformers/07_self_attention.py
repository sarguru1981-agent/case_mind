# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 7
#
# Morgan spreads five key evidence cards on the table and says:
#   "Now let each one speak to the others."
#
# SELF-ATTENTION works exactly like that. Every clue acts as both
# questioner (query) and witness (key/value). "Footprints" asks:
#   "How much do I have in common with 'vault'? With 'midnight'?"
#
# By the end, each clue's representation has been enriched by information
# from every other clue on the table. No clue is analysed in isolation.
# =============================================================================

import math


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def softmax(scores):
    max_s = max(scores)
    exps  = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def weighted_sum(weights, vectors):
    """Blend a list of vectors according to attention weights."""
    d      = len(vectors[0])
    result = [0.0] * d
    for w, v in zip(weights, vectors):
        for i in range(d):
            result[i] += w * v[i]
    return [round(x, 4) for x in result]


def self_attention(token_vectors):
    """
    Each token attends to every other token (Q = K = V = token_vectors).

    For each token i:
      1. Score against every token j: dot(i, j) / sqrt(d_k)
      2. Softmax → attention weights for this row
      3. Weighted sum of all vectors → enriched representation

    Real transformers apply learned linear projections to get Q, K, V.
    """
    n, d_k           = len(token_vectors), len(token_vectors[0])
    outputs          = []
    attention_matrix = []

    for i in range(n):
        scores  = [dot_product(token_vectors[i], token_vectors[j]) / math.sqrt(d_k)
                   for j in range(n)]
        weights = softmax(scores)
        attention_matrix.append(weights)
        outputs.append(weighted_sum(weights, token_vectors))

    return outputs, attention_matrix


# ---------------------------------------------------------------------------
# The five key clues from the Royal Diamond Theft evidence board
# Dimensions: [suspicion, timing, access, physical_evidence, motive]
# ---------------------------------------------------------------------------

clues = ["blackwell", "midnight", "vault",  "diamond",  "footprints"]
vecs  = [
    [0.90, 0.75, 0.55, 0.40, 0.90],  # blackwell  — high suspicion + motive
    [0.40, 0.95, 0.60, 0.20, 0.30],  # midnight   — key timing signal
    [0.30, 0.60, 0.95, 0.50, 0.20],  # vault      — central access point
    [0.20, 0.50, 0.80, 0.90, 0.10],  # diamond    — the stolen item
    [0.60, 0.55, 0.70, 0.95, 0.50],  # footprints — physical evidence
]

print("=" * 62)
print("  CASE FILE 07")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Self-Attention")
print()
print("  Investigation Status:")
print("  Active — Evidence Cross-Examination, Day 2")
print()
print("  Objective:")
print("  Run full self-attention so every clue interrogates every")
print("  other clue and each representation is context-enriched.")
print("=" * 62)

print("""
Morgan spreads five evidence cards across the table.

  "I want each clue to interrogate every other clue," he says.
  "Footprints — do you support vault access? Midnight — do you
   narrow down who was present? Let them cross-examine each other."

This is self-attention: every token is simultaneously a questioner
and a witness. The attention matrix shows the result.
""")

outputs, attn_matrix = self_attention(vecs)

print("Attention matrix — how much each clue attends to every other:\n")
header = f"  {'':>13}" + "".join(f"  {t:>11}" for t in clues)
print(header)
print("  " + "-" * (13 + 13 * len(clues)))
for clue, row in zip(clues, attn_matrix):
    row_str = f"  {clue:>13}" + "".join(f"  {w:>11.3f}" for w in row)
    print(row_str)

print("""
  Read each row to see which clues each token finds most relevant.
  Notice that 'footprints' attends most strongly to 'blackwell' — the
  physical evidence pointing toward the prime suspect. That connection
  was not programmed. Self-attention discovered it from the vectors alone.
  No clue on this board analyses its meaning in isolation.
""")

print("\nBefore self-attention (raw clue vectors):")
for clue, vec in zip(clues, vecs):
    print(f"  {clue:<12}:  {vec}")

print("\nAfter self-attention (each clue enriched by the whole board):")
for clue, out in zip(clues, outputs):
    print(f"  {clue:<12}:  {out}")

print("""
  Morgan points to the 'footprints' row.

  "Look how much attention it pays to 'vault'. Physical evidence
   connecting directly to the access point — that's meaningful.
   After self-attention, every clue knows about every other clue.
   No token is left working alone."
""")

print("""
==========================

Investigation Summary

Morgan runs a full evidence cross-examination across the five key clues.
The attention matrix shows how strongly each clue attends to every other.
After self-attention, "footprints" carries information about "vault" and
"blackwell" — no clue is left analysing its own isolated meaning.

AI Connection

Self-attention is the mechanism that makes transformers context-aware. Every
token attends to every other token simultaneously, and each representation is
enriched by the full sequence. This is why a transformer understands
"bank" differently in "river bank" versus "bank robbery."

Continue Investigation

Three specialist detectives are about to examine the same evidence from
three completely different angles simultaneously.
Open:
    08_multi_head_attention.py
""")
