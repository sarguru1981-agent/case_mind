# =============================================================================
# THE POLICE ACADEMY — Part 2, Chapter 3
#
# Morgan marks the first exam papers. His grading rule is strict:
#
#   A cadet who is uncertain and spreads their answer → fair mark.
#   A cadet who says "definitely X" and is right → best mark.
#   A cadet who says "definitely X" and is wrong → worst mark.
#
# This is CROSS-ENTROPY LOSS. It measures exactly how wrong a prediction is.
# Confident wrong answers are punished far more than uncertain ones.
# This asymmetry is what drives the model toward accuracy during training.
# =============================================================================

import math


def cross_entropy_loss(predicted_probs, correct_index):
    """
    Cross-entropy = -log( probability assigned to the correct answer ).

    Perfect confidence in the right answer  → loss = 0.0
    Confident wrong answer                  → loss approaches infinity
    """
    p_correct = max(predicted_probs[correct_index], 1e-10)  # avoid log(0)
    return -math.log(p_correct)


def grade(scenario, vocab, predicted_probs, correct_word):
    """Print Morgan's grading card for one cadet prediction."""
    correct_index = vocab.index(correct_word)
    loss          = cross_entropy_loss(predicted_probs, correct_index)
    p_correct     = predicted_probs[correct_index]

    print(f"\n  ── {scenario} ──")
    print(f"  {'Word':<14}  {'Prob':>6}  Distribution")
    print(f"  {'-'*46}")
    for word, prob in zip(vocab, predicted_probs):
        bar    = "█" * int(prob * 30)
        marker = "  ← correct" if word == correct_word else ""
        print(f"  {word:<14}  {prob:>6.3f}  {bar}{marker}")
    grade_label = ("★ excellent (low loss)"  if loss < 0.5  else
                   "△ acceptable"             if loss < 1.5  else
                   "✗ penalised (high loss)")
    print(f"\n  Loss = -log({p_correct:.3f}) = {loss:.4f}   {grade_label}")


# ---------------------------------------------------------------------------
# The vocabulary — words the cadet must choose from
# ---------------------------------------------------------------------------

vocab = ["suspect", "detective", "witness", "building", "fled"]

print("=" * 62)
print("  CASE FILE 12")
print()
print("  Case:")
print("  The Police Academy")
print()
print("  Article:")
print("  Part 2")
print()
print("  Chapter:")
print("  The Loss Function")
print()
print("  Investigation Status:")
print("  Academy — Term 1, Grading")
print()
print("  Objective:")
print("  Grade three cadets on the same prediction and show how")
print("  cross-entropy loss penalises confident wrong answers.")
print("=" * 62)

print("""
Morgan picks up the red pen.

  Exam question:
  "The ______ arrived at the crime scene first."
  Correct answer: "detective"

Three cadets answer. Morgan grades them all.
""")

grade(
    'Cadet A — confident and CORRECT   ("definitely detective")',
    vocab,
    [0.04, 0.87, 0.04, 0.03, 0.02],
    "detective",
)

grade(
    'Cadet B — uncertain               ("could be any of them")',
    vocab,
    [0.20, 0.22, 0.20, 0.19, 0.19],
    "detective",
)

grade(
    'Cadet C — confident and WRONG     ("definitely witness")',
    vocab,
    [0.04, 0.03, 0.87, 0.04, 0.02],
    "detective",
)

print("""
  Morgan puts down the pen.

  "Cadet C scores worst. Not for being wrong — being wrong
   is expected at the start. But for being CONFIDENT while wrong.
   The loss function punishes that exponentially.

   This grading signal travels back through every weight in the model.
   That process is called backpropagation.
   The model adjusts every weight in the direction that reduces this loss."
""")

print("""
==========================

Investigation Summary

Morgan grades three cadets on the same prediction question. Cadet A is
confident and correct — near-zero loss. Cadet B is uncertain — medium loss.
Cadet C is confident and completely wrong — the highest loss in the room.
The grading asymmetry teaches cadets to be right before being bold.

AI Connection

Cross-entropy loss penalises confident wrong answers exponentially. It is
the training signal that backpropagation uses to update every weight in the
network. Minimising it across billions of training examples is how a neural
network learns to be both accurate and well-calibrated.

Continue Investigation

One cadet keeps predicting wrong. Morgan will work with them one-on-one
using the gradient to show exactly which direction to improve.
Continue to:
    04_gradient_descent.py
""")
