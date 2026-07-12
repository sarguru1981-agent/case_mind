# =============================================================================
# THE POLICE ACADEMY — Part 2, Chapter 5
#
# Graduation requires 60 epochs. Morgan runs the full curriculum:
# every cadet, every case file, every prediction, every weight update.
#
# At the start: random guesses.
# At the end: a model that can complete any case report sentence with
# genuine accuracy — trained on the Royal Diamond Theft vocabulary.
#
# This is THE TRAINING LOOP — forward pass, loss, gradient, update, repeat.
# It is the complete algorithm used to pre-train every large language model.
# =============================================================================

import math
import random


# ── Vocabulary — drawn from the Royal Diamond Theft case ──────────────────

VOCAB = ["the", "suspect", "detective", "witness",
         "fled",  "found",  "evidence",  "diamond"]

word_to_id = {w: i for i, w in enumerate(VOCAB)}
id_to_word = {i: w for i, w in enumerate(VOCAB)}
V          = len(VOCAB)


# ── Training data — (context_word, target_word) pairs from academy files ──

TRAINING_DATA = [
    ("the",       "suspect"),
    ("the",       "detective"),
    ("the",       "witness"),
    ("the",       "evidence"),
    ("the",       "diamond"),
    ("suspect",   "fled"),
    ("suspect",   "found"),
    ("detective", "found"),
    ("detective", "evidence"),
    ("witness",   "fled"),
    ("witness",   "found"),
    ("found",     "evidence"),
    ("found",     "diamond"),
    ("evidence",  "diamond"),
]


# ── The Trainable Language Model ──────────────────────────────────────────

def softmax(logits):
    max_l = max(logits)
    exps  = [math.exp(x - max_l) for x in logits]
    total = sum(exps)
    return [e / total for e in exps]


class AcademyLM:
    """
    Bigram language model. One weight matrix W of shape (V × V).
    W[context_id] stores the logit vector for the next-token distribution.

    Forward pass:  softmax(W[context_id]) → probability distribution
    Backward pass: cross-entropy + softmax gradient → weight update
    """

    def __init__(self, vocab_size, seed=42):
        random.seed(seed)
        self.V = vocab_size
        self.W = [[random.uniform(-0.1, 0.1) for _ in range(vocab_size)]
                  for _ in range(vocab_size)]

    def forward(self, context_id):
        """Return probability distribution over the next token."""
        return softmax(self.W[context_id])

    def train_step(self, context_id, target_id, lr=0.05):
        """
        One forward + backward pass.

        Gradient of cross-entropy + softmax w.r.t. logit j:
          dL/dlogit_j = p_j - 1   if j == target
          dL/dlogit_j = p_j       otherwise
        """
        probs = self.forward(context_id)
        loss  = -math.log(max(probs[target_id], 1e-10))
        for j in range(self.V):
            grad = probs[j] - (1.0 if j == target_id else 0.0)
            self.W[context_id][j] -= lr * grad
        return loss

    def predict(self, context_word, top_k=3):
        """Return top-k (word, probability) predictions."""
        if context_word not in word_to_id:
            return []
        probs  = self.forward(word_to_id[context_word])
        ranked = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        return [(id_to_word[i], round(p, 4)) for i, p in ranked[:top_k]]


# ── The full training loop ─────────────────────────────────────────────────

model      = AcademyLM(V)
NUM_EPOCHS = 60

print("=" * 62)
print("  CASE FILE 14")
print()
print("  Case:")
print("  The Police Academy")
print()
print("  Article:")
print("  Part 2")
print()
print("  Chapter:")
print("  The Training Loop")
print()
print("  Investigation Status:")
print("  Academy — Term 1, Full Curriculum, Graduation Day")
print()
print("  Objective:")
print("  Run the complete training loop for 60 epochs on the Royal")
print("  Diamond Theft vocabulary and graduate a trained language model.")
print("=" * 62)

print(f"""
Morgan stands at the front of the lecture hall.

  "We begin. {NUM_EPOCHS} epochs. Every case file. Every word.
   Every prediction. Every correction.
   Graduation is at the end."

The cadets — like all language models — start with random weights.
""")

# ── Before training ────────────────────────────────────────────────────────
print("── Before training (random weights) ──────────────────────────────")
for ctx in ["the", "detective", "suspect"]:
    preds = model.predict(ctx, top_k=2)
    print(f'  After "{ctx}":  {[(w, p) for w, p in preds]}')

# ── Training ───────────────────────────────────────────────────────────────
print(f"\n── Training ({NUM_EPOCHS} epochs) ──────────────────────────────────────────")
print(f"  {'Epoch':<6}  {'Avg Loss':>10}  Progress")
print(f"  {'-'*42}")

for epoch in range(1, NUM_EPOCHS + 1):
    total_loss  = 0.0
    valid_steps = 0

    for ctx_word, tgt_word in TRAINING_DATA:
        if ctx_word in word_to_id and tgt_word in word_to_id:
            loss        = model.train_step(word_to_id[ctx_word],
                                           word_to_id[tgt_word],
                                           lr=0.05)
            total_loss += loss
            valid_steps += 1

    avg_loss = total_loss / max(valid_steps, 1)

    if epoch % 10 == 0:
        bar = "█" * int((2.0 - min(avg_loss, 2.0)) * 15)
        print(f"  {epoch:<6}  {avg_loss:>10.4f}  {bar}")

# ── After training ─────────────────────────────────────────────────────────
print(f"\n── After {NUM_EPOCHS} epochs — Graduation ──────────────────────────────────")
for ctx in ["the", "detective", "suspect", "found", "witness"]:
    preds = model.predict(ctx, top_k=3)
    print(f'\n  Prompt: "...the report says [{ctx}] ___"')
    for word, prob in preds:
        bar = "█" * int(prob * 30)
        print(f"    → '{word}':{'':<10}  {prob:.4f}  {bar}")

print(f"""
  Morgan closes the academy register.

  "These cadets started with random guesses.
   After {NUM_EPOCHS} epochs of next-token prediction on the Royal Diamond
   Theft vocabulary, they complete case report sentences accurately.
   That's graduation."

  Model summary:
    Vocabulary  : {V} words (Royal Diamond Theft case vocabulary)
    Parameters  : {V * V} weights (a {V}×{V} matrix)
    Epochs      : {NUM_EPOCHS}

  GPT-3 comparison:
    Vocabulary  : ~100,000 tokens
    Parameters  : ~175 billion
    Training    : weeks on thousands of GPUs
    Objective   : the same next-token prediction loop you just ran.
""")

print("""
==========================

Investigation Summary

The full 60-epoch curriculum runs on the Royal Diamond Theft vocabulary.
The model begins with incoherent random predictions and ends completing
case report sentences accurately. Loss falls steadily across epochs. The
cadets who started with random weights graduate as a trained language model.

AI Connection

The training loop — forward pass, loss calculation, gradient descent, weight
update, repeat — is the complete pre-training algorithm for every LLM.
GPT-3 runs this same loop across 175 billion parameters and 300 billion
tokens. Scale is the only difference between this file and that model.

Continue Investigation

The Royal Diamond Theft is solved. The Police Academy has graduated its
first class. You have completed Build 1 — The First Detective Toolkit.

Return to the articles:
    Part 1 — The Robbery That Taught Me Transformers
    Part 2 — The Police Academy That Built an LLM
""")
