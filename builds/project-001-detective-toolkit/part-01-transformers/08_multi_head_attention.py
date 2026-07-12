# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 8
#
# Inspector Davies sends three specialist detectives to review the case file.
# Each has been trained to focus on a completely different dimension:
#
#   DS Foster  — MOTIVE: who wanted the diamond and why
#   DC Patel   — EVIDENCE: physical traces left at the scene
#   DI Reeves  — TIMELINE: when and where each event occurred
#
# They examine the same five clues but find different patterns. Their
# reports are then combined. This is MULTI-HEAD ATTENTION — parallel
# attention passes from multiple perspectives, concatenated into one output
# richer than any single detective could produce alone.
# =============================================================================

import math


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def softmax(scores):
    max_s = max(scores)
    exps  = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def single_head_attention(queries, keys, values):
    """One specialist's full attention pass over the evidence."""
    d_k     = len(keys[0])
    outputs = []
    for q in queries:
        scores  = [dot_product(q, k) / math.sqrt(d_k) for k in keys]
        weights = softmax(scores)
        d_v     = len(values[0])
        ctx     = [sum(weights[j] * values[j][i] for j in range(len(values)))
                   for i in range(d_v)]
        outputs.append([round(x, 4) for x in ctx])
    return outputs


# ---------------------------------------------------------------------------
# Five key clues as 6-dimensional vectors
# Dims 0–1: motive signal        (DS Foster's sub-space)
# Dims 2–3: physical evidence    (DC Patel's sub-space)
# Dims 4–5: timeline / location  (DI Reeves' sub-space)
# ---------------------------------------------------------------------------

clues = ["blackwell", "midnight", "vault",  "diamond",  "footprints"]
vecs  = [
    [0.90, 0.85, 0.40, 0.30, 0.75, 0.60],  # blackwell
    [0.30, 0.25, 0.20, 0.15, 0.95, 0.90],  # midnight
    [0.40, 0.35, 0.50, 0.55, 0.60, 0.70],  # vault
    [0.15, 0.20, 0.90, 0.85, 0.50, 0.40],  # diamond
    [0.55, 0.50, 0.90, 0.80, 0.60, 0.55],  # footprints
]

SPECIALISTS = {
    "DS Foster  — MOTIVE":   (0, 2, "Who wanted the diamond and why?"),
    "DC Patel   — EVIDENCE": (2, 4, "What physical traces were left?"),
    "DI Reeves  — TIMELINE": (4, 6, "When and where did each event occur?"),
}

print("=" * 62)
print("  CASE FILE 08")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Multi-Head Attention")
print()
print("  Investigation Status:")
print("  Active — Specialist Review, Day 2")
print()
print("  Objective:")
print("  Run three parallel attention passes — motive, physical")
print("  evidence, and timeline — then combine all findings.")
print("=" * 62)

print("""
Inspector Davies sends three specialists to review the same evidence.
Each one examines the same five clues — but through a different lens.

  "DS Foster looks at motive. DC Patel looks at physical evidence.
   DI Reeves looks at the timeline. No single detective sees everything.
   Together, they see it all."
""")

all_head_outputs = []

for specialist, (start, end, question) in SPECIALISTS.items():
    projected = [v[start:end] for v in vecs]
    outputs   = single_head_attention(projected, projected, projected)
    all_head_outputs.append(outputs)

    print(f"  {'─'*58}")
    print(f"  {specialist}")
    print(f'  Angle: "{question}"')
    print(f"  {'─'*58}")
    print(f"  {'Clue':<12}  Output (2D projection)")
    for clue, out in zip(clues, outputs):
        print(f"  {clue:<12}  {out}")
    print()

# Concatenate all three head outputs per clue
print(f"  {'─'*62}")
print("  Inspector Davies collects all three reports and combines them.")
print(f"  Concatenated output: 2D + 2D + 2D = 6D per clue")
print(f"  {'─'*62}")
for i, clue in enumerate(clues):
    combined = []
    for head_out in all_head_outputs:
        combined.extend(head_out[i])
    print(f"  {clue:<12}:  {[round(x, 3) for x in combined]}")

print("""
  "No single head captures all linguistic relationships," says Davies.
  "One head learns syntax. Another learns semantics. A third learns
   coreference. Concatenating them gives a richer representation.

   GPT-3 runs 96 heads simultaneously on every single token."
""")

print("""
==========================

Investigation Summary

DS Foster, DC Patel, and DI Reeves each examine the five clues through
their own lens — motive, physical evidence, and timeline respectively.
Each produces a 2D output per clue. Inspector Davies concatenates all
three reports into one 6D vector per clue, richer than any head alone.

AI Connection

Multi-head attention runs several attention mechanisms in parallel, each
projecting into a different sub-space and learning different relationships.
The concatenated output captures syntax, semantics, and coreference
simultaneously — the reason transformers outperform all prior architectures.

Continue Investigation

All specialist reports are in. The full team assembles for the final
briefing — one complete transformer layer will close the case.
Open:
    09_transformer_layer.py
""")
