# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 4
#
# Morgan has three suspects. Tokens and IDs alone cannot capture WHO these
# people are. He needs to represent each suspect as a set of measurable
# characteristics — a profile card — so he can compare them mathematically.
#
# In AI, these profile cards are called EMBEDDINGS: dense vectors of numbers
# where each dimension captures a meaningful characteristic. Similar suspects
# end up with similar vectors. The model learns these values during training;
# here Morgan builds them by hand to show the idea clearly.
# =============================================================================

import math


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def magnitude(v):
    return math.sqrt(sum(x ** 2 for x in v))


def cosine_similarity(a, b):
    """Measures directional similarity. 1.0 = identical profile."""
    denom = magnitude(a) * magnitude(b)
    if denom == 0:
        return 0.0
    return dot_product(a, b) / denom


# ---------------------------------------------------------------------------
# Suspect and crime profile cards
# Dimensions: [motive, access, expertise, alibi_weakness, prior_record]
# ---------------------------------------------------------------------------

PROFILES = {
    # The three suspects
    "lord_blackwell":  [0.90, 0.55, 0.30, 0.85, 0.50],
    "lady_hartley":    [0.50, 0.40, 0.95, 0.35, 0.90],
    "mr_chen":         [0.30, 0.90, 0.60, 0.40, 0.10],
    "curator_walsh":   [0.15, 0.95, 0.55, 0.20, 0.05],
    # What profile did this crime actually require?
    "theft_required":  [0.85, 0.80, 0.70, 0.00, 0.40],
}

DIMS = ["motive", "access", "expertise", "alibi_weak", "prior_rec"]

print("=" * 62)
print("  CASE FILE 04")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Embeddings")
print()
print("  Investigation Status:")
print("  Active — Suspect Profiling, Day 1")
print()
print("  Objective:")
print("  Build 5-dimensional profile vectors for every suspect")
print("  and measure who most closely matches the theft profile.")
print("=" * 62)

print("""
Morgan opens a fresh notebook. Four suspects. He builds a profile
card for each one — a row of numbers capturing who they are.

  "I need to represent each person mathematically," he says.
  "So I can compare them. So I can measure who fits this crime."

Dimensions: motive, access to vault, expertise, alibi weakness, prior record.
""")

print(f"  {'Name':<18}", end="")
for d in DIMS:
    print(f"  {d:>10}", end="")
print()
print(f"  {'-'*74}")

for name, vec in PROFILES.items():
    marker = "  ← what the crime required" if name == "theft_required" else ""
    print(f"  {name:<18}", end="")
    for v in vec:
        print(f"  {v:>10.2f}", end="")
    print(marker)

# Compare each suspect to the theft profile
print("\nMorgan compares each suspect to what the crime required:\n")
print(f"  {'Suspect':<18}  {'Match Score':>12}  Verdict")
print(f"  {'-'*55}")

theft_vec = PROFILES["theft_required"]
for name, vec in PROFILES.items():
    if name == "theft_required":
        continue
    score = cosine_similarity(vec, theft_vec)
    if score > 0.90:
        label = "★ prime suspect"
    elif score > 0.75:
        label = "△ worth watching"
    else:
        label = "  lower priority"
    print(f"  {name:<18}  {score:>12.4f}  {label}")

print("""
  Morgan circles Lord Blackwell's name. Highest motive.
  Weakest alibi. Closest match to the theft profile.

  "In a real model, these numbers aren't hand-crafted," he notes.
  "They start random and are learned through training.
   Words used in similar contexts end up with similar vectors."
""")

print("""
==========================

Investigation Summary

Morgan builds five-dimensional profile cards for all four suspects and
for the theft itself. Cosine similarity reveals Lord Blackwell as the
closest match to what the crime required — highest motive, weakest alibi,
and a profile that aligns with the vault-breaking event at midnight.

AI Connection

Embeddings are dense vectors where each dimension captures a learnable
characteristic. In a real model, the values start random and are adjusted
through training until similar contexts produce similar vectors. This is how
the model learns that "detective" and "inspector" live near each other in space.

Continue Investigation

Suspect profiles are complete. The next challenge is the exact order of
events — the timeline of the theft must be reconstructed precisely.
Open:
    05_positional_encoding.py
""")
