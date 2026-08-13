# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 2
#
# Morgan carries his list of tokens down the hall to Sergeant Harris,
# who runs the evidence registry. Her rule has never changed in 20 years:
# every unique clue gets a permanent number. Same clue, same number. Always.
#
# In AI, this is called building a VOCABULARY and encoding tokens as IDs.
# Computers work with numbers, not words — token IDs are the bridge.
# =============================================================================


def build_vocabulary(texts):
    """Build a word → integer ID mapping from a list of text strings."""
    vocab   = {}
    next_id = 0
    for text in texts:
        for word in text.lower().split():
            word = word.strip(".,!?;:")
            if word not in vocab:
                vocab[word] = next_id
                next_id += 1
    return vocab


def encode(text, vocab):
    """Convert a sentence into a list of token IDs."""
    return [vocab.get(w.strip(".,!?;:").lower(), -1)
            for w in text.split()]


# ---------------------------------------------------------------------------
# Sergeant Harris builds the registry from all available case documents
# ---------------------------------------------------------------------------

case_documents = [
    "lord blackwell entered the grand museum at midnight",
    "the royal diamond was stolen from the vault",
    "a witness saw blackwell near the west window",
    "muddy footprints led from the window to the vault",
    "the detective found a dropped business card near the vault",
]

print("=" * 62)
print("  CASE FILE 02")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  Token IDs")
print()
print("  Investigation Status:")
print("  Active — Evidence Room Registry, Day 1")
print()
print("  Objective:")
print("  Assign a permanent integer ID to every unique token")
print("  across all Royal Diamond Theft case documents.")
print("=" * 62)

print("""
Morgan walks the token list to Sergeant Harris's desk.

  "Give each unique clue a permanent number," he says.
  "Same word, same number. Every document in this case."

Sergeant Harris opens the registry and starts assigning.
Every new word gets the next available ID. Existing words
keep their original ID — the registry never changes.
""")

vocab = build_vocabulary(case_documents)

print(f"Evidence Registry — {len(vocab)} unique tokens registered:\n")
print(f"  {'Token':<22}  {'ID':>3}")
print(f"  {'-'*27}")
for word, tid in vocab.items():
    print(f"  {word:<22}  {tid:>3}")

# Encode the original crime report
report = "lord blackwell entered the grand museum at midnight"
ids    = encode(report, vocab)

print(f'\nMorgan presents the original crime report:')
print(f'  "{report}"')
print(f'\n  Tokens  : {report.split()}')
print(f'  IDs     : {ids}')

print("""
  "The transformer never sees words," Sergeant Harris says,
  closing the registry. "It only sees these numbers.
  Every word in this case is now a permanent entry."
""")

print("""
==========================

Investigation Summary

Sergeant Harris registers every unique word from all Royal Diamond Theft
case documents, assigning each a permanent integer ID. The original crime
report — eight words spoken at the scene — is fully encoded as a sequence
of integers. This is the form the transformer actually reads internally.

AI Connection

Transformers work with numbers, not words. Token IDs are the bridge.
A model's vocabulary is a fixed mapping built once during training and
frozen forever — words not seen during training have no representation
and must be handled as unknowns in the tokenizer.

Continue Investigation

A witness has called in with new information that must be processed
immediately. The case tokenizer must handle both known and unknown words.
Open:
    03_simple_tokenizer.py
""")
