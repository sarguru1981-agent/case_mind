# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 1
#
# It is 6 AM. Detective Morgan arrives at headquarters to find a sealed
# envelope on his desk marked URGENT. He tears it open.
#
# The Royal Diamond — the Grand Museum's most prized exhibit, insured for
# twelve million pounds — has been stolen overnight.
#
# Before Morgan can analyse a single pattern in the report, he must do what
# every transformer does first: break the text into tokens — the smallest
# meaningful units that can be processed one at a time.
# =============================================================================


def tokenize(text):
    """Split text into word-level tokens, stripping punctuation."""
    # Real LLMs use subword algorithms (BPE, WordPiece) — the idea is the same.
    words  = text.lower().split()
    tokens = [w.strip(".,!?;:\"'()") for w in words]
    return [t for t in tokens if t]


# ---------------------------------------------------------------------------
# The crime report
# ---------------------------------------------------------------------------

crime_report = (
    "Lord Blackwell entered the Grand Museum at midnight "
    "and stole the Royal Diamond from the vault."
)

print("=" * 62)
print("  CASE FILE 01")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Tokenization")
print()
print("  Investigation Status:")
print("  Active — Grand Museum, Day 1, 06:00 AM")
print()
print("  Objective:")
print("  Break the incoming crime report into individual tokens")
print("  before any analysis can begin.")
print("=" * 62)

print(f"""
Detective Morgan tears open the envelope and reads the report.

  [URGENT — CRIME REPORT — GRAND MUSEUM]
  "{crime_report}"

He reads it once. Then he does what he always does first:
picks up a red pen and marks every individual word.

"Before I can find any patterns," he says,
"I need to see the pieces. One clue at a time."
""")

tokens = tokenize(crime_report)

print("Evidence Log — Individual Clues (Tokens):")
print(f"  {'ID':<6}  Clue")
print(f"  {'-'*22}")
for i, token in enumerate(tokens):
    print(f"  [{i:02d}]    '{token}'")

print(f"\nTotal clues extracted: {len(tokens)}")
print("\nThe report is now a sequence of tokens.")
print("Morgan is ready for the next step: assigning them to the evidence registry.")

print("""
==========================

Investigation Summary

Detective Morgan receives an urgent crime report — the Royal Diamond has
been stolen from the Grand Museum vault overnight. Before any analysis
can begin, he breaks the 16-word report into individual tokens using the
same first step every transformer applies to any input text.

AI Connection

Tokenization converts raw text into the atomic units a transformer processes.
Without this step, the model cannot read a single word. Every LLM tokenises
its entire input — from a single sentence to a 100,000-token document —
before any mathematical computation occurs.

Continue Investigation

The tokens need permanent case numbers before they can be catalogued.
Open:
    02_token_ids.py
""")
