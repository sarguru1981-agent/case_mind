# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 9
#
# Morgan calls the full team into the briefing room for the final review.
#
#   Stage 1 — Self-Attention: every clue shares what it knows with the others.
#   Stage 2 — Add & Norm: each clue keeps its original identity (residual),
#             then all vectors are normalised to a common scale.
#   Stage 3 — Feed-Forward: each clue privately processes the shared context.
#   Stage 4 — Add & Norm: one final residual connection and normalisation.
#
# This is ONE TRANSFORMER LAYER — the repeating unit of every LLM.
# Stack 12 of these and you have BERT. Stack 96 and you have GPT-3.
# At the end of this file: the case is closed.
# =============================================================================

import math


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def softmax(scores):
    max_s = max(scores)
    exps  = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def layer_norm(vec):
    """Normalise a vector to zero mean and unit variance."""
    mean = sum(vec) / len(vec)
    var  = sum((x - mean) ** 2 for x in vec) / len(vec)
    std  = math.sqrt(var + 1e-8)
    return [round((x - mean) / std, 4) for x in vec]


def add_and_norm(original, transformed):
    """Residual connection: element-wise add, then layer-normalise."""
    added = [o + t for o, t in zip(original, transformed)]
    return layer_norm(added)


def relu(x):
    return max(0.0, x)


def feed_forward(vec):
    """
    Simplified position-wise feed-forward.

    Real FFN:  Linear(d → 4d) → ReLU → Linear(4d → d) with learned weights.
    Here: expand to 2d with fixed mixing, ReLU, project back. Demonstrates
    the shape of the computation — not the learned values.
    """
    d      = len(vec)
    hidden = [relu(vec[i % d] * 0.6 + vec[(i + 1) % d] * 0.4) for i in range(d * 2)]
    output = [hidden[i] * 0.5 + hidden[i + d] * 0.5 for i in range(d)]
    return [round(x, 4) for x in output]


def self_attention(token_vecs):
    n, d_k = len(token_vecs), len(token_vecs[0])
    outputs = []
    for i in range(n):
        scores  = [dot_product(token_vecs[i], token_vecs[j]) / math.sqrt(d_k)
                   for j in range(n)]
        weights = softmax(scores)
        ctx     = [sum(weights[j] * token_vecs[j][k] for j in range(n))
                   for k in range(d_k)]
        outputs.append([round(x, 4) for x in ctx])
    return outputs


# ---------------------------------------------------------------------------
# The five key clues — same evidence board used in files 07 and 08
# ---------------------------------------------------------------------------

clues = ["blackwell", "midnight", "vault",  "diamond",  "footprints"]
vecs  = [
    [0.90, 0.75, 0.55, 0.40],
    [0.40, 0.95, 0.60, 0.20],
    [0.30, 0.60, 0.95, 0.50],
    [0.20, 0.50, 0.80, 0.90],
    [0.60, 0.55, 0.70, 0.95],
]

print("=" * 62)
print("  CASE FILE 09")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  The Transformer Layer")
print()
print("  Investigation Status:")
print("  Active — Final Briefing, Case Closing")
print()
print("  Objective:")
print("  Run one complete transformer layer on the five key clues")
print("  and close the Royal Diamond Theft investigation.")
print("=" * 62)

print("""
Morgan calls everyone into the briefing room.

  Stage 1 — Self-Attention:  every clue shares context with every other.
  Stage 2 — Add & Norm:      residual keeps identity; normalise the scale.
  Stage 3 — Feed-Forward:    each clue privately processes the new context.
  Stage 4 — Add & Norm:      one final residual and normalisation pass.

This is one complete transformer layer.
""")

# Sub-layer 1: Self-Attention + Add & Norm
attn_out  = self_attention(vecs)
post_attn = [add_and_norm(vecs[i], attn_out[i]) for i in range(len(vecs))]

# Sub-layer 2: Feed-Forward + Add & Norm
ffn_out   = [feed_forward(v) for v in post_attn]
final_out = [add_and_norm(post_attn[i], ffn_out[i]) for i in range(len(vecs))]

stages = [
    ("Stage 0 — Raw clue embeddings (input)",              vecs),
    ("Stage 1 — After self-attention + Add & Norm",        post_attn),
    ("Stage 2 — After feed-forward  + Add & Norm (final)", final_out),
]

for stage_name, stage_vecs in stages:
    print(f"  {'─'*60}")
    print(f"  {stage_name}")
    print(f"  {'─'*60}")
    for clue, vec in zip(clues, stage_vecs):
        print(f"    {clue:<12}:  {vec}")
    print()

print("""  Transformer layer structure (one block):

    Input
      │
      ├── [Self-Attention] ──► [Add & Norm] ──────────────┐
      │                                                    ↓
      └────────────────────────────────────────────────────┤
                                                           │
      ├── [Feed-Forward]  ──► [Add & Norm] ──► Final Output
      │                                                    ↑
      └────────────────────────────────────────────────────┘

  "Each layer adds a full round of reasoning," Morgan tells his team.
  "Stack 96 of these and the model can understand language the way
   a detective understands a case — every clue in full context."

  Lord Blackwell is arrested at dawn near the harbour.
  The Royal Diamond is recovered from a black bag in his car.
  Case closed.
""")

print("""
==========================

Investigation Summary

The full investigation team assembles for the final briefing. Self-attention,
residual connections, layer normalisation, and a feed-forward pass transform
the five key clues through two complete sub-layers. The representations
converge. Lord Blackwell is arrested at dawn. The Royal Diamond is recovered.

AI Connection

A transformer layer is the fundamental repeating unit of every LLM. Each
layer adds one complete round of reasoning — context sharing, identity
preservation, normalisation, and independent processing. Stack 96 of these
and the model reaches GPT-3-level language understanding.

Continue Investigation

The Royal Diamond Theft is solved. Detective Morgan has been invited to
train the next generation of investigators at the Police Academy.
Continue to:
    part-02-llm-training/01_training_examples.py
""")
