# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 5
#
# Morgan stands at the whiteboard and pins index cards in a row.
# The order of events is everything. "The vault was accessed THEN the
# diamond disappeared" is a very different story from "the diamond
# disappeared THEN the vault was accessed."
#
# Transformers process all tokens simultaneously — no loop, no sequence.
# They need POSITIONAL ENCODING: a mathematical signal injected into each
# token's vector so the model knows exactly where it sits in the timeline.
# =============================================================================

import math


def positional_encoding(position, d_model):
    """
    Compute one positional encoding vector for a given position.

    Even dimensions use sine; odd dimensions use cosine.
    The wavelengths form a geometric progression, giving each position
    a unique fingerprint that the model can decode to understand order.
    """
    encoding = []
    for i in range(d_model):
        angle = position / (10000 ** (2 * (i // 2) / d_model))
        if i % 2 == 0:
            encoding.append(round(math.sin(angle), 4))
        else:
            encoding.append(round(math.cos(angle), 4))
    return encoding


# ---------------------------------------------------------------------------
# The Royal Diamond Theft — reconstructed timeline of events
# ---------------------------------------------------------------------------

crime_timeline = [
    "alarm_silenced",   # pos 0 — 11:58 PM, alarm system bypassed
    "window_forced",    # pos 1 — 12:01 AM, west window breached
    "vault_accessed",   # pos 2 — 12:23 AM, keypad log entry
    "diamond_taken",    # pos 3 — 12:23–12:31 AM, display case broken
    "suspect_fled",     # pos 4 — 12:47 AM, footprints lead to harbour
]

d_model = 8  # kept small so the numbers are readable

print("=" * 62)
print("  CASE FILE 05")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Positional Encoding")
print()
print("  Investigation Status:")
print("  Active — Timeline Reconstruction, Day 1")
print()
print("  Objective:")
print("  Encode the exact sequence of five crime events so the")
print("  transformer knows their order without reading them in sequence.")
print("=" * 62)

print("""
Morgan pins five index cards to the whiteboard in order.

  "The alarm was silenced FIRST. Then the window was forced.
   Then the vault was accessed. Then the diamond disappeared.
   Swap any two of those and the whole story changes."

A transformer processes all five tokens at once — it has no built-in
sense of order. Positional encoding gives it that sense.
""")

print(f"Crime timeline  (embedding size d_model = {d_model}):\n")
print(f"  {'Pos':<4}  {'Event':<20}  Positional Encoding Vector")
print(f"  {'-'*68}")

for pos, event in enumerate(crime_timeline):
    pe = positional_encoding(pos, d_model)
    print(f"  {pos:<4}  {event:<20}  {pe}")

# Show why order changes meaning
print("""
Morgan flips two cards to show the cadets what happens:
""")

sequences = [
    ["vault_accessed", "diamond_taken"],   # correct order
    ["diamond_taken",  "vault_accessed"],  # reversed
]

for seq in sequences:
    arrow = " → ".join(seq)
    print(f"  Sequence: {arrow}")
    for pos, event in enumerate(seq):
        pe = positional_encoding(pos, d_model)
        print(f"    pos={pos}  '{event}'  →  PE={pe[:4]}...")
    print()

print("""  "Same words. Different positions. Completely different meaning.
   The positional encoding is ADDED to the token embedding —
   not concatenated. Each position gets a unique sine/cosine signature
   the model learns to read like a timestamp on a CCTV recording."
""")

print("""
==========================

Investigation Summary

Morgan reconstructs the five-event Royal Diamond Theft timeline on the
whiteboard. Each event receives a unique sine/cosine positional encoding
vector. When two events are swapped, their encoding values change — proving
that position is not free and order is baked into the representation.

AI Connection

Positional encoding adds order information to token embeddings by injecting
sine/cosine signals at geometrically spaced wavelengths. Without it, a
transformer cannot distinguish "suspect fled then shot" from "suspect shot
then fled" — the same tokens, but completely different meanings.

Continue Investigation

The timeline is established. Now Morgan has one burning question — and
every piece of evidence must be scored against it.
Open:
    06_attention.py
""")
