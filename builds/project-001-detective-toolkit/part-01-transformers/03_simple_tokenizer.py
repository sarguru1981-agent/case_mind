# =============================================================================
# THE ROYAL DIAMOND THEFT — Part 1, Chapter 3
#
# The phone rings. A witness has come forward. They were outside the Grand
# Museum the night of the theft and saw something important.
#
# Morgan needs to process their statement immediately — encode it into token
# IDs so it can be analysed alongside the existing case documents, and
# decode the IDs back to verify the original words were preserved.
#
# He needs a proper TOKENIZER: a system that encodes AND decodes, and
# handles words it has never seen before with a special <UNK> token.
# =============================================================================


PAD_TOKEN = "<PAD>"   # pads shorter sequences to equal length
UNK_TOKEN = "<UNK>"   # handles any word not in the vocabulary


class CaseTokenizer:
    """
    Word-level tokenizer: encode text to IDs, decode IDs back to text.

    Special IDs:
      0 → <PAD>   (padding)
      1 → <UNK>   (unknown — word not seen during training)
    """

    def __init__(self):
        self.token_to_id = {PAD_TOKEN: 0, UNK_TOKEN: 1}
        self.id_to_token = {0: PAD_TOKEN, 1: UNK_TOKEN}
        self._next_id    = 2

    def train(self, texts):
        """Build vocabulary from a list of text strings."""
        for text in texts:
            for word in text.lower().split():
                word = word.strip(".,!?;:\"'")
                if word and word not in self.token_to_id:
                    self.token_to_id[word] = self._next_id
                    self.id_to_token[self._next_id] = word
                    self._next_id += 1

    def encode(self, text):
        """Convert a text string into a list of integer token IDs."""
        ids = []
        for word in text.lower().split():
            word = word.strip(".,!?;:\"'")
            ids.append(self.token_to_id.get(word, 1))  # 1 = <UNK>
        return ids

    def decode(self, ids):
        """Convert a list of integer token IDs back into a text string."""
        return " ".join(self.id_to_token.get(i, UNK_TOKEN) for i in ids)

    @property
    def vocab_size(self):
        return len(self.token_to_id)


# ---------------------------------------------------------------------------
# The tokenizer is trained on all known Royal Diamond Theft case documents
# ---------------------------------------------------------------------------

case_files = [
    "lord blackwell entered the grand museum at midnight",
    "the royal diamond was stolen from the vault",
    "a witness saw blackwell near the west window",
    "muddy footprints led from the window to the vault",
    "the detective found a business card near the vault",
]

tokenizer = CaseTokenizer()
tokenizer.train(case_files)

print("=" * 62)
print("  CASE FILE 03")
print()
print("  Case:")
print("  The Royal Diamond Theft")
print()
print("  Article:")
print("  Part 1")
print()
print("  Chapter:")
print("  The Tokenizer")
print()
print("  Investigation Status:")
print("  Active — Witness Statement Received, Day 1")
print()
print("  Objective:")
print("  Encode the witness statement into token IDs and decode")
print("  it back — and handle words outside the known vocabulary.")
print("=" * 62)

print(f"""
The phone rings at Morgan's desk.

  "I was walking past the Grand Museum just after midnight,"
  the witness says. "I saw a man in a dark coat near the
  west entrance. He was carrying a black bag."

Morgan's case tokenizer is already trained on all known
documents. Vocabulary built: {tokenizer.vocab_size} tokens.
It is ready to process anything new.
""")

# Encode the witness statement
witness_statement = "a man in a dark coat near the west entrance past midnight"
encoded = tokenizer.encode(witness_statement)
decoded = tokenizer.decode(encoded)

print("Witness statement:")
print(f'  "{witness_statement}"')
print(f"\n  Encoded  →  {encoded}")
print(f'\n  Decoded  ←  "{decoded}"')

# A new forensic note with unknown words
forensic_note = "the suspect wore leather gloves and carried lockpicks"
encoded_note  = tokenizer.encode(forensic_note)
decoded_note  = tokenizer.decode(encoded_note)

print(f"\nForensic note (contains words not in the case vocabulary):")
print(f'  "{forensic_note}"')
print(f"\n  Encoded  →  {encoded_note}")
print(f'\n  Decoded  ←  "{decoded_note}"')
print(f'  Note: "leather", "gloves", "lockpicks" → ID 1 ({UNK_TOKEN})')

print("""
  "Every word we haven't catalogued becomes an unknown," Morgan says.
  "The model can only work with what it was trained to recognise.
   That's why vocabulary coverage matters."
""")

print("""
==========================

Investigation Summary

A witness phones in with new information — a man in a dark coat near
the west entrance at midnight with a black bag. The case tokenizer
encodes the statement perfectly and decodes it back intact. Three new
forensic words (leather, gloves, lockpicks) fall outside the vocabulary
and collapse to <UNK> — the model cannot represent what it never learned.

AI Connection

A tokenizer is a two-way door: it encodes text to IDs for the model and
decodes IDs back to text for humans. Unknown tokens are a hard constraint.
A real LLM using subword tokenization (BPE) reduces unknowns dramatically
by splitting rare words into smaller known pieces.

Continue Investigation

The vocabulary is established. Morgan now builds mathematical profile
cards for each suspect and measures who fits the crime most closely.
Open:
    04_embeddings.py
""")
